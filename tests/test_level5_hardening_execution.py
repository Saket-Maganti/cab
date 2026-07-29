from __future__ import annotations

import json
import sys

import pytest

from causal_agent_bench.level5.execution import (
    ConcurrentFixtureBackend,
    ConcurrentScheduler,
    ContentAddressedStore,
    DisabledProviderBackend,
    ExecutionFailure,
    FailureClass,
    KaggleBundleBackend,
    LocalSubprocessBackend,
    QueueRepository,
    RunPlanSpec,
    RunState,
    compile_run_plan,
    run_crash_consistency_demo,
    run_scheduler_stress,
)
from causal_agent_bench.level5.registry import SQLiteRegistry


def _manifest(*, backend: str = "fixture", tasks: int = 3):
    return compile_run_plan(
        RunPlanSpec(
            study_id="study.hardening.execution",
            task_version="tasks.hardening.v1",
            split_version="split.hardening.v1",
            model_versions=["model.fixture.v1"],
            policies=["policy.fixture.v1"],
            repeats=1,
            seeds=[7],
            task_ids=[f"task_{index}" for index in range(tasks)],
            scorer_version="scorer.fixture.v1",
            code_revision="test",
            backend=backend,
            max_concurrency=4,
            max_attempts=3,
            timeout_seconds=1,
        ),
        shard_count=2,
    )


def _acquire(queue: QueueRepository, manifest, worker: str = "worker.test"):
    lease = queue.acquire(
        worker_id=worker,
        manifest_hash=manifest.manifest_hash,
        backend_limit=4,
        model_limit=4,
        global_limit=4,
        lease_seconds=0.1,
    )
    assert lease is not None
    return lease


def test_queue_lifecycle_retry_stale_lease_and_exactly_once_commit(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    queue = QueueRepository(registry)
    manifest = _manifest(tasks=2)
    queue.enqueue(
        manifest,
        dependencies={manifest.units[1].unit_id: [manifest.units[0].unit_id]},
        priorities={manifest.units[0].unit_id: 10},
    )
    queue.enqueue(manifest)
    queue.pause(manifest.manifest_hash)
    assert queue.summary(manifest.manifest_hash)["state_counts"]["PAUSED"] == 2
    queue.resume(manifest.manifest_hash)

    lease = _acquire(queue, manifest)
    queue.heartbeat(lease, lease_seconds=0.1)
    queue.mark_running(lease)
    target = queue.fail(
        lease,
        RuntimeError("fixture transient"),
        failure_class=FailureClass.TRANSIENT,
        retryable=True,
        retry_base_seconds=0,
    )
    assert target is RunState.RETRY_WAIT
    retried = _acquire(queue, manifest, "worker.retry")
    assert retried.attempt == 2
    queue.mark_running(retried)
    store = ContentAddressedStore(tmp_path / "cas")
    digest = store.put_json({"unit_id": retried.unit.unit_id}).digest
    queue.stage_result(retried, digest)
    assert queue.commit_success(retried, digest) is True
    assert queue.commit_success(retried, digest) is False

    dependent = _acquire(queue, manifest, "worker.dependent")
    queue.mark_running(dependent)
    queue.heartbeat(dependent, lease_seconds=0.01)
    with registry.transaction() as connection:
        connection.execute(
            "UPDATE worker_leases SET expires_at=0 WHERE unit_id=?",
            (dependent.unit.unit_id,),
        )
    assert queue.reclaim_stale() == 1
    with pytest.raises(PermissionError, match="stale"):
        queue.heartbeat(dependent, lease_seconds=1)
    replacement = _acquire(queue, manifest, "worker.replacement")
    queue.mark_running(replacement)
    digest2 = store.put_json({"unit_id": replacement.unit.unit_id}).digest
    queue.stage_result(replacement, digest2)
    queue.commit_success(replacement, digest2)
    summary = queue.summary(manifest.manifest_hash)
    assert summary["state_counts"] == {"SUCCEEDED": 2}
    assert summary["duplicate_committed_results"] == 0
    assert queue.is_complete(manifest.manifest_hash)
    assert queue.events()


def test_queue_quota_cancellation_and_staged_crash_recovery(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    queue = QueueRepository(registry)
    manifest = _manifest(tasks=3)
    quota_unit = manifest.units[0].unit_id
    queue.set_quota("blocked", 0)
    queue.enqueue(
        manifest,
        quota_keys={quota_unit: "blocked"},
        priorities={quota_unit: 100},
    )
    lease = queue.acquire(
        worker_id="quota-worker",
        manifest_hash=manifest.manifest_hash,
        backend_limit=4,
        model_limit=4,
        global_limit=4,
        lease_seconds=1,
    )
    assert lease is not None
    assert queue.summary(manifest.manifest_hash)["state_counts"]["QUOTA_DEFERRED"] == 1
    cancel_unit = next(
        unit.unit_id
        for unit in manifest.units
        if unit.unit_id not in {quota_unit, lease.unit.unit_id}
    )
    assert queue.cancel(cancel_unit)
    assert not queue.cancel(cancel_unit)
    queue.mark_running(lease)
    store = ContentAddressedStore(tmp_path / "cas")
    digest = store.put_json({"unit_id": lease.unit.unit_id, "stage": "written"}).digest
    queue.stage_result(lease, digest)
    assert queue.recover_staged_results(store) == 1
    assert queue.summary(manifest.manifest_hash)["missing_terminal_states"] == 0
    with pytest.raises(KeyError):
        queue.cancel("unit.missing")
    with pytest.raises(ValueError, match="non-negative"):
        queue.set_quota("bad", -1)


def test_five_point_crash_consistency_demo(tmp_path):
    report = run_crash_consistency_demo(tmp_path / "crash-demo")
    assert report["passed"] is True
    assert report["duplicate_committed_results"] == 0
    assert [row["crash_point"] for row in report["crash_points"]] == [
        "after_lease",
        "after_artifact_write",
        "before_registry_commit",
        "after_artifact_registration",
        "before_terminal_scheduler_state",
    ]


def test_concurrent_scheduler_and_fixture_backend_contract(tmp_path):
    manifest = _manifest(tasks=12)
    fail_once = {manifest.units[0].unit_id}
    backend = ConcurrentFixtureBackend(fail_once=fail_once)
    assert backend.capabilities().fixture_only
    assert backend.estimate_resources(manifest.units[0]).wall_seconds >= 0.1
    handle = backend.launch(manifest.units[0], attempt=1)
    assert backend.poll(handle) == "RUNNING"
    assert backend.heartbeat(handle)["state"] == "RUNNING"
    checkpoint = backend.checkpoint(handle)
    resumed = backend.resume(manifest.units[0], checkpoint, attempt=2)
    backend.cleanup(resumed)
    with pytest.raises(ValueError, match="checkpoint"):
        backend.resume(manifest.units[0], {"unit_id": "wrong"}, attempt=2)
    backend.cleanup(handle)

    registry = SQLiteRegistry(tmp_path / "run.sqlite3")
    result = ConcurrentScheduler(
        ConcurrentFixtureBackend(fail_once=fail_once),
        ContentAddressedStore(tmp_path / "cas"),
        registry,
        max_concurrency=4,
    ).run(manifest)
    assert result["state_counts"] == {"SUCCEEDED": 12}
    assert result["duplicate_committed_results"] == 0
    with pytest.raises(ValueError, match="positive"):
        ConcurrentScheduler(
            ConcurrentFixtureBackend(),
            ContentAddressedStore(tmp_path / "invalid"),
            registry,
            max_concurrency=0,
        )


def test_local_subprocess_backend_success_failures_timeout_and_cancel(tmp_path):
    manifest = _manifest(backend="local_subprocess", tasks=1)
    unit = manifest.units[0]
    backend = LocalSubprocessBackend()
    backend.prepare(manifest)
    handle = backend.launch(unit, attempt=1)
    assert backend.heartbeat(handle)["pid"] > 0
    result = backend.collect(handle, timeout_seconds=2)
    assert result.unit_id == unit.unit_id
    assert result.orphan_processes == 0
    assert backend.provenance_receipt(unit, result, attempt=1)["exit_code"] == 0
    backend.cleanup(handle)

    variants = [
        ([sys.executable, "-c", "print('not-json')"], FailureClass.INVALID_OUTPUT),
        (
            [sys.executable, "-c", "import json;print(json.dumps({'unit_id':'wrong'}))"],
            FailureClass.INVALID_OUTPUT,
        ),
        ([sys.executable, "-c", "raise SystemExit(3)"], FailureClass.PERMANENT),
    ]
    for index, (command, expected) in enumerate(variants):
        failing = LocalSubprocessBackend({unit.unit_id: command})
        failing_handle = failing.launch(unit, attempt=index + 1)
        with pytest.raises(ExecutionFailure) as caught:
            failing.collect(failing_handle, timeout_seconds=2)
        assert caught.value.failure_class is expected
        assert failing.classify_failure(caught.value)[0] is expected
        failing.cleanup()

    timeout_backend = LocalSubprocessBackend(
        {unit.unit_id: [sys.executable, "-c", "import time;time.sleep(5)"]}
    )
    timeout_handle = timeout_backend.launch(unit, attempt=1)
    with pytest.raises(ExecutionFailure) as timeout:
        timeout_backend.collect(timeout_handle, timeout_seconds=0.01)
    assert timeout.value.failure_class is FailureClass.TIMEOUT
    timeout_backend.cleanup()

    cancel_backend = LocalSubprocessBackend(
        {unit.unit_id: [sys.executable, "-c", "import time;time.sleep(5)"]}
    )
    cancel_handle = cancel_backend.launch(unit, attempt=1)
    cancel_backend.cancel(unit.unit_id)
    with pytest.raises(ExecutionFailure) as killed:
        cancel_backend.collect(cancel_handle, timeout_seconds=1)
    assert killed.value.failure_class is FailureClass.WORKER_KILLED
    cancel_backend.cleanup()


def test_kaggle_offline_bundle_import_and_provider_fail_closed(tmp_path):
    manifest = _manifest(tasks=3)
    backend = KaggleBundleBackend()
    bundle = backend.export_bundle(manifest, tmp_path / "bundle")
    assert bundle["provider_execution"] is False
    assert len(bundle["shards"]) == 2
    with pytest.raises(ValueError, match="accelerator"):
        backend.export_bundle(manifest, tmp_path / "bad", accelerator_mode="cpu")
    receipt = {
        "commitments": bundle["commitments"],
        "results": [
            {"unit_id": manifest.units[0].unit_id, "score": 1},
        ],
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    imported = backend.import_receipts(
        manifest,
        receipt_path,
        ContentAddressedStore(tmp_path / "cas"),
        registry,
    )
    assert imported["partial_session"] is True
    assert imported["commitments_verified"] is True
    receipt["commitments"]["manifest_hash"] = "wrong"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="commitment"):
        backend.import_receipts(
            manifest,
            receipt_path,
            ContentAddressedStore(tmp_path / "cas2"),
            registry,
        )
    with pytest.raises(RuntimeError, match="never calls"):
        backend.launch(manifest.units[0], attempt=1)
    assert backend.poll("unused") == "NOT_EXECUTED"
    assert backend.heartbeat("unused")["state"] == "NOT_EXECUTED"
    assert backend.checkpoint("unused")["state"] == "OFFLINE_EXPORT"
    assert backend.classify_failure(RuntimeError("x")) == (FailureClass.PERMANENT, False)

    provider_manifest = _manifest(backend="provider", tasks=1)
    provider = DisabledProviderBackend()
    assert len(provider.validate_compatibility(provider_manifest)) == 3
    with pytest.raises(PermissionError, match="approval"):
        provider.prepare(provider_manifest)
    approved = DisabledProviderBackend(
        approved=True,
        credentials_present=True,
        budget_approved=True,
    )
    approved.prepare(provider_manifest)


@pytest.mark.slow
def test_scheduler_stress_is_deterministic_across_real_worker_counts(tmp_path):
    report = run_scheduler_stress(
        tmp_path,
        unit_count=160,
        concurrencies=(1, 2, 4),
    )
    assert report["passed"] is True
    assert report["deterministic_hash_agreement"] is True
    assert report["duplicate_committed_results"] == 0
    assert all(row["paused_units_observed"] for row in report["reports"])
    assert all(row["stale_leases_recovered"] == 1 for row in report["reports"])
