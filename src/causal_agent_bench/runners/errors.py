from __future__ import annotations

import traceback
from typing import Any


def runner_error_record(
    *,
    agent_name: str,
    instance_id: str,
    repeat: int,
    exc: BaseException,
    skipped: bool = True,
) -> dict[str, Any]:
    return {
        "agent": agent_name,
        "instance": instance_id,
        "repeat": repeat,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "traceback_summary": "".join(traceback.format_exception(exc, limit=8)),
        "skipped": skipped,
    }
