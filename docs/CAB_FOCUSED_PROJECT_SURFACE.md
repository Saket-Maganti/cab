# CAB Active Surface Index

This is the short, canonical map for the pre-execution repository. It indexes
active surfaces; it does not promote fixture, static-audit, or design artifacts
to scientific evidence.

The authoritative state and next action are in `CURRENT_PROJECT_STATE.md`.

## Entry points

| Surface | Canonical path | Role |
|---|---|---|
| Repository overview | `README.md` | Installation, scope, and evidence boundary |
| Documentation hub | `docs/index.md` | Reader navigation |
| Safe automation | `Makefile` | Provider-free checks and explicit execution targets |
| CLI | `src/causal_agent_bench/cli.py` | Installed command surface |
| Provider-free CI | `.github/workflows/max-ceiling-provider-free.yml` | Correctness, data, notebook, security, claim, and release gates |

## Correctness contracts

| Contract | Canonical path |
|---|---|
| Typed answer contracts | `src/causal_agent_bench/answer_contracts.py` |
| Typed final-answer scorer | `src/causal_agent_bench/metrics/typed_final_answer.py` |
| Matched causal robustness | `src/causal_agent_bench/metrics/causal_robustness.py` |
| Paired statistical procedures | `src/causal_agent_bench/metrics/statistics.py` |
| Canonical split registry | `src/causal_agent_bench/safety/split_registry.py` |
| Run provenance and merge contract | `src/causal_agent_bench/runners/run_manifest_v2.py` |
| Frozen scorer-v3 endpoints | `configs/pre_run/frozen_endpoints.json` |
| Evaluated system identity | `src/causal_agent_bench/runners/system_identity.py` and `configs/pre_run/evaluated_system_manifest.json` |
| Manifest-driven resource planner | `src/causal_agent_bench/runners/resource_planner.py` |

## Study inputs and execution surfaces

| Surface | Canonical path | Current evidence class |
|---|---|---|
| Study-role membership and hashes | `data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json` | `ENGINEERING_ONLY` |
| Compact v2 packet and commitment | `data/human_validation/compact20_real_review/` and `data/manifests/compact20_review_packet_v2_public_commitment.json` | `HUMAN_INPUT_REQUIRED` |
| Scale v2 public commitment | `data/manifests/scale100_confirmatory_v2_public_manifest.json` | protected candidate; execution forbidden |
| Artifact-rich synthetic transfer v2 commitment | `data/manifests/naturalistic_transfer_v2_public_manifest.json` | protected candidate; execution forbidden |
| V2 execution templates | `configs/iclr/*v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml` | template only; human gates pending |
| Kaggle T4×2 notebooks | `notebooks/kaggle/CAB_T4X2_*.ipynb` | `FIXTURE_ONLY` until an approved live run |
| Human-review gate | `scripts/validate_cab_human_reviews.py` | `HUMAN_INPUT_REQUIRED` |

## Safety, release, and governance

| Policy or gate | Canonical path |
|---|---|
| Evidence policy | `docs/EVIDENCE_LEVEL_POLICY.md` |
| Claims | `docs/claim_ledger.json` and `scripts/check_claim_ledger.py` |
| Security and privacy | `docs/SECURITY_AND_PRIVACY.md` and `scripts/security_check.py` |
| Dataset versioning | `docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md` |
| Held-out release governance | `docs/HELDOUT_RELEASE_GOVERNANCE.md` |
| Code and data licenses | `LICENSE` and `DATA_LICENSE.md` |
| Release inventory | `release/release_manifest.json` and `scripts/release_check.py` |
| Archive/deprecation plan | `docs/DOC_ARCHIVE_PLAN_NO_DELETE.md` |
| Pre-run scientific gate | `cab pre-run scientific-check` and `.github/workflows/pre-run-scientific-hardening.yml` |

## Evidence boundary

Real provider outputs, independent human validation, C10 isolation validation,
and post-run scorer audits are not present. Therefore main-result, causal,
cross-provider, human-validation, and venue-readiness claims remain forbidden.
The canonical aggregate gate is `make pre-run-scientific-check`; it performs no
model or provider execution. The exact next action is genuine dual independent
Compact-20 review plus separate adjudication, not another engineering sprint.
