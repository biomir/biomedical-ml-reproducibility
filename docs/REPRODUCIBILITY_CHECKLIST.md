# Biomedical machine-learning reproducibility and evaluation checklist

## 1. Data provenance and cohort definition

- [ ] Record the dataset owner/source, permitted use, cohort eligibility, and observation period.
- [ ] Fingerprint the exact input file and preserve an auditable dataset version.
- [ ] Define the unit of analysis: patient, specimen, encounter, image, device, or observation.
- [ ] Document label generation, adjudication, outcome timing, and label availability.
- [ ] Characterize duplicate records, missingness, measurement units, site/device effects, and population coverage.
- [ ] Keep patient identifiers and unnecessary row-level detail out of experiment manifests.

## 2. Experimental separation and leakage controls

- [ ] Define train, validation, test, and external-validation populations before fitting.
- [ ] Preserve patient-group isolation where a person contributes repeated observations.
- [ ] Audit the intersection of training and evaluation groups for every fold.
- [ ] Use timezone-aware event times and require training information to precede evaluation.
- [ ] Account separately for label latency, censoring, follow-up, and real deployment timing.
- [ ] Fit scaling, imputation, feature selection, and model selection only inside training partitions.
- [ ] Examine proxy leakage, site leakage, duplicated acquisition artifacts, and outcome-derived features.

## 3. Reconstructable execution

- [ ] Record a validated random seed and the exact model configuration.
- [ ] Fingerprint source code or the source-control revision used for the run.
- [ ] Record Python, platform, and relevant dependency versions.
- [ ] Set `PYTHONHASHSEED` before starting the interpreter; never imply an in-process assignment changes interpreter hashing.
- [ ] Document hardware, parallel execution, accelerator, and framework nondeterminism where relevant.
- [ ] Preserve enough run metadata to reconstruct preprocessing, split generation, and scoring.

## 4. Scientific and clinical interpretation

- [ ] Specify the primary outcome, target population, intended use, and primary metric prospectively.
- [ ] Report uncertainty, subgroup performance, class imbalance, and calibration where scientifically appropriate.
- [ ] Distinguish internal cross-validation from temporal, geographic, site, and external validation.
- [ ] Evaluate dataset shift and the practical effects of missing or stale inputs.
- [ ] Avoid interpreting predictive association as causation or clinical utility.
- [ ] Separate reproducibility evidence from clinical validation, human-factors evaluation, and regulatory authorization.

## 5. Repository evidence

The executable reference demonstrates dataset/config/source fingerprinting, environment capture, grouped patient isolation, timezone-aware split audits, leakage-safe preprocessing, and synthetic grouped cross-validation. It does not claim a validated medical device, representative patient cohort, production monitoring system, or certified quality-management process.
