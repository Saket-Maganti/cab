from __future__ import annotations

import json
import random
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar, overload

import numpy as np
import yaml
from pydantic import BaseModel, TypeAdapter

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from disk."""

    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be an object: {path}")
    return data


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
        f.write("\n")


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_jsonl(path: str | Path, rows: Iterable[BaseModel | dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            payload = row.model_dump(mode="json") if isinstance(row, BaseModel) else row
            f.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


@overload
def read_jsonl(path: str | Path, model: type[T]) -> list[T]: ...
@overload
def read_jsonl(path: str | Path, model: None = ...) -> list[dict[str, Any]]: ...
def read_jsonl(path: str | Path, model: type[T] | None = None) -> list[T] | list[dict[str, Any]]:
    adapter = TypeAdapter(model) if model is not None else None
    rows: list[Any] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            rows.append(adapter.validate_python(payload) if adapter else payload)
    return rows


def set_deterministic_seed(seed: int) -> None:
    """Seed Python and NumPy RNGs for reproducible local smoke runs."""

    random.seed(seed)
    np.random.seed(seed)


def create_run_dir(base_dir: str | Path, run_name: str) -> Path:
    """Create and return a cross-platform run directory."""

    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in run_name)
    run_dir = Path(base_dir) / safe_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
