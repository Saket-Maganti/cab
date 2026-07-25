#!/usr/bin/env python3
"""Validate human audit sample schema (labels optional)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_path", default="data/human_validation/sample.jsonl", nargs="?")
    args = parser.parse_args()
    path = Path(args.sample_path)
    if not path.exists():
        print(f"missing sample (ok for build mode): {path}")
        return 0
    required = {"instance_id", "agent_name", "labels"}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = required - set(row)
        if missing:
            print(f"line {line_no}: missing fields {sorted(missing)}")
            return 1
    print(f"validated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
