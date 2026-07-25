# CAB Active Surface Index

This is the short, canonical map for the pre-execution repository. It indexes
active surfaces; it does not promote fixture, static-audit, or design artifacts
to scientific evidence.

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

## Study inputs and execution surfaces

| Surface | Canonical path | Current evidence class |
|---|---|---|
| Study-role membership and hashes | `data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json` | `ENGINEERING_ONLY` |
| Confirmatory generation configs | `configs/generate_*_confirmatory_v1.yaml` | `DESIGN_ONLY` |
| Naturalistic generation config | `configs/generate_naturalistic_transfer_v1.yaml` | `DESIGN_ONLY` |
| Candidate datasets | `data/processed/*_candidate/` | `HUMAN_INPUT_REQUIRED` |
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

## Evidence boundary

Real provider outputs, independent human validation, C10 isolation validation,
and post-run scorer audits are not present. Therefore main-result, causal,
cross-provider, human-validation, and venue-readiness claims remain forbidden.
The safe aggregate check is `make max-ceiling-ci-serial`; it performs no model
or provider execution.
