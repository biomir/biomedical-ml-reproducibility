"""Reproducible synthetic classification example.

Requires: pip install -e ".[ml]"
"""

from pathlib import Path
import csv
import json
import tempfile

import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from biomed_repro.audit import manifest, seed_everything

SEED = 42
CONFIG = {
    "model": "logistic_regression",
    "n_splits": 5,
    "scoring": "balanced_accuracy",
    "synthetic_only": True,
}

seed_everything(SEED)
X, y = make_classification(
    n_samples=500,
    n_features=12,
    n_informative=6,
    n_redundant=2,
    weights=[0.65, 0.35],
    random_state=SEED,
)

pipeline = Pipeline([
    ("scale", StandardScaler()),
    ("model", LogisticRegression(max_iter=2000, random_state=SEED)),
])

cv = StratifiedKFold(n_splits=CONFIG["n_splits"], shuffle=True, random_state=SEED)
scores = []
for train_idx, test_idx in cv.split(X, y):
    pipeline.fit(X[train_idx], y[train_idx])
    pred = pipeline.predict(X[test_idx])
    scores.append(balanced_accuracy_score(y[test_idx], pred))

with tempfile.TemporaryDirectory() as d:
    dataset = Path(d) / "synthetic.csv"
    with dataset.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([f"x{i}" for i in range(X.shape[1])] + ["target"])
        for row, target in zip(X, y):
            writer.writerow([*row, int(target)])

    record = manifest("synthetic-logistic-regression", SEED, dataset, CONFIG)

print("Fold scores:", [round(s, 4) for s in scores])
print("Mean balanced accuracy:", round(float(np.mean(scores)), 4))
print("Manifest:")
print(record.to_json())
