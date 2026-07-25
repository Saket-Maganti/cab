#!/usr/bin/env python3
"""Validate the no-run paper section evidence contract."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "paper" / "paper_section_contract.json"
DEFAULT_LEDGER = REPO_ROOT / "docs" / "claim_ledger.json"


@dataclass(frozen=True)
class ContractIssue:
    severity: str
    section_id: str
    message: str

    def format(self) -> str:
        return f"{self.severity.upper()}: {self.section_id}: {self.message}"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _claim_statuses(ledger_path: Path) -> dict[str, str]:
    ledger = _read_json(ledger_path)
    claims = ledger.get("claims")
    if not isinstance(claims, list):
        raise ValueError(f"{ledger_path} must contain a claims list")
    statuses: dict[str, str] = {}
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "")
        if claim_id:
            statuses[claim_id] = str(claim.get("status") or "")
    return statuses


def _contains_any(text: str, markers: list[str]) -> bool:
    lower = text.lower()
    return any(marker.lower() in lower for marker in markers)


def _matched_markers(text: str, markers: list[str]) -> list[str]:
    lower = text.lower()
    return [marker for marker in markers if marker.lower() in lower]


def _load_section_text(
    section: dict[str, Any],
    *,
    repo_root: Path,
) -> tuple[str, list[ContractIssue]]:
    section_id = str(section.get("section_id") or "<missing-section-id>")
    issues: list[ContractIssue] = []
    texts: list[str] = []
    files = section.get("paper_files")
    if not isinstance(files, list) or not files:
        return "", [ContractIssue("error", section_id, "paper_files must be a non-empty list")]

    for rel in files:
        path = repo_root / str(rel)
        if not path.exists():
            issues.append(ContractIssue("error", section_id, f"missing paper file: {rel}"))
            continue
        texts.append(path.read_text(encoding="utf-8"))
    return "\n".join(texts), issues


def check_paper_section_contract(
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
    ledger_path: str | Path = DEFAULT_LEDGER,
    repo_root: str | Path = REPO_ROOT,
    mode: str = "draft",
) -> list[ContractIssue]:
    """Return policy issues for the paper section contract."""

    root = Path(repo_root).resolve()
    contract_file = Path(contract_path).resolve()
    ledger_file = Path(ledger_path).resolve()
    issues: list[ContractIssue] = []

    try:
        contract = _read_json(contract_file)
        statuses = _claim_statuses(ledger_file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [ContractIssue("error", "contract", str(exc))]

    if contract.get("schema_version") != 1:
        issues.append(ContractIssue("error", "contract", "schema_version must be 1"))

    for rel in contract.get("linked_policy_docs", []):
        if not (root / str(rel)).exists():
            issues.append(ContractIssue("error", "contract", f"missing policy doc: {rel}"))

    sections = contract.get("sections")
    if not isinstance(sections, list) or not sections:
        return [*issues, ContractIssue("error", "contract", "sections must be a non-empty list")]

    seen_sections: set[str] = set()
    for section in sections:
        if not isinstance(section, dict):
            issues.append(ContractIssue("error", "contract", "section entry must be an object"))
            continue

        section_id = str(section.get("section_id") or "")
        if not section_id:
            issues.append(ContractIssue("error", "contract", "section missing section_id"))
            continue
        if section_id in seen_sections:
            issues.append(ContractIssue("error", section_id, "duplicate section_id"))
        seen_sections.add(section_id)

        text, file_issues = _load_section_text(section, repo_root=root)
        issues.extend(file_issues)

        claim_ids = [str(claim_id) for claim_id in section.get("claim_ids", [])]
        unknown = [claim_id for claim_id in claim_ids if claim_id not in statuses]
        if unknown:
            issues.append(
                ContractIssue("error", section_id, f"unknown claim id(s): {', '.join(unknown)}")
            )

        allowed_statuses = section.get("allowed_claim_statuses")
        if isinstance(allowed_statuses, list) and allowed_statuses:
            disallowed = [
                f"{claim_id}={statuses.get(claim_id)}"
                for claim_id in claim_ids
                if claim_id in statuses and statuses[claim_id] not in allowed_statuses
            ]
            if disallowed:
                issues.append(
                    ContractIssue(
                        "error",
                        section_id,
                        "claim status outside section policy: " + ", ".join(disallowed),
                    )
                )

        unsupported = [
            f"{claim_id}={statuses[claim_id]}"
            for claim_id in claim_ids
            if claim_id in statuses and statuses[claim_id] != "supported"
        ]
        markers = [str(marker) for marker in section.get("required_markers_when_any_claim_unsupported", [])]
        if unsupported and markers and not _contains_any(text, markers):
            issues.append(
                ContractIssue(
                    "error",
                    section_id,
                    "unsupported dependent claims lack required blocked/planned marker; "
                    f"claims: {', '.join(unsupported)}",
                )
            )

        forbidden = [str(phrase) for phrase in section.get("forbidden_when_any_claim_unsupported", [])]
        matched_forbidden = _matched_markers(text, forbidden) if unsupported else []
        if matched_forbidden:
            issues.append(
                ContractIssue(
                    "error",
                    section_id,
                    "forbidden result wording while claims are unsupported: "
                    + ", ".join(matched_forbidden),
                )
            )

        if mode == "submission":
            minimum_status = section.get("minimum_claim_status_for_submission")
            if minimum_status:
                not_ready = [
                    f"{claim_id}={statuses[claim_id]}"
                    for claim_id in claim_ids
                    if claim_id in statuses and statuses[claim_id] != minimum_status
                ]
                if not_ready:
                    issues.append(
                        ContractIssue(
                            "error",
                            section_id,
                            f"submission requires {minimum_status}: " + ", ".join(not_ready),
                        )
                    )
            if section.get("must_clear_markers_for_submission"):
                still_marked = _matched_markers(text, markers)
                if still_marked:
                    issues.append(
                        ContractIssue(
                            "error",
                            section_id,
                            "submission text still contains draft blocked/planned markers: "
                            + ", ".join(still_marked),
                        )
                    )

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate paper section evidence contract.")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--mode", choices=["draft", "submission"], default="draft")
    args = parser.parse_args(argv)

    issues = check_paper_section_contract(
        contract_path=args.contract,
        ledger_path=args.ledger,
        repo_root=args.repo_root,
        mode=args.mode,
    )
    for issue in issues:
        print(issue.format())
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        print(f"paper section contract failed: {len(errors)} error(s)")
        return 1
    print(f"paper section contract passed ({args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
