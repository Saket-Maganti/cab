from __future__ import annotations

import json

import pytest

from causal_agent_bench.level5.core import content_hash
from causal_agent_bench.level5.evaluator import (
    DockerSandboxRuntime,
    MockSandboxRuntime,
    ProtectedTaskBroker,
    SandboxSpec,
    SubmissionManifest,
    audit_output,
    evaluate_fixture_submission,
    validate_archive_members,
    verify_receipt,
)
from causal_agent_bench.level5.reliability import (
    EventLog,
    FaultKind,
    diagnostic_summary,
    run_fixture_chaos_campaign,
)
from causal_agent_bench.level5.review import (
    Adjudication,
    Judgment,
    Reviewer,
    ReviewerRole,
    ReviewStore,
    agreement_report,
    assign_reviews,
    evaluate_c10,
)
from causal_agent_bench.level5.review_server import ReviewLedger


def _reviewer(reviewer_id: str, role: ReviewerRole = ReviewerRole.REVIEWER) -> Reviewer:
    return Reviewer(
        reviewer_id=reviewer_id,
        role=role,
        qualified=True,
        consented=True,
        human_attestation=True,
        compensation_disclosed=True,
    )


def _judgment(
    judgment_id: str,
    reviewer_id: str,
    *,
    valid: bool = True,
    scope: str = "GENUINE_HUMAN",
) -> Judgment:
    return Judgment(
        judgment_id=judgment_id,
        assignment_id=f"assignment.{judgment_id}",
        item_id="item.1",
        reviewer_id=reviewer_id,
        valid=valid,
        manipulation_passed=True,
        invariant=True,
        solvable=True,
        confidence=0.9,
        time_seconds=20,
        submitted_at="2026-01-01T00:00:00Z",
        evidence_scope=scope,
    )


def test_event_log_is_monotonic_and_redacts_private_fields(tmp_path):
    log = EventLog(tmp_path / "events.jsonl")
    log.emit(
        "scheduler",
        "START",
        correlation_id="corr.1",
        fields={"secret_token": "not-public", "safe": "yes"},
    )
    log.emit("artifact_store", "COMPLETE", correlation_id="corr.1")
    events = log.read()
    assert [event["sequence"] for event in events] == [1, 2]
    assert events[0]["fields"]["secret_token"] == "[REDACTED]"
    assert diagnostic_summary(events)["sequence_monotonic"] is True


def test_all_fixture_faults_have_recovery_receipts():
    report = run_fixture_chaos_campaign()
    assert report["passed"] is True
    assert report["case_count"] == len(FaultKind)
    assert report["real_execution_slos_measured"] is False
    assert all(case["evidence_class"] == "FIXTURE_ONLY" for case in report["cases"])


def test_assignment_is_balanced_independent_and_conflict_aware():
    reviewers = [_reviewer("reviewer.a"), _reviewer("reviewer.b"), _reviewer("reviewer.c")]
    assignments = assign_reviews(["item.1", "item.2", "item.3"], reviewers)
    assert len(assignments) == 6
    by_item = {
        item: {row.reviewer_id for row in assignments if row.item_id == item}
        for item in {"item.1", "item.2", "item.3"}
    }
    assert all(len(values) == 2 for values in by_item.values())


def test_review_attestation_rejects_proxy_ai_and_missing_consent():
    with pytest.raises(ValueError, match="human attestation"):
        Reviewer(
            reviewer_id="reviewer.ai",
            role=ReviewerRole.REVIEWER,
            qualified=True,
            consented=True,
            human_attestation=True,
            proxy_or_ai_assistance=True,
        )
    with pytest.raises(ValueError, match="consent"):
        Reviewer(
            reviewer_id="reviewer.no_consent",
            role=ReviewerRole.REVIEWER,
            qualified=True,
            consented=False,
            human_attestation=True,
        )


def test_submitted_judgment_is_immutable_and_amendment_is_logged():
    store = ReviewStore()
    original = _judgment("judgment.original", "reviewer.a")
    store.submit(original)
    with pytest.raises(ValueError, match="immutable"):
        store.submit(original.model_copy(update={"valid": False}))
    replacement = _judgment("judgment.replacement", "reviewer.a").model_copy(
        update={"supersedes": original.judgment_id}
    )
    store.amend(original.judgment_id, replacement, reason="clerical correction")
    assert store.judgments == [replacement]
    assert store.amendments[0]["original_id"] == original.judgment_id


def test_review_server_ledger_persists_and_separates_fixture_counts(tmp_path):
    ledger = ReviewLedger(tmp_path / "review")
    ledger.submit(_judgment("judgment.fixture", "reviewer.a", scope="FIXTURE_ONLY"))
    status = ReviewLedger(tmp_path / "review").status()
    assert status["judgment_count"] == 1
    assert status["fixture_count"] == 1
    assert status["genuine_count"] == 0
    with pytest.raises(ValueError, match="immutable"):
        ledger.submit(_judgment("judgment.fixture", "reviewer.a", scope="FIXTURE_ONLY"))


def test_c10_rejects_fixtures_and_incomplete_coverage():
    fixture = _judgment("judgment.fixture", "reviewer.a", scope="FIXTURE_ONLY")
    report = evaluate_c10(["item.1"], [fixture], [])
    assert report["passed"] is False
    assert report["state"] == "HUMAN_VALIDATION_REQUIRED"
    assert "fixture or non-genuine judgment present" in report["blockers"]


def test_c10_accepts_complete_genuine_agreement_only():
    judgments = [
        _judgment("judgment.a", "reviewer.a"),
        _judgment("judgment.b", "reviewer.b"),
    ]
    report = evaluate_c10(["item.1"], judgments, [])
    assert report["passed"] is True
    assert report["certificate_hash"]
    agreement = agreement_report(judgments)
    assert agreement["raw_agreement"] == 1.0


def test_c10_requires_adjudication_for_disagreement():
    judgments = [
        _judgment("judgment.a", "reviewer.a", valid=True),
        _judgment("judgment.b", "reviewer.b", valid=False),
    ]
    assert evaluate_c10(["item.1"], judgments, [])["passed"] is False
    adjudication = Adjudication(
        adjudication_id="adjudication.1",
        item_id="item.1",
        adjudicator_id="reviewer.c",
        decision=True,
        rationale="Reviewed the invariance contract.",
        submitted_at="2026-01-01T00:00:00Z",
        evidence_scope="GENUINE_HUMAN",
    )
    assert evaluate_c10(["item.1"], judgments, [adjudication])["passed"] is True


def _submission() -> SubmissionManifest:
    return SubmissionManifest(
        submission_id="submission.fixture",
        package_hash=content_hash("package"),
        model_declaration="fixture",
        policy_declaration="fixture",
        runtime_image="fixture:local",
        entry_point=["python", "agent.py"],
        licence="MIT",
        authorship_attestation=True,
    )


def test_submission_contract_denies_network_and_unsafe_archives():
    with pytest.raises(ValueError, match="denies network"):
        _submission().model_copy(update={"network_requested": True}).model_validate(
            _submission().model_dump() | {"network_requested": True}
        )
    with pytest.raises(ValueError, match="unsafe archive"):
        validate_archive_members(["../../escape"])
    validate_archive_members(["agent/package.py"])


def test_docker_sandbox_command_is_hardened(tmp_path):
    private_task = tmp_path / "task.json"
    private_task.write_text('{"fixture": true}', encoding="utf-8")
    submission = _submission()
    command = DockerSandboxRuntime().build_command(
        submission,
        SandboxSpec(resources=submission.resources),
        private_task_path=private_task,
    )
    joined = " ".join(command)
    assert "--network none" in joined
    assert "--read-only" in joined
    assert "--cap-drop ALL" in joined
    assert "no-new-privileges" in joined
    assert "readonly" in joined


@pytest.mark.parametrize(
    "output",
    [
        "BEGIN_PRIVATE_TASK dump",
        "cat /etc/passwd",
        "query_score_oracle",
        "base64 private_payload",
        "hardcoded task_id == abc",
    ],
)
def test_anti_exfiltration_detects_malicious_outputs(output):
    report = audit_output(output, output_limit=1024)
    assert report["passed"] is False
    assert report["findings"]


def test_fixture_receipt_signature_detects_tampering():
    receipt = evaluate_fixture_submission(
        _submission(),
        MockSandboxRuntime(),
        task_set_hash=content_hash(["task"]),
    )
    assert verify_receipt(receipt) is True
    receipt["audit_status"] = "TAMPERED"
    assert verify_receipt(receipt) is False


def test_protected_task_broker_requires_trusted_boundary():
    broker = ProtectedTaskBroker({"opaque.1": "private fixture payload"})
    with pytest.raises(PermissionError):
        broker.resolve("opaque.1", trusted=False)
    assert broker.resolve("opaque.1", trusted=True) == "private fixture payload"
    assert "private fixture payload" not in json.dumps(broker.public_manifest())
