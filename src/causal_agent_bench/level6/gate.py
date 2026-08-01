"""Honest CAB Level-6 maturity state and evidence gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.level6.evaluator import protected_evaluator_fixture_demo
from causal_agent_bench.level6.gold import (
    compact_derivation_spec,
    reconstruct_in_isolated_directory,
)
from causal_agent_bench.level6.governance import governance_foundation_check
from causal_agent_bench.level6.measurement import measurement_foundation_check
from causal_agent_bench.level6.portability import run_cross_implementation_conformance
from causal_agent_bench.level6.release import exact_final_tip_path_check
from causal_agent_bench.level6.semantic import (
    build_compact_semantic_facts,
    build_controlled_evidence_artifact,
)
from causal_agent_bench.schemas import BenchmarkInstance
from causal_agent_bench.utils.io import read_jsonl

Level6State = Literal[
    "CAB_LEVEL6_FOUNDATION_INCOMPLETE",
    "CAB_LEVEL6_FOUNDATION_READY",
    "CAB_LEVEL6_EVIDENCE_CANDIDATE",
    "CAB_LEVEL6_RELEASE_CANDIDATE",
    "CAB_LEVEL6_COMPLETE",
]


class Level6EvidenceCounters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic_evidence_audits: int = Field(default=0, ge=0)
    measurement_model_validations: int = Field(default=0, ge=0)
    measurement_invariance_assessments: int = Field(default=0, ge=0)
    differential_item_functioning_assessments: int = Field(default=0, ge=0)
    generalizability_studies: int = Field(default=0, ge=0)
    independent_reproductions: int = Field(default=0, ge=0)
    blind_external_reproductions: int = Field(default=0, ge=0)
    alternate_implementations: int = Field(default=0, ge=0)
    independent_statistical_audits: int = Field(default=0, ge=0)
    independent_intervention_validity_audits: int = Field(default=0, ge=0)
    protected_evaluator_external_pilots: int = Field(default=0, ge=0)
    community_external_pilots: int = Field(default=0, ge=0)
    external_transfer_studies: int = Field(default=0, ge=0)
    longitudinal_monitoring_cycles: int = Field(default=0, ge=0)
    stewardship_board_approvals: int = Field(default=0, ge=0)
    critical_antigaming_findings: int = Field(default=0, ge=0)
    critical_governance_findings: int = Field(default=0, ge=0)


COMPLETION_MINIMUMS = {
    "semantic_evidence_audits": 1,
    "measurement_model_validations": 1,
    "measurement_invariance_assessments": 1,
    "differential_item_functioning_assessments": 1,
    "generalizability_studies": 1,
    "independent_reproductions": 2,
    "blind_external_reproductions": 1,
    "alternate_implementations": 1,
    "independent_statistical_audits": 1,
    "independent_intervention_validity_audits": 1,
    "protected_evaluator_external_pilots": 2,
    "community_external_pilots": 2,
    "external_transfer_studies": 1,
    "longitudinal_monitoring_cycles": 1,
    "stewardship_board_approvals": 1,
}


def level6_completion_check(
    counters: Level6EvidenceCounters,
    *,
    level5_complete: bool,
    exact_final_tag_reproducible_build: bool,
) -> dict[str, Any]:
    values = counters.model_dump(mode="json")
    checks = {
        "CAB_LEVEL5_COMPLETE": level5_complete,
        **{
            key: int(values[key]) >= minimum
            for key, minimum in COMPLETION_MINIMUMS.items()
        },
        "critical_antigaming_findings_zero": counters.critical_antigaming_findings == 0,
        "critical_governance_findings_zero": counters.critical_governance_findings == 0,
        "exact_final_tag_reproducible_build": exact_final_tag_reproducible_build,
    }
    return {
        "state": "CAB_LEVEL6_COMPLETE" if all(checks.values()) else "CAB_LEVEL6_EVIDENCE_CANDIDATE",
        "CAB_LEVEL6_COMPLETE": all(checks.values()),
        "checks": checks,
        "failed_checks": sorted(name for name, value in checks.items() if not value),
    }


def level6_foundation_check(
    repo_root: str | Path,
    *,
    counters: Level6EvidenceCounters | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    evidence = counters or Level6EvidenceCounters()
    instances = read_jsonl(
        root / "data/compact20_reviewed/compact20_v2_instances.jsonl",
        BenchmarkInstance,
    )
    clean = [row for row in instances if row.condition == "clean"]
    semantic_passed = 0
    reconstruction_passed = 0
    for instance in clean:
        facts = build_compact_semantic_facts(instance)
        semantic_passed += bool(facts)
        artifact = build_controlled_evidence_artifact(
            instance,
            candidate_id=f"gate.{instance.instance_id}",
        )
        result = reconstruct_in_isolated_directory(
            artifact,
            compact_derivation_spec(instance.base_task.domain),
        )
        reconstruction_passed += result["output"] == instance.base_task.goal.expected_final_answer
    measurement = measurement_foundation_check()
    governance = governance_foundation_check()
    portability = run_cross_implementation_conformance(root)
    evaluator = protected_evaluator_fixture_demo()
    release = exact_final_tip_path_check(root)
    simulation_path = root / "reports/level6_foundation/HIERARCHICAL_POWER_MONTE_CARLO_V2.json"
    simulation = _read_json(simulation_path)
    required_paths = [
        "docs/CAB_BENCHMARK_CONSTITUTION.md",
        "docs/level6/LANGUAGE_NEUTRAL_SPEC.md",
        "docs/level6/MEASUREMENT_MODEL.md",
        "docs/level6/EXTERNAL_VALIDATION_PROTOCOL.md",
        "docs/level6/ANTI_GAMING_AND_CONTAMINATION.md",
        "docs/level6/LONGITUDINAL_VALIDITY.md",
        "docs/level6/PROTECTED_EVALUATOR_PROTOCOL.md",
        "spec/level6/conformance_vectors.json",
        "spec/level6/schemas/level6_evidence_counters.schema.json",
    ]
    counters_zero = all(value == 0 for value in evidence.model_dump().values())
    checks = {
        "semantic_fact_ontology": semantic_passed == len(clean) and len(clean) > 0,
        "evidence_only_gold_reconstruction": reconstruction_passed == len(clean),
        "true_two_stage_blinding_contract": (
            root / "src/causal_agent_bench/level6/blinding.py"
        ).is_file(),
        "causal_reachability_contract": (
            root / "src/causal_agent_bench/safety/executable_reachability.py"
        ).is_file(),
        "recovery_authorization_v5": (
            root / "src/causal_agent_bench/level6/recovery.py"
        ).is_file(),
        "hierarchical_power_v2": simulation.get("simulations_completed", 0) >= 20_000,
        "measurement_foundation": measurement["passed"],
        "governance_antigaming_longitudinal_external": governance["passed"],
        "portability_conformance": portability["passed"],
        "protected_evaluator_protocol": evaluator["status"]
        == "CAB_PROTECTED_EVALUATOR_PROTOCOL_READY",
        "exact_final_tip_release_path": release["passed"],
        "schemas_and_protocols_present": all((root / path).is_file() for path in required_paths),
        "genuine_level6_counters_zero": counters_zero,
        "CAB_LEVEL5_COMPLETE_false": True,
        "CAB_LEVEL6_COMPLETE_false": True,
    }
    foundation_ready = all(checks.values())
    completion = level6_completion_check(
        evidence,
        level5_complete=False,
        exact_final_tag_reproducible_build=False,
    )
    return {
        "schema_version": "cab_level6_foundation_gate_v1",
        "state": (
            "CAB_LEVEL6_FOUNDATION_READY"
            if foundation_ready
            else "CAB_LEVEL6_FOUNDATION_INCOMPLETE"
        ),
        "passed": foundation_ready,
        "checks": checks,
        "failed_checks": sorted(name for name, value in checks.items() if not value),
        "genuine_evidence": evidence.model_dump(mode="json"),
        "completion_attempt": completion,
        "CAB_LEVEL5_COMPLETE": False,
        "CAB_LEVEL6_COMPLETE": False,
        "human_validation_state": "HUMAN_VALIDATION_REQUIRED",
        "live_evidence_state": "LIVE_EVIDENCE_REQUIRED",
        "external_validation_state": "EXTERNAL_LEVEL6_VALIDATION_REQUIRED",
        "fixture_outputs_promoted_to_evidence": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


__all__ = [
    "COMPLETION_MINIMUMS",
    "Level6EvidenceCounters",
    "level6_completion_check",
    "level6_foundation_check",
]
