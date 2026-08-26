"""Reproducible grouped cross-validation using exclusively synthetic patients."""

import csv
from pathlib import Path
import tempfile

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from biomed_repro import audit_group_split, manifest, seed_everything


SEED = seed_everything(42)
PATIENT_COUNT = 120
VISITS_PER_PATIENT = 3
CONFIG = {
    "group_unit": "synthetic_patient",
    "model": "logistic_regression",
    "n_splits": 5,
    "preprocessing": "standard_scaler_fit_within_each_training_fold",
    "scoring": "balanced_accuracy",
    "synthetic_only": True,
}

rng = np.random.default_rng(SEED)
patient_features = rng.normal(size=(PATIENT_COUNT, 8))
patient_signal = patient_features[:, 0] - 0.5 * patient_features[:, 1]
patient_labels = (patient_signal > np.quantile(patient_signal, 0.60)).astype(int)

groups = np.repeat(
    [f"synthetic-patient-{index:03d}" for index in range(PATIENT_COUNT)],
    VISITS_PER_PATIENT,
)
features = np.repeat(patient_features, VISITS_PER_PATIENT, axis=0)
features = features + rng.normal(scale=0.15, size=features.shape)
labels = np.repeat(patient_labels, VISITS_PER_PATIENT)

pipeline = Pipeline(
    [
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=2000, random_state=SEED)),
    ]
)
splitter = StratifiedGroupKFold(
    n_splits=CONFIG["n_splits"], shuffle=True, random_state=SEED
)

scores = []
audits = []
for train_indices, test_indices in splitter.split(features, labels, groups):
    split_audit = audit_group_split(
        groups[train_indices].tolist(), groups[test_indices].tolist()
    )
    if not split_audit.passed:
        raise RuntimeError("patient-group leakage detected")
    audits.append(split_audit)

    pipeline.fit(features[train_indices], labels[train_indices])
    predictions = pipeline.predict(features[test_indices])
    scores.append(balanced_accuracy_score(labels[test_indices], predictions))

with tempfile.TemporaryDirectory() as temporary_directory:
    dataset = Path(temporary_directory) / "synthetic_grouped_data.csv"
    with dataset.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["synthetic_patient"]
            + [f"feature_{index}" for index in range(features.shape[1])]
            + ["target"]
        )
        for group, row, target in zip(groups, features, labels):
            writer.writerow([group, *row, int(target)])

    record = manifest(
        "synthetic-grouped-logistic-regression",
        SEED,
        dataset,
        CONFIG,
        source_path=Path(__file__),
        package_names=["numpy", "scikit-learn"],
        group_audits=audits,
    )

print("Grouped fold scores:", [round(score, 4) for score in scores])
print("Mean balanced accuracy:", round(float(np.mean(scores)), 4))
print("Patient overlap per fold:", [audit.overlapping_group_count for audit in audits])
print("Experiment manifest:")
print(record.to_json())
