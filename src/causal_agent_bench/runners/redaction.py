from __future__ import annotations

import re
from typing import Any

SECRET_KEY_MARKERS = ("api_key", "apikey", "secret", "password", "token", "authorization")
SAFE_METADATA_KEYS = frozenset(
    {
        "api_keys_persisted",
        "environment_dump_persisted",
        "redaction",
        "api_key_env",
    }
)
FORBIDDEN_DUMP_KEYS = frozenset({"environment", "environ", "os_environ", "env_dump"})
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]+|xox[baprs]-[A-Za-z0-9-]+)"
)


def redact_config_for_persistence(value: Any) -> Any:
    """Return a config-safe copy that never persists secrets or environment dumps."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered in FORBIDDEN_DUMP_KEYS:
                continue
            if (
                key_text not in SAFE_METADATA_KEYS
                and _is_secret_key(lowered)
                and not _is_env_placeholder(item)
            ):
                redacted[key] = "<redacted>"
                continue
            redacted[key] = redact_config_for_persistence(item)
        return redacted
    if isinstance(value, list):
        return [redact_config_for_persistence(item) for item in value]
    if isinstance(value, str):
        return SECRET_VALUE_PATTERN.sub("<redacted>", value)
    return value


def sanitize_metadata(value: Any) -> Any:
    """Sanitize run/trajectory metadata before writing JSON artifacts."""

    sanitized = redact_config_for_persistence(value)
    if isinstance(sanitized, dict):
        sanitized.pop("environment", None)
        sanitized.pop("environ", None)
        sanitized.pop("env_dump", None)
    return sanitized


def _is_secret_key(lowered: str) -> bool:
    return any(
        lowered == marker
        or lowered.endswith(f"_{marker}")
        or lowered.startswith(f"{marker}_")
        for marker in SECRET_KEY_MARKERS
    )


def _is_env_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.startswith("${") and ":-" in value
