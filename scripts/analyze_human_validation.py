#!/usr/bin/env python3
"""Summarize human validation annotations when present."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_path", default="data/human_validation/sample.jsonl", nargs="?")
    args = parser.parse_args()
    path = Path(args.sample_path)
    if not path.exists():
        print(f"no annotations yet: {path}")
        return 0
    total = 0
    labeled = 0
    label_counts: Counter[str] = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total += 1
        row = json.loads(line)
        labels = row.get("labels") or {}
        if labels:
            labeled += 1
            for key, value in labels.items():
                label_counts[f"{key}={value}"] += 1
    print(f"cases={total} labeled={labeled}")
    for key, count in label_counts.most_common():
        print(f"  {key}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
