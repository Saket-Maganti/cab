from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"


def pytest_configure() -> None:
    existing = os.environ.get("PYTHONPATH")
    paths = [str(SRC), str(REPO_ROOT)]
    if existing:
        paths.append(existing)
    os.environ["PYTHONPATH"] = os.pathsep.join(paths)
