from __future__ import annotations

import json

import pytest

from causal_agent_bench.level5.benchmark import (
    PrivacyClass,
    SplitRole,
    TaskLifecycle,
    advance_lifecycle,
    build_review_packet,
    compile_intervention,
    diversity_report,
)
from causal_agent_bench.level5.execution import (
    ContentAddressedStore,
    FixtureBackend,
    LocalScheduler,
    compile_run_plan,
    fixture_20_spec,
)
from causal_agent_bench.level5.reproduction import public_fixture_authoring_spec


def test_intervention_compilation_is_deterministic_and_public_safe():
    spec = public_fixture_authoring_spec()
    first = compile_intervention(spec)
    second = compile_intervention(spec)
    assert first.receipt.instance_id == second.receipt.instance_id
    assert first.receipt.public_hash == second.receipt.public_hash
    assert first.private is None
    serialized = json.dumps(first.public).lower()
    assert spec.base_task.answer_contract.target_hash not in serialized
    assert "gold_source" not in serialized


def test_intervention_rejects_answer_change_and_multiple_mechanisms():
    spec = public_fixture_authoring_spec()
    with pytest.raises(ValueError, match="changes the target answer"):
        compile_intervention(
            spec.model_copy(
                update={
                    "intervention": spec.intervention.model_copy(
                        update={"expected_target_hash": "0" * 64}
                    )
                }
            )
        )
    with pytest.raises(ValueError, match="exactly one"):
        compile_intervention(
            spec.model_copy(
                update={
                    "intervention": spec.intervention.model_copy(
                        update={"mechanism_count": 2}
                    )
                }
            )
        )


def test_intervention_rejects_role_collision_and_confirmatory_public_role():
    spec = public_fixture_authoring_spec()
    duplicate_tools = [spec.base_task.tools[0], spec.base_task.tools[0]]
    with pytest.raises(ValueError, match="role collision"):
        compile_intervention(
            spec.model_copy(
                update={"base_task": spec.base_task.model_copy(update={"tools": duplicate_tools})}
            )
        )
    with pytest.raises(ValueError, match="confirmatory"):
        compile_intervention(
            spec.model_copy(
                update={
                    "base_task": spec.base_task.model_copy(
                        update={
                            "split_role": SplitRole.CONFIRMATORY,
                            "privacy_class": PrivacyClass.PUBLIC,
                        }
                    )
                }
            )
        )


def test_review_packet_is_blinded_and_requires_two_reviews():
    compiled = compile_intervention(public_fixture_authoring_spec())
    packet = build_review_packet([compiled])
    assert packet["blinded"] is True
    assert packet["coverage"]["required_reviews_per_item"] == 2
    assert "target_hash" not in json.dumps(packet)


def test_diversity_detects_exact_and_normalized_duplicates():
    instance = compile_intervention(public_fixture_authoring_spec()).public
    duplicate = {**instance, "prompt": f"  {instance['prompt'].upper()}!!  "}
    report = diversity_report([instance, instance, duplicate])
    assert report["passed"] is False
    assert report["exact_duplicates"]
    assert report["normalised_duplicates"]


def test_task_lifecycle_is_fail_closed():
    assert (
        advance_lifecycle(TaskLifecycle.DRAFT, TaskLifecycle.STATIC_VALIDATED)
        is TaskLifecycle.STATIC_VALIDATED
    )
    with pytest.raises(ValueError, match="illegal"):
        advance_lifecycle(TaskLifecycle.DRAFT, TaskLifecycle.ACTIVE)


def test_run_plan_is_deterministic_disjoint_and_has_20_units():
    first = compile_run_plan(fixture_20_spec(), shard_count=2)
    second = compile_run_plan(fixture_20_spec(), shard_count=2)
    assert first.manifest_hash == second.manifest_hash
    assert len(first.units) == 20
    assert len({unit.unit_id for unit in first.units}) == 20
    assert {unit.shard for unit in first.units} == {0, 1}


def test_backend_mismatch_fails_closed():
    spec = fixture_20_spec().model_copy(update={"backend": "different"})
    manifest = compile_run_plan(spec)
    with pytest.raises(ValueError, match="backend mismatch"):
        FixtureBackend().prepare(manifest)


def test_cas_atomic_dedup_compression_export_import_and_gc(tmp_path):
    store = ContentAddressedStore(tmp_path / "cas")
    metadata = store.put_json({"fixture": True}, artifact_class="fixture", compress=True)
    same = store.put_json({"fixture": True}, artifact_class="fixture", compress=True)
    assert metadata.digest == same.digest
    assert json.loads(store.get_bytes(metadata.digest)) == {"fixture": True}
    assert store.verify()["verified"] == 1
    bundle = store.export_bundle([metadata.digest], tmp_path / "bundle")
    imported = ContentAddressedStore(tmp_path / "restored")
    assert imported.import_bundle(bundle) == [metadata.digest]
    assert imported.verify()["passed"] is True
    gc = imported.gc_dry_run(set())
    assert gc["candidate_digests"] == [metadata.digest]
    assert gc["deleted"] == 0


def test_cas_detects_corruption(tmp_path):
    store = ContentAddressedStore(tmp_path / "cas")
    metadata = store.put_bytes(b"evidence", artifact_class="fixture")
    store._object_path(metadata.digest).write_bytes(b"corrupt")
    report = store.verify(metadata.digest)
    assert report["passed"] is False


def test_scheduler_interruption_resume_retry_and_deterministic_merge(tmp_path):
    manifest = compile_run_plan(fixture_20_spec(), shard_count=2)
    store = ContentAddressedStore(tmp_path / "cas")
    fail_once = {manifest.units[0].unit_id}
    scheduler = LocalScheduler(FixtureBackend(fail_once=fail_once), store)
    first = scheduler.run(manifest, tmp_path / "run", interrupt_after=7)
    assert first["status"] == "INTERRUPTED"
    assert first["completed_units"] == 7
    final = scheduler.run(manifest, tmp_path / "run")
    assert final["status"] == "COMPLETE"
    assert final["completed_units"] == 20
    assert final["duplicate_units"] == 0
    repeated = scheduler.run(manifest, tmp_path / "run")
    assert repeated["merge_digest"] == final["merge_digest"]
    checkpoint = json.loads((tmp_path / "run/checkpoint.json").read_text())
    assert checkpoint["attempts"][manifest.units[0].unit_id] == 2


def test_scheduler_rejects_changed_manifest_on_resume(tmp_path):
    manifest = compile_run_plan(fixture_20_spec(), shard_count=2)
    store = ContentAddressedStore(tmp_path / "cas")
    scheduler = LocalScheduler(FixtureBackend(), store)
    scheduler.run(manifest, tmp_path / "run", interrupt_after=1)
    changed = compile_run_plan(
        fixture_20_spec().model_copy(update={"code_revision": "changed"}), shard_count=2
    )
    with pytest.raises(ValueError, match="identical immutable manifest"):
        scheduler.run(changed, tmp_path / "run")
