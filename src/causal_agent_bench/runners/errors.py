from __future__ import annotations

import traceback
from typing import Any

_TRANSIENT_ERROR_TYPES = {
    "TimeoutError",
    "ConnectionError",
    "ConnectionResetError",
    "BrokenPipeError",
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "InternalServerError",
    "ServiceUnavailableError",
}


def runner_error_record(
    *,
    agent_name: str,
    instance_id: str,
    repeat: int,
    exc: BaseException,
    skipped: bool = True,
    retriable: bool | None = None,
) -> dict[str, Any]:
    error_type = type(exc).__name__
    if retriable is None:
        retriable = error_type in _TRANSIENT_ERROR_TYPES
    return {
        "agent": agent_name,
        "instance": instance_id,
        "repeat": repeat,
        "error_type": error_type,
        "message": str(exc),
        "traceback_summary": "".join(traceback.format_exception(exc, limit=8)),
        "skipped": skipped,
        "retriable": retriable,
    }
