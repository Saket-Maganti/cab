# CAB hostile integrity audit

Generated at `2026-08-05T05:57:40.898070+00:00`.  Provider-free, fixture-only.

Every workspace below is synthetic and sealed by the public fixture
authority.  No private material is read, and no result here is evidence of
anything except that the gates refuse what they are supposed to refuse.

## Result

- attacks attempted: **66**
- rejected at or before the consuming gate: **66**
- falsely accepted: **0**
- status: **CAB_HOSTILE_INTEGRITY_AUDIT_PASSED**

## Legitimate baseline

| check | value |
| --- | --- |
| workflow completes | True |
| C10 mechanics | `C10_MECHANICS_PASS` |
| C10 status | `C10_PENDING_GENUINE_REVIEW` |
| counts as genuine evidence | False |
| Stage-1 snapshot checks | True |
| Stage-2 snapshot checks | True |

## Schema surface under audit

| schema | version |
| --- | --- |
| two-stage workflow | `cab_review_ready_v2_two_stage_workflow_v3` |
| Stage-1 commitment | `cab_stage1_commitment_v3` |
| committed Stage-1 snapshot | `cab_committed_stage1_snapshot_v1` |
| committed Stage-2 snapshot | `cab_committed_stage2_snapshot_v1` |

## Attacks by receipt chain

| receipt chain | attacks |
| --- | --- |
| `adjudication` | 12 |
| `agreement` | 1 |
| `artifact_origin` | 1 |
| `c10_report` | 2 |
| `committed_stage1_snapshot` | 6 |
| `exclusion_register` | 1 |
| `execution_authorization` | 1 |
| `final_adjudicated_records` | 3 |
| `reviewed_slice_lock` | 3 |
| `reviewer_declaration` | 1 |
| `stage1_commitment` | 2 |
| `stage1_submission` | 20 |
| `stage2_issuance` | 5 |
| `stage2_submission` | 8 |

## Every attack

| attack | receipt chain | mutated after | expected gate | actual gate | scope | result |
| --- | --- | --- | --- | --- | --- | --- |
| `stage1_notes_modified_and_resealed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_confidence_modified_and_resealed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_non_gating_judgement_modified` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_gating_judgement_modified` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_row_added` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_row_removed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_rows_reordered` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_item_id_duplicated` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_reviewer_role_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_pseudonym_binding_changed` | `reviewer_declaration` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_package_hash_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_declaration_hash_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_qualification_hash_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_validation_result_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_row_count_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_payload_hash_retained_content_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_content_retained_envelope_changed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_reviewer_a_receipt_replaced_with_b` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_older_valid_receipt_replayed` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_receipt_copied_from_another_workspace` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_snapshot_file_replaced` | `committed_stage1_snapshot` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_snapshot_manifest_replaced` | `committed_stage1_snapshot` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_snapshot_file_deleted` | `committed_stage1_snapshot` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_conflicting_live_receipt_created` | `stage1_submission` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_snapshot_replaced_by_symlink` | `committed_stage1_snapshot` | `commit_stage1` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage1_fixture_receipt_copied_into_production_verification` | `artifact_origin` | `commit_stage1` | `committed_stage1_snapshot` | `mutation_refused` | production_invariant | REJECTED |
| `stage1_snapshot_made_world_readable_in_production` | `committed_stage1_snapshot` | `commit_stage1` | `committed_stage1_snapshot` | `mutation_refused` | production_invariant | REJECTED |
| `stage2_issuance_swapped` | `stage2_issuance` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_archive_hash_swapped` | `stage2_issuance` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_namespace_swapped` | `stage2_issuance` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_reviewers_swapped` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_stale_stage1_commitment` | `stage1_commitment` | `submit_stage2` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage2_changed_stage1_snapshot` | `committed_stage1_snapshot` | `submit_stage2` | `committed_stage1_snapshot` | `committed_stage1_snapshot` | production_invariant | REJECTED |
| `stage2_judgement_altered` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_applicability_altered` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_not_applicable_value_altered` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_package_hash_altered` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_issuance_replayed_from_another_workspace` | `stage2_issuance` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_issuance_copied_between_reviewers` | `stage2_issuance` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_payload_hash_retained_content_changed` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_submission_replaced_after_queue` | `stage2_submission` | `build_queues` | `committed_stage2_snapshot` | `committed_stage2_snapshot` | production_invariant | REJECTED |
| `stage2_third_submission_after_commitment` | `stage2_submission` | `submit_stage2` | `committed_stage2_snapshot` | `mutation_refused` | production_invariant | REJECTED |
| `adjudication_against_a_changed_queue` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_queue_disputed_set_changed` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_decision_omitted` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_decision_added` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_final_value_changed` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_exclusion_decision_changed` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_rationale_changed` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_evidence_reference_changed` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_adjudicator_changed` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_by_a_reviewer` | `adjudication` | `issue_adjudicator_packages` | `final_records` | `mutation_refused` | production_invariant | REJECTED |
| `adjudication_copied_from_another_workspace` | `adjudication` | `adjudicate` | `final_records` | `final_records` | production_invariant | REJECTED |
| `adjudication_replaced_after_final_records` | `adjudication` | `settle` | `c10` | `c10` | production_invariant | REJECTED |
| `final_records_replaced` | `final_adjudicated_records` | `settle` | `c10` | `c10` | production_invariant | REJECTED |
| `agreement_report_made_stale` | `agreement` | `settle` | `c10` | `c10` | production_invariant | REJECTED |
| `final_records_included_pairs_changed` | `final_adjudicated_records` | `settle` | `c10` | `c10` | production_invariant | REJECTED |
| `final_records_exclusion_reason_changed` | `final_adjudicated_records` | `settle` | `c10` | `c10` | production_invariant | REJECTED |
| `c10_report_copied_from_another_workspace` | `c10_report` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `c10_report_changed_after_lock` | `c10_report` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `exclusion_register_replaced` | `exclusion_register` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `slice_lock_replaced` | `reviewed_slice_lock` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `slice_lock_source_commit_mismatch` | `reviewed_slice_lock` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `slice_lock_freeze_mismatch` | `reviewed_slice_lock` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `slice_lock_packet_mismatch` | `stage1_commitment` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |
| `execution_authorization_replayed` | `execution_authorization` | `lock` | `execution_authorization` | `execution_authorization` | production_invariant | REJECTED |

## What a rejection means

Each attack mutates a sealed artifact on disk and re-seals it with a valid
MAC, modelling a coordinator who holds the sealing key.  A rejection means
the workflow noticed that what it committed is no longer what it is
reading — not merely that a signature failed.

`mutation_refused` means the workflow declined the hostile input before it
could be written at all, which is the earliest possible refusal.
