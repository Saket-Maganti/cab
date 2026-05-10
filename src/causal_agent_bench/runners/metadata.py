from __future__ import annotations

import platform
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench import __version__
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.utils.io import git_commit, write_json


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def safe_run_name(run_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", run_name).strip("_")
    return cleaned or "run"


def prepare_run_directory(config: ExperimentConfig, resume_dir: str | Path | None = None) -> Path:
    if resume_dir is not None:
        run_dir = Path(resume_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    base = config.resolved_output_dir()
    stem = f"{utc_timestamp()}_{safe_run_name(config.run_name)}"
    run_dir = base / stem
    counter = 1
    while run_dir.exists():
        counter += 1
        run_dir = base / f"{stem}_{counter}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def persist_run_setup(
    run_dir: Path,
    config: ExperimentConfig,
    raw_config: dict[str, Any],
    instances_count: int,
    config_hash: str | None = None,
) -> dict[str, Any]:
    digest = config_hash or stable_hash(raw_config)
    (run_dir / "config.yaml").write_text(
        yaml.safe_dump(raw_config, sort_keys=False),
        encoding="utf-8",
    )
    (run_dir / "config_hash.txt").write_text(f"{digest}\n", encoding="utf-8")
    metadata = build_run_metadata(config, digest, instances_count)
    write_json(run_dir / "run_metadata.json", metadata)
    write_json(run_dir / "metadata.json", metadata)
    return metadata


def build_run_metadata(
    config: ExperimentConfig,
    config_hash: str,
    instances_count: int,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(Path.cwd()),
        "python_version": sys.version.split()[0],
        "package_version": __version__,
        "seed": config.seed,
        "config_hash": config_hash,
        "number_of_instances": instances_count,
        "agents": list(config.agents),
        "run_name": config.run_name,
        "max_steps": config.max_steps,
        "num_repeats": config.num_repeats,
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_implementation": platform.python_implementation(),
        },
    }
