from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.io import (
    create_run_dir,
    load_yaml,
    read_json,
    read_jsonl,
    set_deterministic_seed,
    write_json,
    write_jsonl,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def git_commit(cwd: str | Path | None = None) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    commit = result.stdout.strip()
    return commit or None


__all__ = [
    "create_run_dir",
    "git_commit",
    "load_yaml",
    "read_json",
    "read_jsonl",
    "set_deterministic_seed",
    "stable_hash",
    "utc_now",
    "write_json",
    "write_jsonl",
]
