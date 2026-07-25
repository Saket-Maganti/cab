from __future__ import annotations

import contextlib
import time
from pathlib import Path

from causal_agent_bench.runners.run_status import (
    build_run_status,
    format_run_status,
    resolve_run_dir,
)

# Run statuses where further refreshing is pointless: the run will not progress.
_TERMINAL_RUN_STATUSES = {"complete", "interrupted", "dry_run"}


def monitor_run(
    run_dir: str | Path | None = None,
    *,
    latest: bool = False,
    watch: bool = False,
    interval_seconds: float = 5.0,
    max_iterations: int | None = None,
) -> str:
    """Print a run-status snapshot, optionally watching until the run finishes.

    With ``watch=True`` the snapshot is reprinted every ``interval_seconds`` until
    the run reaches a terminal state (complete/interrupted), the optional
    ``max_iterations`` cap is hit, or the user interrupts with Ctrl+C. Returns the
    last rendered snapshot.
    """
    path = resolve_run_dir(run_dir, latest=latest)

    status = build_run_status(path)
    output = format_run_status(status)
    print(output, end="")
    if not watch:
        return output

    index = 1
    # Ctrl+C is the normal way to stop watching; exit cleanly without a traceback.
    with contextlib.suppress(KeyboardInterrupt):
        while status.get("run_status") not in _TERMINAL_RUN_STATUSES and (
            max_iterations is None or index < max_iterations
        ):
            time.sleep(interval_seconds)
            print()  # blank line separates consecutive snapshots
            status = build_run_status(path)
            output = format_run_status(status)
            print(output, end="")
            index += 1
    return output
