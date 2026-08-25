# Biomedical ML reproducibility checklist

## Data provenance

- [ ] Dataset source and eligibility criteria documented
- [ ] Dataset version/fingerprint recorded
- [ ] Unit of analysis defined
- [ ] Label-generation process documented
- [ ] Missing-data handling specified
- [ ] Duplicate and leakage checks performed

## Experimental design

- [ ] Train/validation/test separation defined before modeling
- [ ] Grouping and temporal structure respected
- [ ] Random seeds recorded
- [ ] Hyperparameter search space recorded
- [ ] Preprocessing fit only on training data
- [ ] Primary metric specified prospectively

## Environment

- [ ] Python/runtime version recorded
- [ ] Dependency versions locked or captured
- [ ] Hardware-relevant nondeterminism documented
- [ ] Source commit SHA recorded

## Reporting

- [ ] Confidence intervals or resampling uncertainty reported where appropriate
- [ ] Subgroup performance examined where scientifically justified
- [ ] Calibration evaluated when probabilities are interpreted
- [ ] External validation distinguished from internal validation
- [ ] Limitations and intended-use boundaries stated

## Medical context

Reproducibility is a necessary engineering property, not sufficient evidence for
clinical validity, utility, safety, or regulatory acceptability.
