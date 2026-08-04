#!/usr/bin/env python3
"""Entry point for the reviewer-ready V2 packet and two-stage review workflow.

    python scripts/cab_review_ready_v2.py --help

Nothing this script can do performs model execution or genuine human review.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.review_ready_v2.cli import main

if __name__ == "__main__":
    raise SystemExit(main(repo_root=REPO_ROOT))
