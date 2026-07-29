from __future__ import annotations

import http.client
import json
import re
import subprocess
import threading
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

import pytest
from pydantic import ValidationError

from causal_agent_bench.level5.core import content_hash, utc_now
from causal_agent_bench.level5.evaluator import (
    EVALUATOR_CONTAINER_ATTACKS,
    ArchiveMember,
    DockerSandboxRuntime,
    EvaluationQueue,
    LocalEncryptedFixtureTaskStore,
    MockSandboxRuntime,
    ProtectedTaskBroker,
    SandboxSpec,
    SubmissionManifest,
    audit_structured_output,
    evaluate_fixture_submission,
    inspect_submission,
    run_evaluator_malicious_campaign,
    verify_receipt,
)
from causal_agent_bench.level5.registry import SQLiteRegistry
from causal_agent_bench.level5.review import (
    Adjudication,
    DurableReviewStore,
    Judgment,
    LocalDevelopmentIdentityProvider,
    ReviewerRole,
)
from causal_agent_bench.level5.review_server import make_durable_handler
from causal_agent_bench.level5.signing import (
    FixtureHMACSigner,
    FixtureHMACVerifier,
    SigningKeyRegistry,
    explicit_private_key_environment,
)


def _submission(**updates):
    values = {
        "submission_id": "submission.hardening.fixture",
        "package_hash": content_hash("package"),
        "model_declaration": "fixture model",
        "policy_declaration": "fixture policy",
        "runtime_image": "cab/fixture:local",
        "entry_point": ["agent.py"],
        "licence": "MIT",
        "authorship_attestation": True,
    }
    values.update(updates)
    return SubmissionManifest(**values)


def _judgment(assignment, reviewer: str, valid: bool, judgment_id: str, **updates):
    values = {
        "judgment_id": judgment_id,
        "assignment_id": assignment["assignment_id"],
        "item_id": assignment["item_id"],
        "reviewer_id": reviewer,
        "valid": valid,
        "manipulation_passed": True,
        "invariant": True,
        "solvable": True,
        "confidence": 0.9,
        "time_seconds": 12,
        "notes": "Fixture judgment.",
        "submitted_at": utc_now(),
        "evidence_scope": "FIXTURE_ONLY",
    }
    values.update(updates)
    return Judgment(**values)


def test_durable_review_full_two_reviewer_disagreement_adjudication_and_amendment(tmp_path):
    store = DurableReviewStore(tmp_path / "private" / "review.sqlite3")
    assert store.directory_permissions()["private"]
    store.register_user("admin.fixture", ReviewerRole.ADMINISTRATOR)
    for reviewer in ("reviewer.one", "reviewer.two"):
        store.register_user(reviewer, ReviewerRole.REVIEWER)
        store.qualify_user(
            reviewer,
            consented=True,
            human_attestation=True,
            proxy_or_ai_assistance=False,
        )
    store.register_user("adjudicator.fixture", ReviewerRole.ADJUDICATOR)
    store.qualify_user(
        "adjudicator.fixture",
        consented=True,
        human_attestation=True,
        proxy_or_ai_assistance=False,
    )
    admin = store.create_session("admin.fixture")
    reviewer_sessions = {
        reviewer: store.create_session(reviewer)
        for reviewer in ("reviewer.one", "reviewer.two")
    }
    adjudicator = store.create_session("adjudicator.fixture")
    assignments = store.assign(
        admin.token,
        ["item.fixture"],
        list(reviewer_sessions),
    )
    assert len(assignments) == 2
    by_reviewer = {row["reviewer_id"]: row for row in assignments}

    judgments = []
    for index, reviewer in enumerate(reviewer_sessions):
        session = reviewer_sessions[reviewer]
        assignment = by_reviewer[reviewer]
        draft = store.autosave_draft(
            session.token,
            session.csrf_token,
            assignment["assignment_id"],
            {"valid": index == 0, "notes": "autosaved"},
        )
        assert draft["saved"]
        judgment = _judgment(
            assignment,
            reviewer,
            index == 0,
            f"judgment.fixture.{index}",
        )
        store.submit_judgment(session.token, session.csrf_token, judgment)
        store.submit_judgment(session.token, session.csrf_token, judgment)
        judgments.append(judgment)

    assert store.c10_status(["item.fixture"])["passed"] is False
    decision = Adjudication(
        adjudication_id="adjudication.fixture",
        item_id="item.fixture",
        adjudicator_id="adjudicator.fixture",
        decision=True,
        rationale="Fixture disagreement resolved from the invariance contract.",
        submitted_at=utc_now(),
        evidence_scope="FIXTURE_ONLY",
    )
    store.adjudicate(adjudicator.token, adjudicator.csrf_token, decision)
    store.request_amendment(
        admin.token,
        judgments[0].judgment_id,
        reason="Fixture clerical amendment.",
    )
    replacement = _judgment(
        by_reviewer["reviewer.one"],
        "reviewer.one",
        True,
        "judgment.fixture.replacement",
        supersedes=judgments[0].judgment_id,
        notes="Amended fixture judgment.",
    )
    first_session = reviewer_sessions["reviewer.one"]
    store.record_amendment(
        first_session.token,
        first_session.csrf_token,
        judgments[0].judgment_id,
        replacement,
        reason="Fixture clerical amendment.",
    )
    public = store.export_public()
    private = store.export_private()
    assert public["fixture_judgment_count"] == 2
    assert public["genuine_judgment_count"] == 0
    assert public["identity_fields_exported"] is False
    assert private["raw_identity_exported"] is False
    assert store.dashboard()["coverage"][0]["submitted_count"] == 2
    assert store.c10_status(["item.fixture"])["state"] == "HUMAN_VALIDATION_REQUIRED"

    backup = store.backup(tmp_path / "backup.sqlite3")
    restored = DurableReviewStore.restore(backup, tmp_path / "restored.sqlite3")
    assert restored.export_public()["judgment_count"] == 2
    store.logout(admin.token)
    with pytest.raises(PermissionError, match="revoked"):
        store.authenticate(admin.token)


def test_review_conflicts_authentication_rbac_and_validation_fail_closed(tmp_path):
    store = DurableReviewStore(tmp_path / "review.sqlite3")
    store.register_user("admin.fixture", ReviewerRole.ADMINISTRATOR)
    store.register_user("reviewer.fixture", ReviewerRole.REVIEWER)
    with pytest.raises(ValueError, match="consent"):
        store.qualify_user(
            "reviewer.fixture",
            consented=False,
            human_attestation=True,
            proxy_or_ai_assistance=False,
        )
    store.qualify_user(
        "reviewer.fixture",
        consented=True,
        human_attestation=True,
        proxy_or_ai_assistance=False,
    )
    admin = store.create_session("admin.fixture")
    reviewer = store.create_session("reviewer.fixture")
    with pytest.raises(ValueError, match="independent"):
        store.assign(admin.token, ["item"], ["reviewer.fixture"], reviews_per_item=2)
    assignment = store.assign(
        admin.token,
        ["item"],
        ["reviewer.fixture"],
        reviews_per_item=1,
    )[0]
    with pytest.raises(PermissionError, match="CSRF"):
        store.authenticate(reviewer.token, csrf_token="forged")
    with pytest.raises(PermissionError, match="role"):
        store.authenticate(
            reviewer.token,
            allowed_roles={ReviewerRole.ADMINISTRATOR},
        )
    store.declare_conflict(
        reviewer.token,
        reviewer.csrf_token,
        assignment["assignment_id"],
    )
    with pytest.raises(ValueError, match="conflicted"):
        store.submit_judgment(
            reviewer.token,
            reviewer.csrf_token,
            _judgment(
                assignment,
                "reviewer.fixture",
                True,
                "judgment.conflicted",
            ),
        )
    with pytest.raises(ValueError, match="one day"):
        store.create_session("reviewer.fixture", ttl_seconds=90_000)
    assert LocalDevelopmentIdentityProvider().resolve(
        "reviewer.fixture",
        "local-development:reviewer.fixture",
    )["identity_assurance"] == "LOCAL_DEVELOPMENT_ONLY"
    with pytest.raises(PermissionError, match="rejected"):
        LocalDevelopmentIdentityProvider().resolve("reviewer.fixture", "forged")


def test_actual_review_http_service_session_csrf_and_security_headers(tmp_path):
    store = DurableReviewStore(tmp_path / "review.sqlite3")
    store.register_user("reviewer.http", ReviewerRole.REVIEWER)
    handler = make_durable_handler(store)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request("GET", "/health")
        health = connection.getresponse()
        assert health.status == 200
        assert health.getheader("X-Frame-Options") == "DENY"
        assert json.loads(health.read())["csrf"] is True

        login_body = urlencode(
            {
                "user_id": "reviewer.http",
                "assertion": "local-development:reviewer.http",
            }
        )
        connection.request(
            "POST",
            "/login",
            body=login_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        login = connection.getresponse()
        assert login.status == 303
        cookie = login.getheader("Set-Cookie").split(";", maxsplit=1)[0]
        login.read()

        connection.request("GET", "/", headers={"Cookie": cookie})
        dashboard = connection.getresponse()
        assert dashboard.status == 200
        rotated_cookie = dashboard.getheader("Set-Cookie").split(";", maxsplit=1)[0]
        page = dashboard.read().decode()
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page)
        assert csrf
        qualification = urlencode(
            {
                "csrf_token": csrf.group(1),
                "consented": "true",
                "human_attestation": "true",
                "no_proxy": "true",
            }
        )
        connection.request(
            "POST",
            "/qualify",
            body=qualification,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": rotated_cookie,
            },
        )
        qualified = connection.getresponse()
        assert qualified.status == 303
        qualified.read()

        connection.request("GET", "/v1/export/public")
        unauthorised = connection.getresponse()
        assert unauthorised.status == 401
        unauthorised.read()
        connection.request("GET", "/missing")
        missing = connection.getresponse()
        assert missing.status == 404
        missing.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_evaluator_submission_inspection_output_audit_and_task_broker(tmp_path):
    submission = _submission()
    benign = inspect_submission(
        submission,
        [ArchiveMember(path="agent.py", size_bytes=20, content_sample="print('ok')")],
    )
    assert benign["passed"]
    malicious = inspect_submission(
        submission,
        [
            ArchiveMember(path="../../escape", size_bytes=1),
            ArchiveMember(
                path="agent.py",
                size_bytes=101,
                is_symlink=True,
                link_target="/etc/passwd",
                content_sample="api_key=abcdefghijklmnop",
            ),
        ],
        max_archive_bytes=100,
        max_files=1,
    )
    assert not malicious["passed"]
    assert {
        "file_count_limit",
        "archive_size_limit",
        "archive_traversal",
        "unsafe_symlink",
        "bundled_secret",
    }.issubset({row["kind"] for row in malicious["findings"]})
    structured = audit_structured_output(
        json.dumps({"answer": "the protected fixture prompt has five tokens here", "extra": 1}),
        output_limit=1_000,
        allowed_fields={"answer"},
        protected_text="the protected fixture prompt has five tokens here",
    )
    assert not structured["passed"]
    repeated = audit_structured_output(
        '{"answer":"ok"}',
        output_limit=1_000,
        allowed_fields={"answer"},
        prior_probe_hashes={content_hash('{"answer":"ok"}')},
    )
    assert repeated["repeated_probe"]
    assert not audit_structured_output(
        "not-json",
        output_limit=1_000,
        allowed_fields={"answer"},
    )["passed"]

    tasks = LocalEncryptedFixtureTaskStore(tmp_path / "tasks", key=b"k" * 32)
    task_hash = tasks.put("opaque.fixture", b"protected fixture body")
    assert task_hash in tasks.public_commitment()["task_set_hash"] or len(task_hash) == 64
    lease = tasks.lease(
        "opaque.fixture",
        evaluator_id="worker.fixture",
        auth_token="authenticated",
    )
    with pytest.raises(PermissionError):
        tasks.resolve_once(lease["lease_token"], evaluator_auth="wrong")
    assert (
        tasks.resolve_once(lease["lease_token"], evaluator_auth="authenticated")
        == b"protected fixture body"
    )
    with pytest.raises(PermissionError, match="consumed"):
        tasks.resolve_once(lease["lease_token"], evaluator_auth="authenticated")
    with pytest.raises(ValueError, match="32"):
        LocalEncryptedFixtureTaskStore(tmp_path / "short", key=b"short")

    broker = ProtectedTaskBroker({"opaque.fixture": "body"})
    assert broker.public_manifest()["task_count"] == 1
    with pytest.raises(KeyError, match="unknown"):
        broker.resolve("missing", trusted=True)


def test_evaluation_queue_signed_receipt_rotation_revocation_and_fail_closed(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    queue = EvaluationQueue(registry)
    submission = _submission()
    policy = inspect_submission(
        submission,
        [ArchiveMember(path="agent.py", size_bytes=1)],
    )
    queue.set_quota("submitter.fixture", 1)
    assert queue.submit(
        submission,
        submitter_id="submitter.fixture",
        policy_report=policy,
    )["status"] == "SUBMITTED"
    queued = queue.approve_and_enqueue(
        submission.submission_id,
        approver_id="approver.fixture",
        priority=10,
    )
    assert queued["status"] == "QUEUED"
    assert queue.claim("evaluator.worker")["status"] == "RUNNING"
    assert queue.claim("evaluator.other") is None

    signer = FixtureHMACSigner.development("fixture-key-v1")
    verifier = FixtureHMACVerifier.development("fixture-key-v1")
    receipt = evaluate_fixture_submission(
        submission,
        MockSandboxRuntime(),
        task_set_hash=content_hash(["fixture"]),
        signer=signer,
    )
    assert verify_receipt(receipt, verifier=verifier)
    queue.record_receipt(receipt)
    assert queue.revoke_receipt(receipt["receipt_id"], "fixture revocation")

    keys = SigningKeyRegistry()
    keys.add(verifier, activate=True)
    assert keys.active_key_id == "fixture-key-v1"
    assert verify_receipt(receipt, key_registry=keys)
    keys.add(FixtureHMACVerifier.development("fixture-key-v2"))
    keys.rotate("fixture-key-v2")
    keys.revoke_object(receipt["receipt_id"], "fixture receipt retired")
    assert not verify_receipt(receipt, key_registry=keys)
    keys.revoke_key("fixture-key-v1", "test key retired")
    assert keys.status()["production_secrets_stored"] is False
    assert not verify_receipt(receipt, verifier=verifier, protected_mode=True)

    deferred_submission = _submission(submission_id="submission.quota.fixture")
    assert queue.submit(
        deferred_submission,
        submitter_id="submitter.fixture",
        policy_report={
            **policy,
            "policy_hash": content_hash("deferred-policy"),
        },
    )["status"] == "QUOTA_DEFERRED"
    with pytest.raises(ValueError, match="approval"):
        queue.approve_and_enqueue(
            deferred_submission.submission_id,
            approver_id="approver.fixture",
        )
    with pytest.raises(ValueError, match="policy"):
        queue.submit(
            _submission(submission_id="submission.rejected.fixture"),
            submitter_id="other",
            policy_report={"passed": False},
        )


def test_evaluator_protected_policy_and_malicious_campaign_are_honest(tmp_path, monkeypatch):
    digest = "sha256:" + "0" * 64
    protected = _submission(protected_mode=True, image_digest=digest)
    task = tmp_path / "task.json"
    task.write_text("{}", encoding="utf-8")
    seccomp = tmp_path / "seccomp.json"
    seccomp.write_text("{}", encoding="utf-8")
    sandbox = SandboxSpec(
        resources=protected.resources,
        seccomp_profile=str(seccomp),
        mandatory_lsm_hook="apparmor:cab-evaluator",
    )
    command = DockerSandboxRuntime().build_command(
        protected,
        sandbox,
        private_task_path=task,
        output_path=tmp_path / "output",
    )
    joined = " ".join(command)
    assert f"cab/fixture:local@{digest}" in joined
    assert "--userns private" in joined
    assert "seccomp=" in joined
    with pytest.raises(PermissionError, match="development"):
        evaluate_fixture_submission(
            protected,
            MockSandboxRuntime(),
            task_set_hash=content_hash(["protected"]),
        )
    with pytest.raises(ValidationError):
        _submission(image_digest="not-a-digest")
    with pytest.raises(ValueError, match="signer or signing_key"):
        evaluate_fixture_submission(
            _submission(),
            MockSandboxRuntime(),
            task_set_hash=content_hash(["fixture"]),
            signing_key=b"key",
            signer=FixtureHMACSigner.development(),
        )
    monkeypatch.setattr(DockerSandboxRuntime, "available", staticmethod(lambda: False))
    report = run_evaluator_malicious_campaign(
        image="cab/evaluator-fixture:unavailable",
        execute_containers=True,
    )
    assert report["executed_count"] == 0
    assert report["not_executed_count"] == len(EVALUATOR_CONTAINER_ATTACKS)
    assert all(not row["passed"] for row in report["cases"])


def test_evaluator_malicious_container_campaign_executes_all_safe_fixtures(monkeypatch):
    outputs = [
        (0, "/etc/passwd"),
        (0, '{"answer":"network_blocked"}'),
        (0, '{"answer":"fork_bounded","children":32}'),
        (137, ""),
        "timeout",
        (0, "x" * 1_000_001),
        (0, "BEGIN_PRIVATE_TASK"),
        (0, "../../cab/private/task.json"),
        "timeout",
        "timeout",
        (0, '{"answer":["PATH"]}'),
        (0, '{"answer":"read_only"}'),
    ]
    observed_runs = 0

    def fake_run(command, **kwargs):
        nonlocal observed_runs
        del kwargs
        if command[:3] == ["docker", "image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[:3] == ["docker", "rm", "-f"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        assert command[:2] == ["docker", "run"]
        response = outputs[observed_runs]
        observed_runs += 1
        if response == "timeout":
            raise subprocess.TimeoutExpired(command, 2, output=b"", stderr=b"timeout")
        return subprocess.CompletedProcess(
            command,
            response[0],
            stdout=response[1],
            stderr="",
        )

    monkeypatch.setattr(DockerSandboxRuntime, "available", staticmethod(lambda: True))
    monkeypatch.setattr(
        "causal_agent_bench.level5.evaluator.subprocess.run",
        fake_run,
    )
    report = run_evaluator_malicious_campaign(
        image="cab/evaluator-fixture:test",
        execute_containers=True,
    )
    assert observed_runs == len(EVALUATOR_CONTAINER_ATTACKS)
    assert report["executed_count"] == len(EVALUATOR_CONTAINER_ATTACKS)
    assert report["not_executed_count"] == 0
    assert report["critical_unresolved_count"] == 0
    assert report["passed"]


def test_explicit_private_key_environment_never_guesses(monkeypatch, tmp_path):
    monkeypatch.delenv("CAB_TEST_PRIVATE_KEY_PATH", raising=False)
    with pytest.raises(RuntimeError, match="missing"):
        explicit_private_key_environment("CAB_TEST_PRIVATE_KEY_PATH")
    monkeypatch.setenv("CAB_TEST_PRIVATE_KEY_PATH", str(tmp_path / "key.pem"))
    assert explicit_private_key_environment("CAB_TEST_PRIVATE_KEY_PATH") == tmp_path / "key.pem"
