"""Minimal provenance utilities for reproducible computational experiments."""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import random
import sys
from typing import Any


@dataclass(frozen=True)
class ExperimentManifest:
    name: str
    seed: int
    dataset_sha256: str
    config_sha256: str
    python: str
    platform: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def seed_everything(seed: int) -> int:
    seed = int(seed)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    return seed


def file_sha256(path: str | Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def runtime_environment() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }


def manifest(
    name: str,
    seed: int,
    dataset_path: str | Path,
    config: dict[str, Any],
) -> ExperimentManifest:
    env = runtime_environment()
    return ExperimentManifest(
        name=str(name),
        seed=int(seed),
        dataset_sha256=file_sha256(dataset_path),
        config_sha256=stable_json_sha256(config),
        python=env["python"],
        platform=env["platform"],
    )
