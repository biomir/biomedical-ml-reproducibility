"""Provenance and split-integrity controls for synthetic biomedical experiments."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import random
import sys
from typing import Any, Sequence


@dataclass(frozen=True)
class GroupSplitAudit:
    training_group_count: int
    evaluation_group_count: int
    overlapping_group_count: int
    passed: bool


@dataclass(frozen=True)
class TemporalSplitAudit:
    latest_training_timestamp: str
    earliest_evaluation_timestamp: str
    passed: bool


@dataclass(frozen=True)
class ExperimentManifest:
    name: str
    seed: int
    dataset_sha256: str
    config_sha256: str
    source_sha256: str | None
    python: str
    platform: str
    python_hash_seed: str | None
    dependency_versions: dict[str, str]
    group_split_audits: tuple[GroupSplitAudit, ...]
    temporal_split_audit: TemporalSplitAudit | None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True, allow_nan=False)


def _validated_seed(seed: int) -> int:
    normalized = int(seed)
    if not 0 <= normalized < 2**32:
        raise ValueError("seed must be an integer in the range [0, 2**32)")
    return normalized


def seed_everything(seed: int) -> int:
    """Seed available RNGs without misrepresenting interpreter hash behavior.

    Python hash randomization is fixed at interpreter startup. Set
    ``PYTHONHASHSEED`` in the parent environment before running Python.
    """
    normalized = _validated_seed(seed)
    random.seed(normalized)
    try:
        import numpy as np

        np.random.seed(normalized)
    except ImportError:
        pass
    return normalized


def file_sha256(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def dependency_versions(package_names: Sequence[str]) -> dict[str, str]:
    """Capture installed package versions without importing model frameworks."""
    versions: dict[str, str] = {}
    for package_name in sorted({str(name).strip() for name in package_names}):
        if not package_name:
            raise ValueError("dependency names must not be empty")
        try:
            versions[package_name] = version(package_name)
        except PackageNotFoundError:
            versions[package_name] = "not-installed"
    return versions


def runtime_environment(package_names: Sequence[str] = ()) -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "dependency_versions": dependency_versions(package_names),
    }


def _group_ids(values: Sequence[str], partition: str) -> set[str]:
    if not values:
        raise ValueError(f"{partition} group identifiers must not be empty")
    groups: set[str] = set()
    for value in values:
        if value is None or not str(value).strip():
            raise ValueError(f"{partition} contains a missing group identifier")
        groups.add(str(value).strip())
    return groups


def audit_group_split(
    training_groups: Sequence[str], evaluation_groups: Sequence[str]
) -> GroupSplitAudit:
    """Report group leakage using counts only; never return patient identifiers."""
    training = _group_ids(training_groups, "training")
    evaluation = _group_ids(evaluation_groups, "evaluation")
    overlap_count = len(training & evaluation)
    return GroupSplitAudit(
        training_group_count=len(training),
        evaluation_group_count=len(evaluation),
        overlapping_group_count=overlap_count,
        passed=overlap_count == 0,
    )


def _aware_timestamp(value: str | datetime, partition: str) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    else:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{partition} timestamps must be timezone-aware")
    return timestamp.astimezone(timezone.utc)


def audit_temporal_split(
    training_timestamps: Sequence[str | datetime],
    evaluation_timestamps: Sequence[str | datetime],
) -> TemporalSplitAudit:
    """Require the latest training observation to precede evaluation strictly."""
    if not training_timestamps or not evaluation_timestamps:
        raise ValueError("training and evaluation timestamps must not be empty")
    training = [_aware_timestamp(value, "training") for value in training_timestamps]
    evaluation = [
        _aware_timestamp(value, "evaluation") for value in evaluation_timestamps
    ]
    latest_training = max(training)
    earliest_evaluation = min(evaluation)
    return TemporalSplitAudit(
        latest_training_timestamp=latest_training.isoformat(),
        earliest_evaluation_timestamp=earliest_evaluation.isoformat(),
        passed=latest_training < earliest_evaluation,
    )


def manifest(
    name: str,
    seed: int,
    dataset_path: str | Path,
    config: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    package_names: Sequence[str] = (),
    group_audits: Sequence[GroupSplitAudit] = (),
    temporal_audit: TemporalSplitAudit | None = None,
) -> ExperimentManifest:
    experiment_name = str(name).strip()
    if not experiment_name:
        raise ValueError("experiment name must not be empty")
    if any(not audit.passed for audit in group_audits):
        raise ValueError("cannot record an accepted experiment with group leakage")
    if temporal_audit is not None and not temporal_audit.passed:
        raise ValueError("cannot record an accepted experiment with temporal leakage")

    environment = runtime_environment(package_names)
    return ExperimentManifest(
        name=experiment_name,
        seed=_validated_seed(seed),
        dataset_sha256=file_sha256(dataset_path),
        config_sha256=stable_json_sha256(config),
        source_sha256=file_sha256(source_path) if source_path is not None else None,
        python=environment["python"],
        platform=environment["platform"],
        python_hash_seed=environment["python_hash_seed"],
        dependency_versions=environment["dependency_versions"],
        group_split_audits=tuple(group_audits),
        temporal_split_audit=temporal_audit,
    )
