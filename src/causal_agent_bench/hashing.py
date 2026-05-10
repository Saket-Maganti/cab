from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def stable_hash(data: Any, length: int = 16) -> str:
    """Return a deterministic hash for JSON-serializable config-like data."""

    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:length]


def config_hash(config: dict[str, Any] | str | Path, length: int = 16) -> str:
    """Hash a config mapping or a YAML/JSON config file."""

    if isinstance(config, str | Path):
        path = Path(config)
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(text) or {}
        else:
            payload = json.loads(text)
        return stable_hash(payload, length=length)
    return stable_hash(config, length=length)
