"""Focused tests for the reviewer-ready V2 repair.

Every test here is provider-free and fixture-only.  Nothing in this module
performs model execution, genuine human review, or produces genuine evidence.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.catalog import (
    DESIGN_MATRIX,
    OBJECTIVES,
    TARGET_FAMILY_ROUTE_MATRIX,
)
from causal_agent_bench.review_ready_v2.common import FIXTURE_MARKER, structural_diff
from causal_agent_bench.review_ready_v2.design import (
    anchor_audit,
    composition_audit,
    confounding_audit,
    design_audit,
    semantic_diversity_audit,
)
from causal_agent_bench.review_ready_v2.evidence import (
    primitive_evidence_report,
    scan_answer_bearing,
)
from causal_agent_bench.review_ready_v2.fixture_e2e import run_fixture_e2e
from causal_agent_bench.review_ready_v2.hostile import hostile_route_audit
from causal_agent_bench.review_ready_v2.leakage import (
    _extract,
    pair_secrets,
    stage1_leakage_audit,
    usability_audit,
)
from causal_agent_bench.review_ready_v2.models import PairSpec
from causal_agent_bench.review_ready_v2.operators import (
    OperatorError,
    corrupt_memory_field,
    inject_conflicting_observation,
    inject_tool_failure,
    isolation_audit,
    remove_tool,
)
from causal_agent_bench.review_ready_v2.pairs import PairGenerationError, build_all_pairs
from causal_agent_bench.review_ready_v2.qualification import (
    build_private_qualification,
    score_qualification,
)
from causal_agent_bench.review_ready_v2.registry import (
    RETIRED_PACKETS,
    RetiredPacketError,
    enforce_active_packet,
    retired_packet_registry,
    retirement_enforcement_report,
)
from causal_agent_bench.review_ready_v2.roles import REVIEWER_A, REVIEWER_B
from causal_agent_bench.review_ready_v2.routes import (
    validate_clean_route,
    validate_intervention_route,
)
from causal_agent_bench.review_ready_v2.runtime import (
    ToolExecutionError,
    ToolRuntime,
    audit_tool_contracts,
    execute_available_route,
)
from causal_agent_bench.review_ready_v2.stage1 import (
    REVIEW_DIMENSIONS,
    REVIEW_FORM_COLUMNS,
    build_stage1_package,
    stage1_item,
)
from causal_agent_bench.review_ready_v2.vault import (
    KEY_ENV,
    VaultError,
    load_or_create_key,
    resolve_key_path,
    seal,
    unseal,
    write_vault,
)
from causal_agent_bench.review_ready_v2.workflow import (
    GATING_DIMENSIONS,
    ReviewWorkspace,
    WorkflowError,
    validate_stage1_submission,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED = hashlib.sha256(b"cab-review-ready-v2-test-seed").digest()


@pytest.fixture(scope="module")
def pairs() -> list[PairSpec]:
    return build_all_pairs(SEED)


# ---------------------------------------------------------------------------
# scientific design
# ---------------------------------------------------------------------------


def test_twenty_explicit_clean_intervention_pairs(pairs: list[PairSpec]) -> None:
    assert len(pairs) == 20
    for pair in pairs:
        assert pair.clean_instance_id != pair.intervention_instance_id
        assert pair.clean_environment != pair.intervention_environment
        assert pair.shared_goal == pair.clean_environment.goal == pair.intervention_environment.goal


def test_composition_matches_the_frozen_design(pairs: list[PairSpec]) -> None:
    report = composition_audit(pairs)
    assert report["passed"], report["checks"]
    assert report["difficulty_counts"] == {"easy": 4, "hard": 4, "medium": 8, "stress": 4}
    assert len(report["domain_counts"]) >= 8
    assert max(report["domain_counts"].values()) <= 3


def test_sixteen_distinct_semantic_objectives(pairs: list[PairSpec]) -> None:
    report = semantic_diversity_audit(pairs)
    assert report["distinct_objective_signatures"] >= 16
    assert report["passed"], report["checks"]
    assert not report["generic_prompt_pairs"]


def test_no_generic_placeholder_prompts(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        assert "resolve request" not in pair.clean_prompt.casefold()
        assert len(pair.clean_prompt) > 120
        assert pair.clean_prompt == pair.intervention_prompt


def test_four_true_controlled_anchors(pairs: list[PairSpec]) -> None:
    report = anchor_audit(pairs)
    assert report["passed"], report["checks"]
    assert len(report["groups"]) == 4
    for group in report["groups"]:
        assert group["checks"]["same_answer_logic_numeric_values"]
        assert group["checks"]["identifier_labels_differ"]
        assert group["checks"]["record_order_differs"]
        assert group["checks"]["instances_are_not_byte_identical"]


def test_family_and_response_type_are_not_confounded(pairs: list[PairSpec]) -> None:
    report = confounding_audit(pairs)
    assert report["passed"], report["checks"]
    assert report["family_route_matrix"] == TARGET_FAMILY_ROUTE_MATRIX
    assert all(count >= 2 for count in report["routes_per_family"].values())
    assert all(count >= 2 for count in report["families_per_route"].values())


def test_design_matrix_is_frozen_and_consistent() -> None:
    assert len(DESIGN_MATRIX) == 20
    assert {plan.objective_id for plan in DESIGN_MATRIX} <= set(OBJECTIVES)
    anchors = [plan for plan in DESIGN_MATRIX if plan.anchor_group_id]
    assert len(anchors) == 4
    assert len({plan.family for plan in anchors}) == 4


# ---------------------------------------------------------------------------
# intervention operators
# ---------------------------------------------------------------------------


def test_every_intervention_is_an_executable_mutation(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        report = isolation_audit(
            pair.clean_environment, pair.intervention_environment, pair.intervention_patch
        )
        assert report["passed"], (pair.intervention_operator, report["checks"])
        assert report["checks"]["exactly_one_intended_mutation_unit"]
        assert report["checks"]["no_unexpected_mutation"]
        assert report["diff"], "an intervention must actually change the environment"


def test_all_four_operators_are_exercised(pairs: list[PairSpec]) -> None:
    assert {pair.intervention_operator for pair in pairs} == {
        "remove_tool",
        "inject_tool_failure",
        "corrupt_memory_field",
        "inject_conflicting_observation",
    }


def test_tool_removal_removes_exactly_one_capability(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        if pair.intervention_operator != "remove_tool":
            continue
        clean = {row.tool_id for row in pair.clean_environment.tools}
        intervention = {row.tool_id for row in pair.intervention_environment.tools}
        assert len(clean - intervention) == 1
        assert not intervention - clean


def test_tool_failure_keeps_the_tool_declared(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        if pair.intervention_operator != "inject_tool_failure":
            continue
        assert len(pair.intervention_environment.injected_failures) == 1
        for tool_id, failure_class in pair.intervention_environment.injected_failures.items():
            contract = pair.intervention_environment.tool(tool_id)
            assert contract is not None
            assert failure_class in contract.failure_modes


def test_memory_corruption_requires_a_valid_clean_predecessor(pairs: list[PairSpec]) -> None:
    pair = next(p for p in pairs if p.intervention_operator == "corrupt_memory_field")
    with pytest.raises(OperatorError):
        corrupt_memory_field(pair.clean_environment, "field_that_never_existed", "x")


def test_conflict_injection_requires_a_real_conflict(pairs: list[PairSpec]) -> None:
    pair = next(p for p in pairs if p.intervention_operator == "inject_conflicting_observation")
    name, value = next(
        (n, v) for n, v in pair.clean_environment.sources.items() if isinstance(v, dict) and v
    )
    field = sorted(value)[0]
    with pytest.raises(OperatorError):
        inject_conflicting_observation(pair.clean_environment, name, field, value[field])


def test_isolation_audit_rejects_a_goal_change(pairs: list[PairSpec]) -> None:
    pair = pairs[0]
    tampered = pair.intervention_environment.model_copy(deep=True)
    tampered.goal = pair.clean_environment.goal + " And also summarise everything."
    report = isolation_audit(pair.clean_environment, tampered, pair.intervention_patch)
    assert not report["passed"]
    assert not report["checks"]["goal_text_identical"]


def test_isolation_audit_rejects_unrelated_evidence_changes(pairs: list[PairSpec]) -> None:
    pair = next(p for p in pairs if p.intervention_operator == "remove_tool")
    tampered = pair.intervention_environment.model_copy(deep=True)
    _, value = next(
        (n, v) for n, v in tampered.sources.items() if isinstance(v, list) and v
    )
    value[0][sorted(value[0])[0]] = "mutated"
    report = isolation_audit(pair.clean_environment, tampered, pair.intervention_patch)
    assert not report["passed"]


def test_operator_refuses_to_remove_or_fail_an_absent_tool(pairs: list[PairSpec]) -> None:
    state = pairs[0].clean_environment
    with pytest.raises(OperatorError):
        remove_tool(state, "no_such_tool")
    with pytest.raises(OperatorError):
        inject_tool_failure(state, "no_such_tool", "timeout")


# ---------------------------------------------------------------------------
# evidence and tool contracts
# ---------------------------------------------------------------------------


def test_evidence_is_primitive_only(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        report = primitive_evidence_report(
            pair.clean_environment.sources,
            gold=pair.clean_gold_private,
            manifest=pair.primitive_evidence_manifest,
        )
        assert report["passed"], (pair.semantic_objective_id, report["checks"])


def test_answer_bearing_fields_are_detected() -> None:
    assert scan_answer_bearing({"records": [{"final_answer": 1}]})
    assert scan_answer_bearing({"best_option": "x"})
    assert scan_answer_bearing({"selected_vendor": "x"})
    assert not scan_answer_bearing({"nightly_rate": 10, "refundable": True})


def test_no_undeclared_universal_oracle(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        objective = OBJECTIVES[pair.semantic_objective_id]
        for state in (pair.clean_environment, pair.intervention_environment):
            report = audit_tool_contracts(state, objective)
            assert report["passed"], report["findings"]
            assert all(row.tool_id != "read_file" for row in state.tools)


def test_recovery_only_tools_are_invisible_without_authorization(pairs: list[PairSpec]) -> None:
    pair = next(p for p in pairs if p.route_requirement_intervention == "recovery")
    runtime = ToolRuntime(pair.intervention_environment)
    hidden = [
        row for row in pair.intervention_environment.tools if row.authorization_scope == "recovery_only"
    ]
    assert hidden
    assert all(row not in runtime.visible_tools() for row in hidden)
    with pytest.raises(ToolExecutionError):
        runtime.execute(hidden[0], {})


def test_tool_rejects_undeclared_arguments(pairs: list[PairSpec]) -> None:
    pair = pairs[0]
    runtime = ToolRuntime(pair.clean_environment)
    contract = pair.clean_environment.tools[0]
    with pytest.raises(ToolExecutionError):
        runtime.execute(contract, {"unauthorized_scope": "all"})


# ---------------------------------------------------------------------------
# routes
# ---------------------------------------------------------------------------


def test_clean_route_completes_for_every_pair(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        proof = validate_clean_route(pair)
        assert proof.passed, (pair.semantic_objective_id, proof.checks)
        assert proof.derived_answer == pair.clean_gold_private
        assert not proof.hidden_gold_visible_during_derivation
        assert not proof.undeclared_oracle_used


def test_intervention_route_is_proved_for_every_pair(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        proof = validate_intervention_route(pair)
        assert proof.passed, (pair.semantic_objective_id, proof.route_kind, proof.checks)
        assert proof.route_kind == pair.route_requirement_intervention
        assert proof.route_inventory


def test_recovery_is_temporally_and_causally_bound(pairs: list[PairSpec]) -> None:
    recoveries = [p for p in pairs if p.route_requirement_intervention == "recovery"]
    assert len(recoveries) == 5
    for pair in recoveries:
        proof = validate_intervention_route(pair)
        assert proof.recovery is not None
        assert proof.recovery.attempt_step_index > proof.recovery.failure_step_index
        assert proof.recovery.supplied_input_keys
        assert proof.checks["recovery_credit_not_inherited"]
        assert proof.checks["fallback_is_declared_recovery_only_in_this_pair"]


def test_abstention_requires_genuine_route_exhaustion(pairs: list[PairSpec]) -> None:
    abstentions = [p for p in pairs if p.route_requirement_intervention == "abstention"]
    assert len(abstentions) == 3
    for pair in abstentions:
        proof = validate_intervention_route(pair)
        assert proof.checks["every_declared_route_enumerated"]
        assert proof.checks["reasoning_closure_insufficient"]
        assert proof.checks["no_authorized_recovery_route"]
        assert proof.checks["no_targeted_clarification_available"]
        assert pair.abstention_opportunity_private is not None


def test_abstention_is_refused_when_the_task_is_still_solvable(pairs: list[PairSpec]) -> None:
    pair = next(p for p in pairs if p.route_requirement_intervention == "abstention")
    restored = PairSpec.model_validate(pair.model_dump(mode="json"))
    restored.intervention_environment = pair.clean_environment
    assert not validate_intervention_route(restored).passed


def test_clarification_requires_a_counterparty_resolvable_field(pairs: list[PairSpec]) -> None:
    clarifications = [p for p in pairs if p.route_requirement_intervention == "clarification"]
    assert len(clarifications) == 5
    for pair in clarifications:
        requirement = pair.clarification_requirement_private
        assert requirement is not None
        target = requirement["missing_input_key"]
        assert target in pair.counterparty_resolvable_inputs
        assert target in requirement["required_question_reference"]


def test_generic_clarification_is_rejected(pairs: list[PairSpec]) -> None:
    pair = next(p for p in pairs if p.route_requirement_intervention == "clarification")
    tampered = PairSpec.model_validate(pair.model_dump(mode="json"))
    tampered.clarification_requirement_private = {
        **(pair.clarification_requirement_private or {}),
        "required_question_reference": "Please clarify.",
    }
    assert not validate_intervention_route(tampered).passed


def test_manual_reasoning_closure_is_credited(pairs: list[PairSpec]) -> None:
    """Removing a tool whose inputs remain available must not force abstention."""

    completions = [
        p
        for p in pairs
        if p.intervention_family == "tool_removal" and p.route_requirement_intervention == "completion"
    ]
    assert completions
    for pair in completions:
        objective = OBJECTIVES[pair.semantic_objective_id]
        result = execute_available_route(pair.intervention_environment, objective)
        assert not result.missing_inputs(objective.required_input_keys)


def test_hostile_route_audit_rejects_every_attack(pairs: list[PairSpec]) -> None:
    report = hostile_route_audit(pairs)
    assert report["passed"], report["surviving_attacks"]
    assert report["attack_count"] >= 200
    assert not report["surviving_attacks"]


# ---------------------------------------------------------------------------
# reviewer packages
# ---------------------------------------------------------------------------


def test_stage1_item_hides_every_private_field(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        item = stage1_item(pair, "RA-01")
        blob = json.dumps(item)
        assert pair.clean_gold_private not in blob
        assert pair.intervention_gold_or_policy_private not in blob
        assert pair.pair_id not in blob
        assert pair.route_requirement_intervention not in blob
        assert "authorization_scope" not in blob
        assert "recovery_only" not in blob


def test_stage1_review_form_covers_every_required_dimension() -> None:
    names = {name for name, _, _ in REVIEW_DIMENSIONS}
    required = {
        "task_clarity",
        "clean_goal_clear",
        "clean_evidence_sufficient",
        "clean_solvable",
        "intervention_understandable",
        "intended_factor_identifiable",
        "goal_preserved",
        "single_factor_isolation",
        "preserved_invariants_hold",
        "primitive_evidence_adequate",
        "declared_tools_adequate",
        "intervention_realistic",
        "ambiguity_present",
        "response_space_structurally_valid",
        "exclude_item",
        "reviewer_confidence",
        "notes",
    }
    assert names == required
    assert REVIEW_FORM_COLUMNS[0] == "reviewer_item_id"


def test_reviewer_packages_are_independently_ordered(pairs: list[PairSpec]) -> None:
    payload_a, mapping_a, items_a = build_stage1_package(pairs, SEED, "stage1_reviewer_a")
    payload_b, mapping_b, items_b = build_stage1_package(pairs, SEED, "stage1_reviewer_b")
    assert payload_a != payload_b
    assert [row["reviewer_item_id"] for row in items_a] != [
        mapping_b[row["reviewer_item_id"]] for row in items_b
    ]
    assert list(mapping_a.values()) != list(mapping_b.values())
    assert len(set(mapping_a)) == len(set(mapping_b)) == 20


def test_reviewer_packages_are_byte_stable(pairs: list[PairSpec]) -> None:
    first, _, _ = build_stage1_package(pairs, SEED, "stage1_reviewer_a")
    second, _, _ = build_stage1_package(pairs, SEED, "stage1_reviewer_a")
    assert first == second


def test_stage1_form_has_exactly_one_row_per_item(pairs: list[PairSpec]) -> None:
    payload, mapping, _ = build_stage1_package(pairs, SEED, "stage1_reviewer_a")
    files = _extract(payload)
    rows = files["review_form.csv"].decode().strip().splitlines()
    assert rows[0] == ",".join(REVIEW_FORM_COLUMNS)
    assert len(rows) - 1 == len(mapping) == 20
    assert [line.split(",")[0] for line in rows[1:]] == sorted(mapping)


def test_stage1_leakage_audit_passes(pairs: list[PairSpec]) -> None:
    packages, mappings = {}, {}
    for role in ("stage1_reviewer_a", "stage1_reviewer_b"):
        payload, mapping, _ = build_stage1_package(pairs, SEED, role)
        packages[role] = payload
        mappings[role] = mapping
    for role in (REVIEWER_A, REVIEWER_B):
        packages[f"qualification_{role.casefold()}"] = build_private_qualification(SEED, role)[
            "package_bytes"
        ]
    report = stage1_leakage_audit(packages, pairs, mappings)
    assert report["passed"], [row["checks"] for row in report["packages"]]
    assert report["leaked_values_are_never_printed"]


def test_leakage_audit_catches_a_planted_gold_value(pairs: list[PairSpec]) -> None:
    payload, mapping, _ = build_stage1_package(pairs, SEED, "stage1_reviewer_a")
    files = _extract(payload)
    victim = next(iter(mapping))
    pair = next(p for p in pairs if p.pair_id == mapping[victim])
    files[f"items/{victim}.json"] = json.dumps(
        {"reviewer_item_id": victim, "leak": pair.clean_gold_private}
    ).encode()
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, blob in sorted(files.items()):
            archive.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), blob)
    report = stage1_leakage_audit({"tampered": stream.getvalue()}, pairs, {"tampered": mapping})
    assert not report["passed"]


def test_packages_are_path_safe_and_ship_no_source(pairs: list[PairSpec]) -> None:
    packages = {
        role: build_stage1_package(pairs, SEED, role)[0]
        for role in ("stage1_reviewer_a", "stage1_reviewer_b")
    }
    for role in (REVIEWER_A, REVIEWER_B):
        packages[f"qualification_{role.casefold()}"] = build_private_qualification(SEED, role)[
            "package_bytes"
        ]
    report = usability_audit(packages)
    assert report["passed"], [row["checks"] for row in report["packages"]]
    assert report["reviewer_orders_independent"]
    for payload in packages.values():
        for name in _extract(payload):
            assert not name.startswith("/")
            assert ".." not in name.split("/")
            assert not name.endswith((".py", ".pyc", ".so"))


# ---------------------------------------------------------------------------
# qualification
# ---------------------------------------------------------------------------


def test_qualification_is_separate_from_the_review_set(pairs: list[PairSpec]) -> None:
    package = build_private_qualification(SEED, REVIEWER_A)
    blob = json.dumps(
        [json.loads(body) for name, body in _extract(package["package_bytes"]).items()
         if name.startswith("items/")]
    )
    for pair in pairs:
        assert pair.clean_gold_private not in blob
        assert pair.shared_goal not in blob


def test_qualification_threshold_is_enforced() -> None:
    package = build_private_qualification(SEED, REVIEWER_A)
    key = package["answer_key"]
    perfect = {
        item_id: {str(entry["decisive_dimension"]): str(entry["expected_value"])}
        for item_id, entry in key.items()
    }
    assert score_qualification(perfect, key, reviewer_role=REVIEWER_A)["qualified"]
    wrong = {
        item_id: {
            str(entry["decisive_dimension"]): "no"
            if str(entry["expected_value"]) == "yes"
            else "yes"
        }
        for item_id, entry in key.items()
    }
    result = score_qualification(wrong, key, reviewer_role=REVIEWER_A)
    assert not result["qualified"]
    assert result["threshold"] == 0.80


def test_qualification_package_ships_no_key() -> None:
    files = _extract(build_private_qualification(SEED, REVIEWER_B)["package_bytes"])
    blob = b"".join(files.values()).lower()
    assert b"decisive_dimension" not in blob
    assert b"expected_value" not in blob
    assert not any("key" in name.casefold() for name in files)


# ---------------------------------------------------------------------------
# security
# ---------------------------------------------------------------------------


def test_vault_fails_closed_without_the_key_environment_variable(monkeypatch) -> None:
    monkeypatch.delenv(KEY_ENV, raising=False)
    with pytest.raises(VaultError):
        resolve_key_path(REPO_ROOT)


def test_vault_refuses_a_key_inside_the_repository(monkeypatch, tmp_path: Path) -> None:
    inside = REPO_ROOT / "private_data" / "not_allowed.key"
    monkeypatch.setenv(KEY_ENV, str(inside))
    with pytest.raises(VaultError):
        resolve_key_path(REPO_ROOT)


def test_vault_creates_an_owner_only_external_key(monkeypatch, tmp_path: Path) -> None:
    key_path = tmp_path / "keys" / "stage2.key"
    monkeypatch.setenv(KEY_ENV, str(key_path))
    resolved, key = load_or_create_key(REPO_ROOT)
    assert resolved == key_path
    assert len(key) == 32
    assert oct(key_path.stat().st_mode)[-3:] == "600"


def test_vault_roundtrip_and_wrong_key_rejection() -> None:
    key = hashlib.sha256(b"key-a").digest()
    other = hashlib.sha256(b"key-b").digest()
    sealed = seal([{"pair_id": "x", "clean_gold": "secret"}], key)
    assert b"secret" not in sealed
    assert unseal(sealed, key)[0]["clean_gold"] == "secret"
    with pytest.raises(VaultError):
        unseal(sealed, other)


def test_vault_refuses_plaintext_beside_the_ciphertext(tmp_path: Path) -> None:
    key = hashlib.sha256(b"key-c").digest()
    vault = tmp_path / "stage2" / "stage2_vault.enc"
    vault.parent.mkdir(parents=True)
    (vault.parent / "stage2_private.jsonl").write_text("{}\n")
    with pytest.raises(VaultError):
        write_vault(vault, [{"pair_id": "x"}], key)


def test_private_data_is_git_ignored() -> None:
    assert "private_data/" in (REPO_ROOT / ".gitignore").read_text()


# ---------------------------------------------------------------------------
# retired packets
# ---------------------------------------------------------------------------


def test_retired_packet_registry_covers_every_prior_packet() -> None:
    registry = retired_packet_registry()
    assert registry["retired_packet_count"] == len(RETIRED_PACKETS) >= 5
    assert registry["active_packet_version"] == PACKET_VERSION
    for entry in registry["retired_packets"]:
        assert entry["status"].startswith("EXPOSED_OR_INVALID_DEVELOPMENT_FIXTURE")
        assert entry["eligible_for_genuine_review"] is False
        assert entry["eligible_for_c10"] is False
        assert entry["eligible_for_model_execution"] is False
        assert entry["eligible_for_paper_claims"] is False
        assert entry["replacement_version"] == PACKET_VERSION


@pytest.mark.parametrize(
    "gate", ["stage1_ingestion", "c10_evaluation", "slice_lock", "model_execution_authorization"]
)
def test_retired_packets_are_rejected_at_every_gate(gate: str) -> None:
    for entry in RETIRED_PACKETS:
        with pytest.raises(RetiredPacketError):
            enforce_active_packet(packet_version=str(entry["packet_version"]), action=gate)


def test_renamed_retired_packet_is_still_rejected() -> None:
    with pytest.raises(RetiredPacketError):
        enforce_active_packet(
            packet_version=PACKET_VERSION,
            commitment="f4767f10ef0c5edadb2a22a5445450fba5583a99eee8aff709a0537c86e6e66f",
            action="renamed_copy",
        )


def test_retirement_enforcement_report_passes() -> None:
    report = retirement_enforcement_report()
    assert report["passed"], report["checks"]
    assert report["checks"]["renamed_copy_with_retired_commitment_rejected"]


# ---------------------------------------------------------------------------
# workflow
# ---------------------------------------------------------------------------


def test_fixture_end_to_end_workflow_passes() -> None:
    report = run_fixture_e2e()
    assert report["passed"], [row for row in report["steps"] if not row["passed"]]
    assert report["evidence_class"] == FIXTURE_MARKER
    assert report["counts_as_genuine_evidence"] is False
    assert report["genuine_human_judgments"] == 0
    assert report["genuine_model_trajectories"] == 0


def test_production_workspace_refuses_fixture_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from causal_agent_bench.review_ready_v2.keys import create_external_key
    from causal_agent_bench.review_ready_v2.receipts import COORDINATOR_KEY_ENV

    monkeypatch.setenv(COORDINATOR_KEY_ENV, str(tmp_path / "keys" / "coordinator.key"))
    create_external_key(COORDINATOR_KEY_ENV, tmp_path / "repo")

    fixture = ReviewWorkspace.fixture(tmp_path / "packet")
    fixture.write("stage1_commitment", {"receipt_kind": "stage1_commitment"})
    production = ReviewWorkspace.production(tmp_path / "packet", tmp_path / "repo")
    production.receipts.mkdir(parents=True, exist_ok=True)
    (production.receipts / "stage1_commitment.json").write_bytes(
        (fixture.receipts / "stage1_commitment.json").read_bytes()
    )
    with pytest.raises(WorkflowError):
        production.read("stage1_commitment")


def test_stage2_unlock_requires_a_stage1_commitment(tmp_path: Path) -> None:
    workspace = ReviewWorkspace.fixture(tmp_path / "packet")
    with pytest.raises(WorkflowError):
        workspace.unlock_stage2(
            packet_commitment="a" * 64,
            scientific_freeze_sha256="b" * 64,
            exact_commit="c" * 40,
            key_available=True,
        )


def test_stage1_ingestion_requires_qualification(tmp_path: Path) -> None:
    workspace = ReviewWorkspace.fixture(tmp_path / "packet")
    with pytest.raises(WorkflowError):
        workspace.ingest_stage1(
            REVIEWER_A, b"", expected_item_ids=["X-01"], package_sha256="0" * 64
        )


def test_malformed_submission_is_rejected() -> None:
    rows = {"RA-01": dict.fromkeys(REVIEW_FORM_COLUMNS, "")}
    report = validate_stage1_submission(rows, ["RA-01"])
    assert not report["passed"]
    assert report["malformed"]


def test_gating_dimensions_are_a_subset_of_the_form() -> None:
    names = {name for name, _, _ in REVIEW_DIMENSIONS}
    assert set(GATING_DIMENSIONS) <= names


# ---------------------------------------------------------------------------
# generation is fail-closed
# ---------------------------------------------------------------------------


def test_generation_refuses_a_short_seed() -> None:
    with pytest.raises(PairGenerationError):
        build_all_pairs(b"too-short")


def test_generation_is_deterministic_for_a_fixed_seed() -> None:
    first = build_all_pairs(SEED)
    second = build_all_pairs(SEED)
    assert [p.model_dump(mode="json") for p in first] == [p.model_dump(mode="json") for p in second]


def test_full_design_audit_passes(pairs: list[PairSpec]) -> None:
    report = design_audit(pairs)
    assert report["passed"], report
    assert report["status"] == "CAB_SEMANTIC_DIVERSITY_VALIDATED"


def test_pair_secrets_do_not_include_shared_vocabulary(pairs: list[PairSpec]) -> None:
    for pair in pairs:
        strong, _ = pair_secrets(pair)
        tool_ids = {row.tool_id for row in pair.declared_tool_contracts}
        assert strong.isdisjoint(tool_ids)
        assert strong.isdisjoint(set(pair.required_input_keys))


def test_structural_diff_enumerates_leaf_changes() -> None:
    diff = structural_diff({"a": 1, "b": {"c": 2}}, {"a": 1, "b": {"c": 3}, "d": 4})
    assert {row["locator"] for row in diff} == {"$.b.c", "$.d"}
