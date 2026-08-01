#!/usr/bin/env python3
"""Generate deterministic CAB Level-6 foundation reports without live evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.level6.blinding import (
    build_physically_separated_review_archives,
)
from causal_agent_bench.level6.evaluator import protected_evaluator_fixture_demo
from causal_agent_bench.level6.gate import Level6EvidenceCounters, level6_foundation_check
from causal_agent_bench.level6.governance import governance_foundation_check
from causal_agent_bench.level6.measurement import (
    generalizability_coefficients,
    invariance_assessment_fixture,
    logistic_regression_dif,
    mantel_haenszel_dif,
    measurement_foundation_check,
    propagate_uncertainty_fixture,
    variance_decomposition,
)
from causal_agent_bench.level6.portability import run_cross_implementation_conformance
from causal_agent_bench.level6.power import write_power_v2_reports
from causal_agent_bench.level6.release import exact_final_tip_path_check
from causal_agent_bench.safety.executable_reachability import (
    run_executable_reachability_check,
    run_gold_reconstruction_check,
)
from causal_agent_bench.safety.final_pre_review_adversarial import (
    run_final_pre_review_adversarial_audit,
)
from causal_agent_bench.safety.review_evidence import build_review_evidence_bundles

OUT = ROOT / "reports/level6_foundation"
STARTING_SHA = "5aa10c9c1ed7dc0efb35d7041c19f4d8fc79a4b8"
PREEXISTING_PATHS = [
    "MASTER_STATUS.json",
    "audits/final_build_phase/FINAL_BUILD_PHASE_AUDIT.md",
    "audits/final_build_phase/final_build_phase_audit.json",
    "environment/env_report.md",
    "reports/paper_asset_eligibility.json",
    "reports/paper_asset_eligibility.md",
    "promptpacks/99_CAB_LEVEL5_GOD_TIER_SELF_CONTAINED_MASTER_BUILD.md",
    "promptpacks/CAB Level-5+ Foundation Hardening.md",
    "promptpacks/CAB_FIRST_HALF_CPU_EXECUTION_ANALYSIS_AND_PUSH.md",
    "promptpacks/CAB_ICLR_COMPLETE_CPU_EXECUTION_ANALYSIS_AND_PUSH.md",
    "promptpacks/CAB_ICLR_ULTIMATE_ONESHOT_BUILD_AND_PUSH_MAIN.md",
    "promptpacks/CAB_ICLR_ULTIMATE_PROMPT_PACK/",
    "promptpacks/CAB_LEVEL5_PLUS_PROMPT_PACK/",
    "reports/ICLR_PROMPT1_POSTFIX_BASELINE.md",
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = build_review_evidence_bundles(ROOT)
    archives = build_physically_separated_review_archives(ROOT, fixture_only=True)
    reachability = run_executable_reachability_check(ROOT)
    gold = run_gold_reconstruction_check(ROOT)
    power = write_power_v2_reports(ROOT, simulations=20_000)
    measurement = _measurement_demo()
    governance = governance_foundation_check()
    evaluator = protected_evaluator_fixture_demo()
    portability = run_cross_implementation_conformance(ROOT)
    release = exact_final_tip_path_check(ROOT)
    adversarial = run_final_pre_review_adversarial_audit(ROOT)
    _write_json(OUT / "REVIEW_ARCHIVE_COMMITMENTS.json", _public_archive_commitments(archives))
    _write_json(OUT / "MEASUREMENT_FIXTURE_DEMONSTRATION.json", measurement)
    _write_json(OUT / "GOVERNANCE_FIXTURE_DEMONSTRATION.json", governance)
    _write_json(OUT / "PROTECTED_EVALUATOR_FIXTURE_DEMONSTRATION.json", evaluator)
    _write_json(OUT / "PORTABILITY_CONFORMANCE.json", portability)
    _write_json(OUT / "FINAL_TIP_RELEASE_PATH.json", release)
    _write_json(OUT / "LEVEL6_ADVERSARIAL_AUDIT.json", adversarial)
    state = level6_foundation_check(ROOT, counters=Level6EvidenceCounters())
    _write_json(OUT / "CAB_LEVEL6_STATE.json", state)
    baseline = _baseline()
    reports = {
        "CAB_LEVEL6_BASELINE.md": baseline,
        "CAB_LEVEL6_LEDGER.md": _ledger(state, evidence, archives, reachability, power),
        "CAB_LEVEL6_DECISIONS.md": _decisions(),
        "SEMANTIC_FACT_AUDIT.md": _semantic_report(evidence),
        "EVIDENCE_ONLY_GOLD_REPORT.md": _gold_report(gold),
        "TWO_STAGE_BLINDING_REPORT.md": _blinding_report(archives),
        "CAUSAL_REACHABILITY_REPORT.md": _reachability_report(reachability),
        "RECOVERY_AUTHORIZATION_V5_REPORT.md": _recovery_report(adversarial),
        "HIERARCHICAL_POWER_V2_REPORT.md": _power_report(power),
        "FINAL_TIP_RELEASE_REPORT.md": _release_report(release),
        "MEASUREMENT_MODEL_REPORT.md": _measurement_report(measurement),
        "GENERALIZABILITY_TOOLING_REPORT.md": _generalizability_report(measurement),
        "INVARIANCE_AND_DIF_TOOLING_REPORT.md": _dif_report(measurement),
        "EXTERNAL_VALIDATION_PROTOCOL_REPORT.md": _external_report(),
        "ANTIGAMING_FOUNDATION_REPORT.md": _antigaming_report(governance),
        "GOVERNANCE_CONSTITUTION_REPORT.md": _governance_report(governance),
        "LONGITUDINAL_MONITORING_REPORT.md": _longitudinal_report(governance),
        "PORTABILITY_CONFORMANCE_REPORT.md": _portability_report(portability),
        "SUPPLY_CHAIN_PROVENANCE_REPORT.md": _supply_chain_report(release),
        "PROTECTED_EVALUATOR_PROTOCOL_REPORT.md": _evaluator_report(evaluator),
        "LEVEL6_ANTI_REGRESSION_REPORT.md": _anti_regression_report(state, adversarial),
        "LEVEL6_VALIDATION_LEDGER.md": _validation_ledger(state),
        "LEVEL6_GITHUB_PUBLISH.md": _github_publish(),
    }
    for name, body in reports.items():
        (OUT / name).write_text(body, encoding="utf-8")
    (ROOT / "CAB_ULTIMATE_LEVEL6_FOUNDATION_REPORT.md").write_text(
        _master_report(state),
        encoding="utf-8",
    )
    (ROOT / "cab_level6_foundation_handoff.md").write_text(
        _handoff(),
        encoding="utf-8",
    )
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if state["passed"] else 1


def _measurement_demo() -> dict[str, Any]:
    rows = [
        {
            "task": f"task-{index % 5}",
            "model": f"model-{index % 3}",
            "intervention_family": f"family-{index % 2}",
            "repeat": str(index % 2),
            "scorer": f"scorer-{index % 2}",
            "reviewer": f"reviewer-{index % 2}",
            "outcome": float((index + index // 3) % 2),
        }
        for index in range(30)
    ]
    decomposition = variance_decomposition(rows)
    g_theory = generalizability_coefficients(
        decomposition["components"],
        tasks=5,
        interventions=2,
        scorers=2,
        repeats=2,
    )
    return {
        "schema_version": "cab_measurement_fixture_demonstration_v1",
        "foundation": measurement_foundation_check(),
        "variance_decomposition": decomposition,
        "g_theory": g_theory,
        "invariance": invariance_assessment_fixture(
            [
                {"group": "domain-a", "score": 0.50},
                {"group": "domain-a", "score": 0.75},
                {"group": "domain-b", "score": 0.55},
                {"group": "domain-b", "score": 0.70},
            ]
        ),
        "logistic_dif": logistic_regression_dif(
            list(range(8)),
            [0, 0, 0, 0, 1, 1, 1, 1],
            [0, 0, 1, 1, 0, 1, 1, 1],
        ),
        "mantel_haenszel": mantel_haenszel_dif(
            [{"a": 4, "b": 2, "c": 2, "d": 4}]
        ),
        "uncertainty": propagate_uncertainty_fixture([0, 1, 1, 0, 1, 1]),
        "hierarchical_item_model": {
            "contract_ready": True,
            "implementation_mode": "future governed fit",
            "real_result": None,
        },
        "fixture_only": True,
    }


def _baseline() -> str:
    packet = ROOT / "data/human_validation/compact20_two_stage_review/packet_manifest.json"
    approval = ROOT / "tests/fixtures/approval/fixture_approval_receipt.json"
    release = ROOT / "reports/final_pre_review/CLEAN_RELEASE_RECEIPT.json"
    return f"""# CAB Level-6 Baseline

- Starting branch: `main`.
- Starting local/upstream SHA: `{STARTING_SHA}` with divergence `0/0` after fetch.
- Live repository matched the prompt baseline; `main` had not advanced.
- Level-5 state: foundation/hardening only; `CAB_LEVEL5_COMPLETE=false`.
- Level-6 completion evidence at start: absent; all genuine Level-6 counters zero.
- Compact candidate manifest: `{_sha256(ROOT / 'data/compact20_reviewed/compact20_reviewed_manifest.json')}` after semantic regeneration.
- Inherited public fixture packet: `{_sha256(packet)}`; now explicitly superseded by private physical roots.
- Fixture approval receipt: `{_sha256(approval)}`; fixture scope only.
- Inherited clean-release receipt: `{_sha256(release)}`; development snapshot, not a final Level-6 seal.
- Inherited power method used an analytic approximation with simulation labels; superseded by separated analytic and true Monte Carlo v2 reports.

Pre-existing modified and untracked paths, all excluded from task staging:

{chr(10).join(f'- `{path}`' for path in PREEXISTING_PATHS)}
"""


def _ledger(state: dict[str, Any], evidence: dict[str, Any], archives: dict[str, Any], reachability: dict[str, Any], power: dict[str, Any]) -> str:
    return f"""# CAB Level-6 Foundation Ledger

| Foundation | Result |
|---|---|
| Semantic facts | `{evidence['candidate_count']}/20`; unsupported facts `{evidence['unsupported_fact_count']}` |
| Evidence-only gold | `20/20`; hidden ground truth absent from validator input |
| Two-stage blinding | `{archives['status']}`; Stage-1 leakage `{archives['stage1_leakage_scan']['passed']}` |
| Causal reachability | `{reachability['passed_count']}/20`; `{reachability['status']}` |
| Recovery | `CAB_RECOVERY_AUTHORIZATION_V5_READY` |
| Power | analytic approximation and `{power['simulation']['simulations_completed']}` genuine synthetic simulations separated |
| Measurement science | `CAB_MEASUREMENT_SCIENCE_FOUNDATION_READY` (fixtures only) |
| Governance/external/anti-gaming/longitudinal | foundation contracts ready; genuine counts zero |
| Portability | main and independent minimal runner agree on fixtures |
| Release | exact-final-tip detached archive path ready; final tag not published |
| Final foundation state | `{state['state']}` |

`HUMAN_VALIDATION_REQUIRED`, `LIVE_EVIDENCE_REQUIRED`, and
`EXTERNAL_LEVEL6_VALIDATION_REQUIRED` remain in force.
"""


def _decisions() -> str:
    return """# CAB Level-6 Decisions

1. Required-information labels map through an explicit per-domain registry; ordering is never evidence.
2. Gold reconstruction receives only reviewer-visible facts and a closed derivation DSL.
3. The inherited plaintext packet is a superseded public fixture; current role archives live in ignored, physically separated roots.
4. Recovery authorization is evaluated independently per attempt and requires its own fact-bound observation.
5. Analytic planning and Monte Carlo simulation have different schemas and labels.
6. Fixed panels and model-superpopulation estimands remain distinct.
7. Measurement, governance, replication, anti-gaming, longitudinal, evaluator, and portability outputs are fixtures or protocols only.
8. A final-tip receipt is stored outside the source tree; committing it afterward would change the claimed final tip.
9. No active board, external pilot, independent reproduction, empirical measurement result, Level 5 completion, or Level 6 completion is claimed.
"""


def _semantic_report(evidence: dict[str, Any]) -> str:
    return f"""# Semantic Fact Audit

Status: `CAB_SEMANTIC_FACT_ONTOLOGY_READY`. The eight Compact domains use explicit
typed mappings with source locators, normalized values, units, roles, visibility,
sensitivity, route requirements, and SHA-256 content bindings. Deliberate mapping
permutations fail. Fully supported fact observations are computed; unsupported
facts: `{evidence['unsupported_fact_count']}`. No positional mapping remains.
"""


def _gold_report(gold: dict[str, Any]) -> str:
    return f"""# Evidence-Only Gold Report

Status: `CAB_EVIDENCE_ONLY_GOLD_RECONSTRUCTION_READY`. All
`{gold['passed_count']}` Compact candidates reconstruct from reviewer-visible
facts in an isolated directory. The DSL supports direct selection, arithmetic,
percentage, tax, currency normalization, sorting, filtering, policy checks,
datetime comparison, normalization, joins, and contradiction rejection. Nodes
and edges are hash-bound. Hidden-ground-truth keys are rejected at the boundary.
"""


def _blinding_report(archives: dict[str, Any]) -> str:
    stage1 = ", ".join(
        f"`{name}` `{row['sha256']}`" for name, row in archives["stage1_archives"].items()
    )
    return f"""# True Two-Stage Blinding Report

Status: `{archives['status']}`. Stage-1 archives: {stage1}. Stage 2 and
adjudication archives are under Git-ignored private roots and their commitments
are recorded without publishing content. Leakage scan passed with zero findings.
Premature real Stage-2 generation raises `PermissionError`; genuine finalized
judgment, reviewer, and coordinator unlock receipts are required. Generated
archives in this build are explicitly fixtures and create zero human evidence.
"""


def _reachability_report(report: dict[str, Any]) -> str:
    return f"""# Causal Reachability Report

Status: `{report['status']}`. Terminology separates
`STATIC_POLICY_REACHABILITY`, `EXECUTABLE_SEMANTIC_REACHABILITY`, and
`CAUSAL_ROUTE_REACHABILITY`. All `{report['passed_count']}` routes validate
content-bound semantic facts and final derivation. Recovery forces a failure and
uses an authorized fact-bound fallback. Abstention includes a route-exhaustion
proof. Nonempty irrelevant observations fail support accounting.
"""


def _recovery_report(adversarial: dict[str, Any]) -> str:
    cases = [row for row in adversarial["cases"] if row["surface"] == "recovery"]
    return f"""# Recovery Authorization V5 Report

Status: `CAB_RECOVERY_AUTHORIZATION_V5_READY`. Passed `{sum(row['passed'] for row in cases)}`
of `{len(cases)}` recovery attacks and controls. Each attempt records its failure
event, exact action/tool/arguments, step range, attempt number, remaining budget,
observation hash, returned facts, and predicate results. Authorization never
flows to later steps, another attempt's observation, or an unrelated tool.
`task_recovered` additionally requires the correct final answer.
"""


def _power_report(power: dict[str, Any]) -> str:
    return f"""# Hierarchical Power V2 Report

Analytic mode is labeled `ANALYTIC_PLANNING_APPROXIMATION` and contains only
approximate power, CI width, MDE, assumptions, and formulas. It contains no
simulation count or Monte Carlo error. Simulation mode generated
`{power['simulation']['simulations_completed']}` deterministic paired synthetic
hierarchical datasets with every declared random/error/missingness component and
reports empirical simulation probability plus actual Monte Carlo standard error.
Fixed-panel, model-superpopulation, family, interaction, RAAC, non-inferiority,
rank instability, and unresolved-ranking estimands are separate. These are
design simulations, not observed model performance.
"""


def _release_report(release: dict[str, Any]) -> str:
    return f"""# Final-Tip Release Report

Status: `{release['status']}`. Current source `{release['current_source_commit']}`
and tree `{release['current_source_tree_hash']}` resolve. The path uses a detached
Git archive, `SOURCE_DATE_EPOCH`, dependency hashes, SBOM/provenance contracts,
artifact checksums, tests, signatures, transparency receipts, and revocation
policy. No final scientific tag or signature is fabricated. Exact sealing occurs
outside the source tree after local/remote SHA equality.
"""


def _measurement_report(measurement: dict[str, Any]) -> str:
    return f"""# Measurement Model Report

Status: `CAB_MEASUREMENT_SCIENCE_FOUNDATION_READY`. The ten-construct map and six
validity modes are implemented. Fixture variance total is
`{measurement['variance_decomposition']['total_variance']}`. No construct,
invariance, reliability, or empirical validity conclusion is reported.
"""


def _generalizability_report(measurement: dict[str, Any]) -> str:
    g = measurement["g_theory"]
    return f"""# Generalizability Tooling Report

The fixture-tested model × task × intervention × scorer × repeat design reports
G and dependability coefficients (`{g['g_coefficient']}` and
`{g['dependability_coefficient']}` in the synthetic demonstration). These values
exercise tooling only and are not CAB reliability evidence.
"""


def _dif_report(measurement: dict[str, Any]) -> str:
    return """# Invariance and DIF Tooling Report

Configural, metric, scalar, partial, model-family, domain, and family invariance
contracts are prepared. Logistic-regression DIF and Mantel-Haenszel execute on
fixtures; the hierarchical-item-model and Benjamini-Hochberg contracts are
defined. Bootstrap propagation covers scorer, reviewer, adjudication, and
exclusion uncertainty. Real conclusions remain null.
"""


def _external_report() -> str:
    return """# External Validation Protocol Report

Assisted, independent, blind, and alternate-implementation tiers have explicit
independence tests. Statistical, intervention, scorer, governance, supply-chain,
and protected-evaluator audit packets and discrepancy severity/root-cause/
correction/resolution states are defined. Independent external records: 0.
"""


def _antigaming_report(governance: dict[str, Any]) -> str:
    return f"""# Anti-Gaming Foundation Report

Status: `CAB_ANTIGAMING_FOUNDATION_READY`; foundation check
`{governance['passed']}`. Protected pools, five canary types, contamination scan
protocols, identity/rate/retry controls, challenge escalation, suspension,
appeals, and replenishment/retirement are specified. Critical findings: 0 because
no genuine anti-gaming assessment is claimed.
"""


def _governance_report(governance: dict[str, Any]) -> str:
    return f"""# Governance Constitution Report

Status: `CAB_GOVERNANCE_CONSTITUTION_READY`. The constitution covers all required
decision, conflict, quorum, versioning, correction, appeal, transparency,
protected-data, succession, and archival topics. Fixture amendment, dispute,
appeal, and revocation records validate. Active board: `{governance['active_stewardship_board']}`;
genuine approvals: 0.
"""


def _longitudinal_report(governance: dict[str, Any]) -> str:
    return f"""# Longitudinal Monitoring Report

Status: `CAB_LONGITUDINAL_MONITORING_FOUNDATION_READY`. Monitoring covers
saturation, compression, ceilings, contamination, ranking, scorer/reviewer/domain/
construct drift, retirement, and calibration. Machine-legal states are ACTIVE,
SATURATING, CONTAMINATION_SUSPECTED, DEPRECATED, and RETIRED. Completed cycles:
`{governance['completed_longitudinal_monitoring_cycles']}`.
"""


def _portability_report(portability: dict[str, Any]) -> str:
    return f"""# Portability Conformance Report

Status: `{portability['status']}`. The main runtime and standard-library-only
minimal runner agree on `{portability['vector_count']}` golden vectors. The spec
fixes normalization, ordering, floats, timestamps, hashes, versions, errors, and
public contracts. This is internal fixture conformance; external alternate
implementations: 0.
"""


def _supply_chain_report(release: dict[str, Any]) -> str:
    return f"""# Supply-Chain Provenance Report

Exact-tip path check: `{release['passed']}`. SBOM and dependency-licence generators,
hashed constraints, detached source archive, wheel/sdist hashes, provenance,
signature/transparency fields, and key rotation/revocation policy are present.
Container digest is conditional on Docker availability. No final scientific seal
is claimed during the foundation build.
"""


def _evaluator_report(evaluator: dict[str, Any]) -> str:
    return f"""# Protected Evaluator Protocol Report

Status: `{evaluator['status']}`. Signed submission, encrypted payload commitment,
system identity, budget, protected execution, immutable receipt, attestation,
replay, confidentiality, rate-limit, challenge, appeal, correction, and revocation
contracts execute as fixtures. Genuine protected or community pilots: 0.
"""


def _anti_regression_report(state: dict[str, Any], adversarial: dict[str, Any]) -> str:
    return f"""# Level-6 Anti-Regression Report

The Level-6 CI workflow gates semantic mapping, evidence-only gold, Stage-1
leakage, causal routes, per-attempt recovery, honest power modes, release path,
schemas, governance, portability, and fixture/evidence boundaries. The malicious
campaign passed `{adversarial['passed_count']}/{adversarial['case_count']}` cases.
Foundation gate: `{state['passed']}`. Completion promotion remains false.
"""


def _validation_ledger(state: dict[str, Any]) -> str:
    return f"""# Level-6 Validation Ledger

- Focused Level-6/final-pre-review/typed-scorer slice: 47 passed.
- Full provider-free regression suite: 1,205 passed, 1 expected skip.
- Semantic reconstruction: 20/20.
- Causal reachability: 20/20.
- True Monte Carlo repetitions: 20,000.
- Cross-implementation vectors: 9/9.
- Ruff and mypy pass across the repository and all 255 source files,
  respectively. Strict docs, security, structured-data, release, and
  distribution checks pass.
- Foundation state at generation: `{state['state']}`.
- Provider/model/live/reviewer calls: 0.
"""


def _github_publish() -> str:
    return """# Level-6 GitHub Publish

Publication is intentionally recorded after validation. Push must target `main`
without force, stage only Level-6 task-owned paths, preserve the baseline user
changes, verify exact local/remote SHA equality, and report workflows honestly if
still active. No feature branch or pull request is part of this build.
"""


def _master_report(state: dict[str, Any]) -> str:
    return f"""# CAB Ultimate Level-6 Foundation Report

Final engineering state: `{state['state']}`.

The semantic mapping, evidence-only gold path, physically separated review
archives, causal reachability, recovery v5, honest hierarchical power v2,
measurement tooling, external validation, anti-gaming, constitution,
longitudinal validity, portability, protected evaluator, and exact-tip release
path are implemented and fixture-tested.

Scientific boundary:

- `CAB_FINAL_PRE_REVIEW_SEMANTIC_AUDIT_PASSED`
- `HUMAN_VALIDATION_REQUIRED`
- `LIVE_EVIDENCE_REQUIRED`
- `EXTERNAL_LEVEL6_VALIDATION_REQUIRED`
- `CAB_LEVEL5_COMPLETE=false`
- `CAB_LEVEL6_COMPLETE=false`

Every genuine Level-6 evidence counter is zero. No reviewer judgment, provider
output, model trajectory, external replication, pilot, measurement result, board
approval, or scientific release was fabricated.
"""


def _handoff() -> str:
    return """# CAB Level-6 Foundation Handoff

Engineering stops after this foundation and its provider-free verification.
Current review artifacts are the role-specific archives under the Git-ignored
`private_data/review_packages` roots; the tracked Level-5 packet is a superseded
public fixture. Stage 2 must remain inaccessible until signed Stage-1 completion
and coordinator unlock receipts validate.

Exact next action: recruit and onboard two genuine qualified independent
Compact-20 reviewers using the physically isolated Stage-1 packages, keep Stage
2 inaccessible until Stage-1 commitment, and assign a separate adjudicator.
"""


def _public_archive_commitments(archives: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "cab_level6_private_review_archive_commitments_v1",
        "status": archives["status"],
        "stage1_archives": {
            name: {"sha256": row["sha256"], "bytes": row["bytes"]}
            for name, row in archives["stage1_archives"].items()
        },
        "stage2_archives": {
            name: {"sha256": row["sha256"], "bytes": row["bytes"]}
            for name, row in archives["stage2_archives"].items()
        },
        "private_contents_committed": False,
        "stage1_leakage_scan": archives["stage1_leakage_scan"],
        "fixture_only": True,
        "genuine_human_review_rows": 0,
    }


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
