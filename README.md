# Biomedical ML Reproducibility Reference

A compact reference for the engineering practices that make biomedical machine
learning experiments inspectable and reproducible.

The project focuses on provenance and experimental determinism rather than on a
novel predictive model.

## Demonstrated controls

- deterministic random-seed setup
- canonical dataset/file hashing
- environment capture
- structured experiment manifests
- separation of training and evaluation configuration
- repeatable scikit-learn example pipeline
- unit tests and CI

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test,ml]"
pytest -q
python examples/sklearn_demo.py
```

The example generates a synthetic classification dataset, performs stratified
cross-validation with a fixed seed, uses preprocessing inside the model
pipeline to avoid leakage, and records a compact experiment manifest.

## Reproducibility is not validity

Reproducing the same result does not establish:

- clinical validity
- generalizability
- fairness
- absence of leakage
- causal interpretation
- adequate external validation
- fitness for a medical purpose

Those require additional evidence and domain-specific study design.

## Public/non-proprietary boundary

All demonstrations use synthetic data. No patient-level data, confidential
employer data, BioMIR proprietary algorithms, or unpublished product models are
included.

## Author

Yonathan Emmanuel — biomedical scientist and computational health technology
developer.

## License

MIT.
