"""Performance guard for the CLI lazy-import contract.

Importing the CLI (and running lightweight commands like ``--help``, ``generate``,
``validate``) must NOT pull in the heavy optional dependency stack — pandas, scipy,
and matplotlib. Those are imported lazily inside the analysis/plotting command
branches that actually need them, which keeps CLI startup at ~0.4s instead of ~1.1s.

If this test fails, a module-level ``import pandas`` / ``scipy`` / ``matplotlib``
(or an eager import of an analysis module that pulls them) has crept back into the
CLI import graph — move it into the command branch that needs it.
"""

from __future__ import annotations

import subprocess
import sys

HEAVY_DEPS = ("pandas", "scipy", "matplotlib")


def _heavy_modules_after_import(module: str) -> list[str]:
    """Import ``module`` in a clean subprocess; return which heavy deps it loaded."""
    code = (
        "import importlib, sys\n"
        f"importlib.import_module({module!r})\n"
        f"loaded = [m for m in {HEAVY_DEPS!r} if m in sys.modules]\n"
        "print(' '.join(loaded))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    return [name for name in result.stdout.split() if name]


def test_importing_cli_does_not_load_heavy_deps() -> None:
    loaded = _heavy_modules_after_import("causal_agent_bench.cli")
    assert loaded == [], (
        f"Importing the CLI eagerly loaded heavy deps {loaded}. "
        "Move that import into the command branch that needs it (see cli.py)."
    )


def test_importing_top_package_does_not_load_heavy_deps() -> None:
    loaded = _heavy_modules_after_import("causal_agent_bench")
    assert loaded == [], f"Importing the top package eagerly loaded heavy deps {loaded}."
