# Biomedical Machine-Learning Reproducibility

[![CI](https://github.com/biomir/biomedical-ml-reproducibility/actions/workflows/ci.yml/badge.svg)](https://github.com/biomir/biomedical-ml-reproducibility/actions/workflows/ci.yml)

**Executable provenance and leakage controls for inspectable biomedical machine-learning experiments.**

In biomedical modeling, a repeatable score is not persuasive if the evaluation leaks patient identity, ignores temporal ordering, hides preprocessing, or cannot identify the exact dataset and code that produced it. This repository demonstrates controls for those failure modes using synthetic, patient-grouped data.

## Evidence encoded in the implementation

| Risk | Reference control | What remains outside scope |
| --- | --- | --- |
| Dataset ambiguity | SHA-256 fingerprints for the exact input file. | Provenance rights, cohort validity, labeling accuracy, and representativeness. |
| Configuration drift | Canonically serialized configuration fingerprints. | Prospective study governance and change-control approval. |
| Source or environment drift | Source-file hashes, Python/platform details, package versions, and observed interpreter hash-seed configuration. | Container equivalence, hardware nondeterminism, and distributed-system reproducibility. |
| Patient-level leakage | Explicit group-overlap audits plus grouped cross-validation in the executable example. | Hidden source-system linkage or identity collisions not present in supplied group identifiers. |
| Temporal leakage | Timezone-aware chronological split audits with strict train-before-test ordering. | Outcome availability, label-latency, censoring, and deployment-specific decision timing. |
| Preprocessing leakage | Scaling is fit inside the cross-validation pipeline rather than on the full dataset. | Every other feature-generation or selection step must also obey the same boundary. |

## Inspect the evidence

- [`src/biomed_repro/audit.py`](src/biomed_repro/audit.py): manifests, source/data/config fingerprints, dependency capture, seed validation, and split audits.
- [`tests/test_audit.py`](tests/test_audit.py): stable hashing, group overlap, timezone-aware chronology, manifest integrity, and interpreter-seeding limitations.
- [`examples/sklearn_demo.py`](examples/sklearn_demo.py): synthetic repeated observations, grouped cross-validation, leakage-safe preprocessing, and a recorded experiment manifest.
- [`docs/REPRODUCIBILITY_CHECKLIST.md`](docs/REPRODUCIBILITY_CHECKLIST.md): a reviewer-oriented checklist distinguishing reproducibility, scientific validity, and intended-use evidence.

## Run the reference

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,ml]"
pytest -q
PYTHONHASHSEED=42 python examples/sklearn_demo.py
```

```python
from biomed_repro import audit_group_split, audit_temporal_split

groups = audit_group_split(["patient-01", "patient-02"], ["patient-03"])
chronology = audit_temporal_split(
    ["2025-01-02T09:00:00+00:00"],
    ["2025-02-02T09:00:00+00:00"],
)

assert groups.passed and chronology.passed
```

### A precise note on determinism

`PYTHONHASHSEED` must be set **before the interpreter starts**. Changing that environment variable inside a running Python process does not retroactively change the interpreter's hash behavior. The reference records the observed setting and never misrepresents an in-process assignment as proof of deterministic execution.

## Reproducibility is not clinical validity

Reproducing a result does not establish calibration, fairness, external validity, causal interpretation, clinical utility, safety, or regulatory authorization. FDA's [Good Machine Learning Practice for Medical Device Development](https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles) is relevant context for thinking about lifecycle quality; this repository does not claim implementation of a regulated quality system or conformance assessment.

All data are synthetic. No patient-level records, proprietary BioMIR models, unpublished employer work, or product algorithms are included.

## Related portfolio evidence

- [Analytical method validation and calculation verification](https://github.com/biomir/analytical-method-validation-python)
- [Clinical laboratory QC and run-aware decision evidence](https://github.com/biomir/clinical-lab-qc-python)
- [SaMD requirements, risk controls, and release gates](https://github.com/biomir/samd-engineering-reference)
- [Yonathan Emmanuel's scientific and engineering portfolio](https://github.com/biomir)

**Author:** Yonathan Emmanuel · **License:** MIT
