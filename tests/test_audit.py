from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random

import pytest

from biomed_repro.audit import (
    audit_group_split,
    audit_temporal_split,
    dependency_versions,
    file_sha256,
    manifest,
    runtime_environment,
    seed_everything,
    stable_json_sha256,
)


def test_json_hash_is_order_independent():
    first = stable_json_sha256({"alpha": 1, "beta": [2, 3]})
    second = stable_json_sha256({"beta": [2, 3], "alpha": 1})
    assert first == second


def test_json_hash_changes_with_configuration():
    assert stable_json_sha256({"seed": 1}) != stable_json_sha256({"seed": 2})


def test_json_hash_rejects_nonstandard_nan_values():
    with pytest.raises(ValueError):
        stable_json_sha256({"measurement": float("nan")})


def test_file_hash_changes_when_data_changes(tmp_path: Path):
    dataset = tmp_path / "data.csv"
    dataset.write_text("x,y\n1,2\n", encoding="utf-8")
    original = file_sha256(dataset)
    assert file_sha256(dataset) == original
    dataset.write_text("x,y\n1,3\n", encoding="utf-8")
    assert file_sha256(dataset) != original


def test_seed_function_normalizes_and_reproduces_rng_state():
    assert seed_everything("42") == 42
    first = random.random()
    seed_everything(42)
    assert random.random() == first


def test_seed_function_rejects_unsupported_numpy_seed_range():
    with pytest.raises(ValueError, match="range"):
        seed_everything(-1)
    with pytest.raises(ValueError, match="range"):
        seed_everything(2**32)


def test_seeding_does_not_falsely_reconfigure_interpreter_hash_seed():
    previous = os.environ.get("PYTHONHASHSEED")
    seed_everything(37)
    assert os.environ.get("PYTHONHASHSEED") == previous


def test_dependency_versions_are_sorted_and_explicit_about_missing_packages():
    versions = dependency_versions(["definitely-not-an-installed-biomir-package"])
    assert versions == {"definitely-not-an-installed-biomir-package": "not-installed"}


def test_runtime_environment_records_observed_hash_configuration():
    environment = runtime_environment()
    assert environment["python_hash_seed"] == os.environ.get("PYTHONHASHSEED")
    assert "python" in environment
    assert "platform" in environment


def test_group_audit_accepts_isolated_patient_groups():
    audit = audit_group_split(["patient-01", "patient-01"], ["patient-02"])
    assert audit.training_group_count == 1
    assert audit.evaluation_group_count == 1
    assert audit.overlapping_group_count == 0
    assert audit.passed


def test_group_audit_detects_repeated_patient_leakage():
    audit = audit_group_split(["patient-01", "patient-02"], ["patient-02"])
    assert audit.overlapping_group_count == 1
    assert not audit.passed


def test_group_audit_rejects_empty_or_missing_identifiers():
    with pytest.raises(ValueError, match="must not be empty"):
        audit_group_split([], ["patient-02"])
    with pytest.raises(ValueError, match="missing group identifier"):
        audit_group_split([" "], ["patient-02"])


def test_temporal_audit_accepts_strictly_chronological_partitions():
    audit = audit_temporal_split(
        ["2025-01-01T08:00:00-05:00"], ["2025-01-02T00:00:00+00:00"]
    )
    assert audit.passed
    assert audit.latest_training_timestamp == "2025-01-01T13:00:00+00:00"


def test_temporal_audit_detects_future_information_leakage():
    audit = audit_temporal_split(
        ["2025-02-01T00:00:00+00:00"], ["2025-01-01T00:00:00+00:00"]
    )
    assert not audit.passed


def test_temporal_audit_rejects_equal_partition_boundary():
    value = "2025-01-01T00:00:00+00:00"
    assert not audit_temporal_split([value], [value]).passed


def test_temporal_audit_accepts_timezone_aware_datetime_objects():
    audit = audit_temporal_split(
        [datetime(2025, 1, 1, tzinfo=timezone.utc)],
        [datetime(2025, 1, 2, tzinfo=timezone.utc)],
    )
    assert audit.passed


def test_temporal_audit_rejects_naive_timestamps():
    with pytest.raises(ValueError, match="timezone-aware"):
        audit_temporal_split(["2025-01-01T00:00:00"], ["2025-01-02T00:00:00Z"])


def test_temporal_audit_rejects_empty_partitions():
    with pytest.raises(ValueError, match="must not be empty"):
        audit_temporal_split([], ["2025-01-02T00:00:00Z"])


def test_manifest_records_source_environment_and_leakage_evidence(tmp_path: Path):
    dataset = tmp_path / "data.csv"
    source = tmp_path / "experiment.py"
    dataset.write_text("x,y\n1,0\n", encoding="utf-8")
    source.write_text("print('synthetic')\n", encoding="utf-8")
    group_audit = audit_group_split(["patient-01"], ["patient-02"])
    temporal_audit = audit_temporal_split(
        ["2025-01-01T00:00:00Z"], ["2025-01-02T00:00:00Z"]
    )

    result = manifest(
        "synthetic-evaluation",
        42,
        dataset,
        {"model": "logistic_regression"},
        source_path=source,
        group_audits=[group_audit],
        temporal_audit=temporal_audit,
    )
    record = json.loads(result.to_json())
    assert record["source_sha256"] == file_sha256(source)
    assert record["dataset_sha256"] == file_sha256(dataset)
    assert record["group_split_audits"][0]["passed"]
    assert record["temporal_split_audit"]["passed"]


def test_manifest_never_persists_raw_patient_group_identifiers(tmp_path: Path):
    dataset = tmp_path / "data.csv"
    dataset.write_text("x\n1\n", encoding="utf-8")
    audit = audit_group_split(["PRIVATE-PATIENT-001"], ["PRIVATE-PATIENT-002"])
    record = manifest("safe", 42, dataset, {}, group_audits=[audit]).to_json()
    assert "PRIVATE-PATIENT" not in record


def test_manifest_refuses_group_leakage(tmp_path: Path):
    dataset = tmp_path / "data.csv"
    dataset.write_text("x\n1\n", encoding="utf-8")
    failed = audit_group_split(["patient-01"], ["patient-01"])
    with pytest.raises(ValueError, match="group leakage"):
        manifest("unsafe", 42, dataset, {}, group_audits=[failed])


def test_manifest_refuses_temporal_leakage(tmp_path: Path):
    dataset = tmp_path / "data.csv"
    dataset.write_text("x\n1\n", encoding="utf-8")
    failed = audit_temporal_split(
        ["2025-02-01T00:00:00Z"], ["2025-01-01T00:00:00Z"]
    )
    with pytest.raises(ValueError, match="temporal leakage"):
        manifest("unsafe", 42, dataset, {}, temporal_audit=failed)


def test_manifest_rejects_missing_experiment_name(tmp_path: Path):
    dataset = tmp_path / "data.csv"
    dataset.write_text("x\n1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must not be empty"):
        manifest(" ", 42, dataset, {})
