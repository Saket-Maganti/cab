#!/usr/bin/env python3
"""Idempotent repair for web_shadow_25 docs-hub answer leakage (processed data only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.safety.answer_leakage_repair import validate_answer_leakage_cleared

DATASET = ROOT / "data/processed/web_shadow_25"
OLD_INSTRUCTION = "Open the documentation hub and report its page title."
NEW_INSTRUCTION = (
    "Open the docs landing page linked from the site navigation index and report its page title."
)
OLD_SUCCESS = "Reports documentation hub title"
NEW_SUCCESS = "Reports the landing page title discovered via navigation"
TASK_IDS = {"webshadow_web_snapshot_docs_hub_medium", "webshadow_api_docs_hub_medium"}


def _patch_goal(goal: dict) -> bool:
    changed = False
    ui = str(goal.get("user_instruction") or "")
    if OLD_INSTRUCTION in ui or "documentation hub" in ui.lower():
        goal["user_instruction"] = ui.replace(OLD_INSTRUCTION, NEW_INSTRUCTION)
        if "documentation hub" in goal["user_instruction"].lower():
            goal["user_instruction"] = NEW_INSTRUCTION
        changed = True
    sc = goal.get("success_criteria")
    if isinstance(sc, list):
        new_sc = []
        for item in sc:
            text = str(item)
            if OLD_SUCCESS in text or "documentation hub" in text.lower():
                new_sc.append(NEW_SUCCESS)
                changed = True
            else:
                new_sc.append(item)
        goal["success_criteria"] = new_sc
    return changed


def _patch_row(row: dict) -> bool:
    changed = False
    tid = str(row.get("task_id") or "")
    base = row.get("base_task") if isinstance(row.get("base_task"), dict) else None
    if base:
        tid = tid or str(base.get("task_id") or "")
    if tid not in TASK_IDS and OLD_INSTRUCTION not in json.dumps(row, ensure_ascii=False).lower():
        return False
    goal = row.get("goal")
    if isinstance(goal, dict) and _patch_goal(goal):
        changed = True
    if isinstance(base, dict):
        bgoal = base.get("goal")
        if isinstance(bgoal, dict) and _patch_goal(bgoal):
            changed = True
    return changed


def repair_dataset(*, dry_run: bool = False) -> dict:
    stats = {"files_touched": 0, "lines_changed": 0, "files": []}
    for path in sorted(DATASET.glob("*.jsonl")):
        lines_out: list[str] = []
        file_changed = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if _patch_row(row):
                file_changed += 1
            lines_out.append(json.dumps(row, ensure_ascii=False))
        if file_changed:
            stats["files_touched"] += 1
            stats["lines_changed"] += file_changed
            stats["files"].append(str(path.relative_to(ROOT)))
            if not dry_run:
                path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    stats = repair_dataset(dry_run=args.dry_run)
    print(json.dumps(stats, indent=2))
    if args.dry_run:
        return 0
    for rel in stats["files"]:
        path = ROOT / rel
        result = validate_answer_leakage_cleared(ROOT, path)
        if not result.get("passed"):
            print(f"validation failed for {rel}: {result.get('remaining')}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
