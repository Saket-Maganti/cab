"""Machine-readable claim ledger validation and updates."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.run_completion import load_run_metadata

SCHEMA_VERSION = 3
VALID_STATUSES = frozenset(
    {"planned", "engineering_only", "supported", "weakened", "rejected"}
)

REQUIRED_CLAIM_FIELDS = frozenset(
    {
        "claim_id",
        "claim_text",
        "short_name",
        "status",
        "required_study",
        "required_evidence",
        "validation_threshold",
        "current_state",
        "allowed_wording",
        "forbidden_wording",
        "paper_location",
        "linked_run_dirs",
        "linked_tables_figures",
        "linked_validation_files",
        "current_evidence_paths",
        "blocking_items",
        "notes",
        "owner",
        "last_updated",
    }
)

CLAIM_TEXT_BY_ID: dict[str, str] = {
    "C1": "Clean success overestimates robust competence under intervention.",
    "C2": "Tool failure and memory corruption expose hidden weaknesses.",
    "C3": "Trajectory metrics detect failures missed by final-answer scoring.",
    "C4": "ACRS changes model rankings relative to clean success.",
    "C5": "Recovery ability is separable from planning ability.",
    "C6": "Simple self-checking improves some intervention families but not all.",
    "C7": "Some agents overuse tools even when unnecessary.",
    "C8": "Some agents stop prematurely under misleading success signals.",
    "C9": "CausalAgentBench smoke tests are reproducible without paid services.",
    "C10": "Controlled interventions isolate intended skill components.",
}

CLAIM_STUDY_BY_ID: dict[str, str] = {
    "C1": "Scale-100 confirmatory and Main-500 confirmatory paired evaluation",
    "C2": "Scale-100 and Main-500 intervention-family analysis",
    "C3": "Main-500 scorer validation with blinded human review",
    "C4": "Main-500 multi-model rank comparison with clustered bootstrap",
    "C5": "Main-500 component analysis and controlled recovery ablation",
    "C6": "Controlled prompt/scaffold ablation on a frozen task slice",
    "C7": "Main-500 irrelevant-tools family analysis",
    "C8": "Main-500 premature-success-signal family analysis",
    "C9": "Provider-free reproducibility validation in a fresh environment",
    "C10": "Independent two-reviewer intervention-isolation audit with adjudication",
}

CLAIM_THRESHOLD_BY_ID: dict[str, str] = {
    "C1": (
        "Complete matched pairs; preregistered uncertainty; audited scorer; "
        "direction and interval reported without suppressing null results."
    ),
    "C2": (
        "Family-matched denominators, at least the preregistered family sample, "
        "clustered intervals, and reviewed representative trajectories."
    ),
    "C3": (
        "Blinded human subset with two independent reviewers, adjudication, and "
        "reported scorer false-positive/false-negative uncertainty."
    ),
    "C4": (
        "At least three eligible non-oracle models on common matched units, with "
        "rank probabilities and clustered bootstrap intervals."
    ),
    "C5": (
        "Preregistered component or ablation contrast on common tasks with paired "
        "effect sizes and multiplicity disclosure."
    ),
    "C6": (
        "Frozen-task paired ablation with prompt hashes, equal budgets, uncertainty, "
        "and all intervention-family effects disclosed."
    ),
    "C7": (
        "Eligible irrelevant-tools runs with unnecessary-call rates, matched task "
        "success, uncertainty, and audited examples."
    ),
    "C8": (
        "Eligible premature-signal runs with matched premature-stop rates, success "
        "effects, uncertainty, and audited examples."
    ),
    "C9": (
        "Fresh provider-free install, CLI, validation, fixture, and test commands all "
        "pass from the documented environment."
    ),
    "C10": (
        "Every locked candidate has two independent genuine reviews; disagreements "
        "are adjudicated; raw agreement is at least 0.80; all final decisions pass."
    ),
}

CLAIM_PAPER_LOCATIONS: dict[str, list[str]] = {
    "C1": ["paper/latexpaper/sections/01_introduction.tex", "paper/latexpaper/sections/07_results.tex"],
    "C2": ["paper/latexpaper/sections/04_interventional_framework.tex", "paper/latexpaper/sections/07_results.tex"],
    "C3": ["paper/latexpaper/sections/05_metrics.tex", "paper/latexpaper/sections/08_human_validation.tex"],
    "C4": ["paper/latexpaper/sections/05_metrics.tex", "paper/latexpaper/sections/07_results.tex"],
    "C5": ["paper/latexpaper/sections/05_metrics.tex", "paper/latexpaper/sections/09_ablations.tex"],
    "C6": ["paper/latexpaper/sections/07_results.tex", "paper/latexpaper/sections/09_ablations.tex"],
    "C7": ["paper/latexpaper/sections/04_interventional_framework.tex", "paper/latexpaper/sections/07_results.tex"],
    "C8": ["paper/latexpaper/sections/04_interventional_framework.tex", "paper/latexpaper/sections/07_results.tex"],
    "C9": ["paper/latexpaper/sections/03_benchmark_design.tex", "paper/latexpaper/sections/11_ethics_reproducibility.tex"],
    "C10": ["paper/latexpaper/sections/04_interventional_framework.tex", "paper/latexpaper/sections/08_human_validation.tex"],
}

DEFAULT_ALLOWED_WORDING = [
    "State this item as a preregistered hypothesis, planned analysis, or unresolved question."
]
DEFAULT_FORBIDDEN_WORDING = [
    "Do not say the result is demonstrated, established, significant, or supported before the validation threshold is met."
]

CLAIM_ARTIFACT_MAP: dict[str, list[str]] = {
    "C1": [
        "tables/table2_main_agent_performance.csv",
        "figures/figure2_clean_vs_intervention_success.png",
    ],
    "C2": [
        "figures/figure3_intervention_family_breakdown.png",
        "tables/table3_intervention_family_performance.csv",
    ],
    "C3": ["figures/figure6_trajectory_final_disagreement.png"],
    "C4": [
        "figures/figure4_ranking_instability.png",
        "tables/table2_main_agent_performance.csv",
    ],
    "C5": [
        "tables/table2_main_agent_performance.csv",
        "tables/table4_ablation_results.csv",
    ],
    "C6": ["tables/table4_ablation_results.csv"],
    "C7": [
        "tables/table2_main_agent_performance.csv",
        "figures/figure5_failure_mode_distribution.png",
    ],
    "C8": ["figures/figure5_failure_mode_distribution.png"],
    "C10": ["tables/table5_human_validation_agreement.csv"],
}

CLAIM_VALIDATION_FILES: dict[str, list[str]] = {
    "C3": ["tables/table5_human_validation_agreement.csv"],
    "C10": [
        "tables/table5_human_validation_agreement.csv",
        "data/frozen/pilot_v0.1/intervention_audit_report.json",
    ],
}

NON_SCIENTIFIC_EVIDENCE_SCOPES = frozenset(
    {
        "pilot_stub_engineering_only",
        "deterministic_baseline_engineering",
        "engineering_only_local_stub",
        "mock_diagnostic_only",
    }
)

MOCK_STUB_DRY_EVIDENCE_MARKERS = frozenset(
    {
        "mock_diagnostic",
        "mock_diagnostic_only",
        "dry_run",
        "stub",
        "stub_engineering",
        "engineering_only",
        "preliminary_or_engineering",
        "interrupted",
        "incomplete",
    }
)

MAIN_CLAIMS_REQUIRING_HUMAN_VALIDATION = frozenset({"C3", "C10"})

SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT = frozenset(
    {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C10"}
)

CLAIMREF_RE = re.compile(r"\\claimref\{([^}]+)\}")
CLAIM_ID_RE = re.compile(r"C\d+")


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _resolve_path(path: str | Path, repo_root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def normalize_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Fill schema v3 fields and migrate legacy keys in place."""

    claim_id = str(claim.get("claim_id", ""))
    if not claim.get("claim_text"):
        claim["claim_text"] = CLAIM_TEXT_BY_ID.get(
            claim_id,
            str(claim.get("short_name", claim_id)).replace("_", " "),
        )
    if "linked_tables_figures" not in claim:
        claim["linked_tables_figures"] = list(claim.get("planned_artifacts", []))
    if "linked_run_dirs" not in claim:
        claim["linked_run_dirs"] = []
    if "linked_validation_files" not in claim:
        claim["linked_validation_files"] = list(
            CLAIM_VALIDATION_FILES.get(claim_id, [])
        )
    if "notes" not in claim:
        claim["notes"] = ""
    if "current_evidence_paths" not in claim:
        claim["current_evidence_paths"] = []
    if "required_study" not in claim:
        claim["required_study"] = CLAIM_STUDY_BY_ID.get(
            claim_id,
            "Study assignment required before claim promotion",
        )
    if "validation_threshold" not in claim:
        claim["validation_threshold"] = CLAIM_THRESHOLD_BY_ID.get(
            claim_id,
            "A preregistered validation threshold is required before claim promotion.",
        )
    if "current_state" not in claim:
        claim["current_state"] = (
            "ENGINEERING_ONLY"
            if claim.get("status") == "engineering_only"
            else "EXECUTION_PENDING"
        )
    if "allowed_wording" not in claim:
        claim["allowed_wording"] = list(DEFAULT_ALLOWED_WORDING)
    if "forbidden_wording" not in claim:
        claim["forbidden_wording"] = list(DEFAULT_FORBIDDEN_WORDING)
    if "paper_location" not in claim:
        claim["paper_location"] = list(
            CLAIM_PAPER_LOCATIONS.get(claim_id, ["paper location not assigned"])
        )
    return claim


def load_ledger(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("claim ledger root must be an object")
    claims = payload.get("claims")
    if not isinstance(claims, list):
        raise ValueError("claim ledger must contain a 'claims' list")
    for claim in claims:
        if isinstance(claim, dict):
            normalize_claim(claim)
    if payload.get("schema_version", 1) < SCHEMA_VERSION:
        payload["schema_version"] = SCHEMA_VERSION
    return payload


def save_ledger(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    payload["schema_version"] = SCHEMA_VERSION
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_claim_ledger(
    path: str | Path,
    repo_root: str | Path | None = None,
) -> list[str]:
    ledger_path = Path(path)
    root = Path(repo_root) if repo_root is not None else ledger_path.resolve().parents[1]
    errors: list[str] = []

    try:
        payload = load_ledger(ledger_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    claims = payload["claims"]
    seen_ids: set[str] = set()

    for index, claim in enumerate(claims, 1):
        if not isinstance(claim, dict):
            errors.append(f"claim #{index} is not an object")
            continue
        normalize_claim(claim)
        missing = sorted(REQUIRED_CLAIM_FIELDS - set(claim))
        if missing:
            errors.append(f"claim #{index} is missing fields: {', '.join(missing)}")

        claim_id = str(claim.get("claim_id", f"#{index}"))
        if claim_id in seen_ids:
            errors.append(f"duplicate claim_id: {claim_id}")
        seen_ids.add(claim_id)

        status = claim.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{claim_id}: invalid status {status!r}")

        for field in (
            "linked_run_dirs",
            "linked_tables_figures",
            "linked_validation_files",
            "current_evidence_paths",
            "blocking_items",
            "allowed_wording",
            "forbidden_wording",
            "paper_location",
        ):
            value = claim.get(field, [])
            if not isinstance(value, list):
                errors.append(f"{claim_id}: {field} must be a list")
            elif field in {"allowed_wording", "forbidden_wording", "paper_location"} and (
                not value or not all(isinstance(item, str) and item.strip() for item in value)
            ):
                errors.append(f"{claim_id}: {field} must contain at least one non-empty string")

        for field in ("required_study", "required_evidence", "validation_threshold", "current_state"):
            value = claim.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{claim_id}: {field} must be a non-empty string")

        if status == "supported":
            errors.extend(_validate_supported_claim(claim, claim_id, root))

    return errors


def validate_claim_evidence_levels(
    path: str | Path,
    repo_root: str | Path | None = None,
    *,
    mode: str = "draft",
) -> list[str]:
    """Enforce evidence-level policy on supported/weakened claims."""

    ledger_path = Path(path)
    root = Path(repo_root) if repo_root is not None else ledger_path.resolve().parents[1]
    issues: list[str] = []

    try:
        payload = load_ledger(ledger_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    for claim in payload["claims"]:
        if not isinstance(claim, dict):
            continue
        normalize_claim(claim)
        claim_id = str(claim.get("claim_id", ""))
        status = claim.get("status")
        if status not in {"supported", "weakened", "engineering_only"}:
            continue

        notes = str(claim.get("notes", "")).lower()
        evidence_paths = [str(p).lower() for p in claim.get("current_evidence_paths", [])]
        run_dirs = list(claim.get("linked_run_dirs", []))
        haystack = " ".join([*evidence_paths, notes, *run_dirs]).lower()

        if claim_id in SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT and status == "supported":
            if any(marker in haystack for marker in MOCK_STUB_DRY_EVIDENCE_MARKERS):
                msg = (
                    f"{claim_id}: supported status cannot rely on mock/stub/dry-run/interrupted evidence"
                )
                issues.append(msg if mode == "submission" else f"WARNING: {msg}")

        for run_rel in run_dirs:
            run_path = _resolve_path(run_rel, root)
            meta_path = run_path / "run_metadata.json"
            if not meta_path.exists():
                continue
            try:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            scope = str(metadata.get("evidence_scope", "")).lower()
            if claim_id in SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT and status == "supported":
                if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES or "mock" in scope:
                    msg = f"{claim_id}: supported claim links non-scientific run {run_rel} ({scope})"
                    issues.append(msg if mode == "submission" else f"WARNING: {msg}")
            if (run_path / "INCOMPLETE_RUN.json").exists() and status == "supported":
                msg = f"{claim_id}: supported claim links interrupted run {run_rel}"
                issues.append(msg if mode == "submission" else f"WARNING: {msg}")

        if status == "supported":
            required_fields = {
                "linked_run_dirs": run_dirs,
                "current_evidence_paths": claim.get("current_evidence_paths", []),
            }
            for field, value in required_fields.items():
                if not value:
                    issues.append(f"{claim_id}: supported claim missing {field}")

            if claim_id in MAIN_CLAIMS_REQUIRING_HUMAN_VALIDATION:
                validation_files = claim.get("linked_validation_files", [])
                missing = [
                    vf
                    for vf in validation_files
                    if not _resolve_path(str(vf), root).exists()
                ]
                if missing and mode == "submission":
                    issues.append(
                        f"{claim_id}: human validation claims require annotation artifacts: {missing}"
                    )
                elif missing:
                    issues.append(
                        f"WARNING: {claim_id}: missing human validation artifacts: {missing}"
                    )

        if status == "supported" and "local" in haystack and "main_experiment" not in haystack:
            if claim_id in {"C1", "C2", "C4", "C5", "C6", "C7", "C8"}:
                msg = f"{claim_id}: local_model_preliminary cannot fully support main-scale claim"
                issues.append(msg if mode == "submission" else f"WARNING: {msg}")

    return issues


def _validate_supported_claim(
    claim: dict[str, Any],
    claim_id: str,
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    evidence_paths = list(claim.get("current_evidence_paths", []))
    linked_runs = list(claim.get("linked_run_dirs", []))
    if not evidence_paths:
        errors.append(f"{claim_id}: supported claims require current_evidence_paths")
    if not linked_runs:
        errors.append(f"{claim_id}: supported claims require linked_run_dirs")
    for rel in evidence_paths + linked_runs + claim.get("linked_tables_figures", []):
        if not _resolve_path(str(rel), repo_root).exists():
            errors.append(f"{claim_id}: missing evidence artifact: {rel}")
    return errors


def extract_paper_claim_ids(paper_root: str | Path) -> set[str]:
    root = Path(paper_root)
    claim_ids: set[str] = set()
    for tex_path in sorted(root.rglob("*.tex")):
        text = tex_path.read_text(encoding="utf-8")
        for match in CLAIMREF_RE.finditer(text):
            for claim_id in CLAIM_ID_RE.findall(match.group(1)):
                claim_ids.add(claim_id)
    return claim_ids


def check_paper_claims(
    ledger_path: str | Path,
    paper_root: str | Path,
    repo_root: str | Path | None = None,
    *,
    mode: str = "draft",
) -> list[str]:
    """Return warnings/errors for claim references in paper sources."""

    ledger_path = Path(ledger_path)
    paper_root = Path(paper_root)
    issues: list[str] = []

    try:
        payload = load_ledger(ledger_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    claims_by_id = {
        str(claim["claim_id"]): normalize_claim(claim)
        for claim in payload["claims"]
        if isinstance(claim, dict) and claim.get("claim_id")
    }
    paper_ids = extract_paper_claim_ids(paper_root)

    for claim_id in sorted(paper_ids):
        if claim_id not in claims_by_id:
            issues.append(f"paper references unknown claim_id: {claim_id}")
            continue
        claim = claims_by_id[claim_id]
        status = claim.get("status")
        if status == "supported":
            if not claim.get("linked_run_dirs"):
                issues.append(
                    f"{claim_id}: paper cites supported claim without linked_run_dirs"
                )
            if not claim.get("current_evidence_paths"):
                issues.append(
                    f"{claim_id}: paper cites supported claim without current_evidence_paths"
                )
        elif status in {"planned", "engineering_only"} and mode == "submission":
            issues.append(
                f"{claim_id}: paper cites claim with status={status!r} in submission mode"
            )

    if mode == "submission":
        for claim_id, claim in claims_by_id.items():
            if claim.get("status") == "supported" and claim_id not in paper_ids:
                issues.append(
                    f"WARNING: {claim_id} is supported in ledger but not referenced in paper"
                )

    return issues


def claim_status_rows(claims: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        normalize_claim(claim)
        rows.append(
            {
                "claim_id": str(claim.get("claim_id", "")),
                "status": str(claim.get("status", "")),
                "current_state": str(claim.get("current_state", "")),
                "required_study": str(claim.get("required_study", "")),
                "validation_threshold": str(claim.get("validation_threshold", "")),
                "linked_runs": str(len(claim.get("linked_run_dirs", []))),
                "evidence_paths": str(len(claim.get("current_evidence_paths", []))),
            }
        )
    return rows


MANUAL_SUPPORTED_OVERRIDE_NOTE = (
    "WARNING: manual supported override — not verified by claim-evidence validator; "
    "not safe for paper claims without review."
)


def _validate_manual_supported_claim(
    claim_id: str,
    claim: dict[str, Any],
    repo_root: Path,
) -> None:
    """Strict gate for direct status=supported updates (non-promotion path)."""

    eligible, reason = _claim_eligible_for_supported_promotion(claim_id, repo_root)
    if not eligible:
        raise ValueError(
            f"refusing manual status=supported for {claim_id}: {reason}. "
            "Link a verified run with --run-dir --promote-to-supported, "
            "or pass --force-manual-supported to override (engineering review only)."
        )

    for run_rel in claim.get("linked_run_dirs", []):
        run_path = _resolve_path(str(run_rel), repo_root)
        if run_path.exists():
            _validate_run_for_claim_promotion(run_path, repo_root)


def update_claim_ledger(
    ledger_path: str | Path,
    *,
    claim_id: str | None = None,
    status: str | None = None,
    evidence_paths: list[str] | None = None,
    linked_run_dirs: list[str] | None = None,
    linked_tables_figures: list[str] | None = None,
    linked_validation_files: list[str] | None = None,
    notes: str | None = None,
    blocking_items: list[str] | None = None,
    repo_root: str | Path | None = None,
    force_manual_supported: bool = False,
) -> dict[str, Any]:
    path = Path(ledger_path)
    root = Path(repo_root) if repo_root is not None else path.resolve().parents[1]
    payload = load_ledger(path)
    claims = payload["claims"]

    if claim_id is None:
        return {"updated": False, "claims": claim_status_rows(claims)}

    target = next((claim for claim in claims if claim.get("claim_id") == claim_id), None)
    if target is None:
        raise ValueError(f"claim id not found: {claim_id}")
    normalize_claim(target)

    if status:
        if status not in VALID_STATUSES:
            raise ValueError(
                f"invalid claim status {status!r}; expected one of {sorted(VALID_STATUSES)}"
            )
        target["status"] = status
    if notes is not None:
        target["notes"] = notes

    def _merge_list_field(field: str, values: list[str] | None) -> None:
        if not values:
            return
        current = list(target.get(field, []))
        for value in values:
            if value not in current:
                current.append(value)
        target[field] = current

    _merge_list_field("current_evidence_paths", evidence_paths)
    _merge_list_field("linked_run_dirs", linked_run_dirs)
    _merge_list_field("linked_tables_figures", linked_tables_figures)
    _merge_list_field("linked_validation_files", linked_validation_files)
    _merge_list_field("blocking_items", blocking_items)

    target["last_updated"] = _today()

    if target.get("status") == "supported":
        if not force_manual_supported:
            _validate_manual_supported_claim(claim_id, target, root)
        else:
            existing_notes = str(target.get("notes", ""))
            if MANUAL_SUPPORTED_OVERRIDE_NOTE not in existing_notes:
                target["notes"] = (
                    f"{existing_notes} {MANUAL_SUPPORTED_OVERRIDE_NOTE}".strip()
                    if existing_notes
                    else MANUAL_SUPPORTED_OVERRIDE_NOTE
                )
        errors = _validate_supported_claim(target, claim_id, root)
        if errors:
            raise ValueError("; ".join(errors))

    save_ledger(path, payload)
    return {
        "updated": True,
        "claim": target,
        "force_manual_supported": force_manual_supported,
    }


def _relative_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


UNSAFE_PROMOTION_CLASSIFICATIONS = frozenset(
    {
        "mock_diagnostic",
        "stub_engineering",
        "local_preliminary",
        "incomplete",
        "interrupted",
        "unknown_needs_review",
        "complete_engineering_only",
    }
)

PROMOTION_SUPPORTED_CLASSIFICATIONS = frozenset({"provider_backed_pilot", "main_benchmark"})


def _artifact_claim_eligibility(rel: str, repo_root: Path) -> tuple[bool, str]:
    from causal_agent_bench.safety.claim_evidence_matrix import artifact_claim_eligibility

    return artifact_claim_eligibility(rel, repo_root)


def _human_validation_artifact_ready(repo_root: Path) -> bool:
    table_path = repo_root / "tables" / "table5_human_validation_agreement.csv"
    if not table_path.exists():
        return False
    text = table_path.read_text(encoding="utf-8").lower()
    if "not yet run" in text or "placeholder" in text:
        return False
    eligible, _ = _artifact_claim_eligibility(
        "tables/table5_human_validation_agreement.csv",
        repo_root,
    )
    return eligible


def _validate_run_for_claim_promotion(run_path: Path, repo_root: Path) -> dict[str, Any]:
    """Raise ValueError when a run cannot safely support promote-to-supported."""

    from causal_agent_bench.safety.common import classify_run_entry, strict_bool

    classified = classify_run_entry({"path": str(run_path)}, repo_root)
    metadata = load_run_metadata(run_path)
    reasons: list[str] = []

    if not metadata:
        reasons.append("missing run metadata")
    if classified.get("missing_metadata"):
        reasons.extend(
            f"missing metadata field: {field}" for field in classified["missing_metadata"]
        )
    classification = str(classified.get("classification", "unknown"))
    if classification in UNSAFE_PROMOTION_CLASSIFICATIONS:
        reasons.append(f"classification={classification}")
    if classification not in PROMOTION_SUPPORTED_CLASSIFICATIONS:
        reasons.append(
            f"classification={classification} is not verified provider/main evidence"
        )
    if not classified.get("paper_eligible"):
        reasons.append(str(classified.get("paper_eligibility_reason", "run not paper eligible")))
    if not strict_bool(metadata.get("scientific_evidence")):
        reasons.append("scientific_evidence is not true")
    if strict_bool(metadata.get("not_real_llm_behavior")):
        reasons.append("not_real_llm_behavior=true")
    if str(metadata.get("deployment_class") or "").lower() == "mock_diagnostic_only":
        reasons.append("deployment_class=mock_diagnostic_only")
    if strict_bool(metadata.get("engineering_only")):
        reasons.append("engineering_only=true")
    scope = str(metadata.get("evidence_scope") or "").lower()
    if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES or any(
        marker in scope for marker in MOCK_STUB_DRY_EVIDENCE_MARKERS
    ):
        reasons.append(f"non-scientific evidence_scope={scope or 'unknown'}")
    if (run_path / "INCOMPLETE_RUN.json").exists():
        reasons.append("INCOMPLETE_RUN.json present")

    if reasons:
        raise ValueError(
            f"refusing promote-to-supported for {run_path.name}: " + "; ".join(dict.fromkeys(reasons))
        )
    return classified


def _claim_eligible_for_supported_promotion(
    claim_id: str,
    repo_root: Path,
) -> tuple[bool, str]:
    if claim_id == "C9":
        return False, "C9 is reproducibility-only; use engineering_only unless stronger verified evidence exists"
    if claim_id not in CLAIM_ARTIFACT_MAP:
        return False, f"unknown claim_id {claim_id}"

    artifacts = list(CLAIM_ARTIFACT_MAP.get(claim_id, []))
    if not artifacts:
        return False, "no linked artifacts configured"

    ineligible: list[str] = []
    for rel in artifacts:
        eligible, reason = _artifact_claim_eligibility(rel, repo_root)
        if not eligible:
            ineligible.append(f"{rel} ({reason})")
    if ineligible:
        return False, "ineligible artifacts: " + ", ".join(ineligible)

    if claim_id in MAIN_CLAIMS_REQUIRING_HUMAN_VALIDATION:
        if not _human_validation_artifact_ready(repo_root):
            return False, "human-validation artifacts incomplete or placeholder (Table 5 text alone is insufficient)"
        validation_files = list(CLAIM_VALIDATION_FILES.get(claim_id, []))
        missing_validation = [
            vf
            for vf in validation_files
            if not (repo_root / vf).exists()
            or not _artifact_claim_eligibility(vf, repo_root)[0]
        ]
        if missing_validation:
            return False, f"missing human-validation files: {', '.join(missing_validation)}"

    return True, "eligible"


def _infer_status_from_run(run_dir: Path) -> str:
    metadata_path = run_dir / "run_metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        scope = str(metadata.get("evidence_scope", "")).lower()
        if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES:
            return "engineering_only"
    return "weakened"


def update_claim_ledger_from_run(
    ledger_path: str | Path,
    run_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    claim_ids: list[str] | None = None,
    status: str | None = None,
    notes: str | None = None,
    promote_to_supported: bool = False,
) -> dict[str, Any]:
    """Link a verified experiment run to claim ledger rows."""

    ledger_path = Path(ledger_path)
    root = Path(repo_root) if repo_root is not None else ledger_path.resolve().parents[1]
    run_path = Path(run_dir)
    if not run_path.is_absolute():
        run_path = root / run_path
    if not run_path.exists():
        raise ValueError(f"run directory does not exist: {run_path}")

    run_rel = _relative_to_repo(run_path, root)
    metadata_rel = f"{run_rel}/run_metadata.json"
    scores_rel = f"{run_rel}/scores.jsonl"
    summary_rel = f"{run_rel}/run_summary.md"

    base_evidence = [path for path in (run_rel, metadata_rel, scores_rel, summary_rel) if (root / path).exists()]
    if not base_evidence:
        base_evidence = [run_rel]

    if promote_to_supported:
        _validate_run_for_claim_promotion(run_path, root)

    inferred_status = status or (
        "supported" if promote_to_supported else _infer_status_from_run(run_path)
    )
    if inferred_status == "supported" and not promote_to_supported:
        inferred_status = "weakened"

    default_claims = [cid for cid in CLAIM_ARTIFACT_MAP if cid not in {"C9", "C10"}]
    selected = claim_ids or default_claims
    updates: list[dict[str, Any]] = []
    promoted: list[str] = []
    skipped: list[dict[str, str]] = []

    for claim_id in selected:
        artifacts = list(CLAIM_ARTIFACT_MAP.get(claim_id, []))
        validation = list(CLAIM_VALIDATION_FILES.get(claim_id, []))
        claim_status = inferred_status

        if promote_to_supported:
            eligible, reason = _claim_eligible_for_supported_promotion(claim_id, root)
            if not eligible:
                skipped.append({"claim_id": claim_id, "reason": reason})
                continue
            claim_status = "supported"
        elif claim_id == "C10" and claim_status == "supported":
            if not _human_validation_artifact_ready(root):
                claim_status = "weakened"

        result = update_claim_ledger(
            ledger_path,
            claim_id=claim_id,
            status=claim_status,
            evidence_paths=base_evidence + artifacts,
            linked_run_dirs=[run_rel],
            linked_tables_figures=artifacts,
            linked_validation_files=validation,
            notes=notes,
        )
        updates.append(result.get("claim", {}))
        if claim_status == "supported":
            promoted.append(claim_id)

    if promote_to_supported and not promoted:
        detail = "; ".join(f"{item['claim_id']}: {item['reason']}" for item in skipped) or "no eligible claims"
        raise ValueError(
            f"refusing promote-to-supported for {run_rel}: no claims could be promoted ({detail})"
        )

    return {
        "updated": True,
        "run_dir": run_rel,
        "status": inferred_status,
        "promote_to_supported": promote_to_supported,
        "claims_promoted": promoted,
        "claims_skipped": skipped,
        "claims_updated": [claim.get("claim_id") for claim in updates if claim.get("claim_id")],
        "claims": updates,
    }
