# Experiment registry

Planned experiments for CausalAgentBench. **Do not run long/paid jobs without explicit approval.**

## micro_stub

| Field | Value |
|-------|-------|
| Purpose | Fastest engineering validation of runner/scoring/analysis |
| Cost | $0 |
| Runtime | seconds |
| Evidence | engineering_only |
| Approval | none |
| Config | `configs/pilot_stub_micro_3.yaml` |
| Artifacts | trajectories, report, failure_gallery |

## micro_local

| Field | Value |
|-------|-------|
| Purpose | Bounded Ollama preliminary smoke |
| Cost | $0 |
| Runtime | minutes |
| Evidence | preliminary_or_engineering |
| Approval | user time budget |
| Config | `configs/pilot_free_local_micro_3.yaml` |
| Artifacts | trajectories, checkpoint, report |

## pilot_20_local

| Field | Value |
|-------|-------|
| Purpose | Local 20-instance slice, 1 agent |
| Cost | $0 |
| Runtime | tens of minutes |
| Evidence | preliminary |
| Approval | user time budget |
| Config | `configs/pilot_free_local_fast_10.yaml` |
| Artifacts | full run dir + report + index entry |

## pilot_20_provider

| Field | Value |
|-------|-------|
| Purpose | First non-oracle multi-provider pilot |
| Cost | low–medium USD |
| Runtime | minutes–hours |
| Evidence | pilot candidate |
| Approval | explicit budget + `allow_paid_calls: true` |
| Config | `configs/pilot_multi_provider_20.yaml` |
| Artifacts | scored run, paper_assets (if eligible) |

## pilot_100

| Field | Value |
|-------|-------|
| Purpose | Medium-scale agent comparison |
| Cost | medium USD |
| Runtime | hours |
| Evidence | pilot |
| Approval | explicit budget |
| Config | `configs/pilot_100_multi_agent.yaml` |

## main_500

| Field | Value |
|-------|-------|
| Purpose | Main benchmark evaluation |
| Cost | high USD |
| Runtime | many hours |
| Evidence | main candidate |
| Approval | full experiment sign-off |
| Config | `configs/main_500_multi_provider.yaml` |

## human_validation

| Field | Value |
|-------|-------|
| Purpose | Label quality + diagnostic agreement |
| Cost | annotator time |
| Runtime | days–weeks |
| Evidence | validation study |
| Approval | protocol + sample size |
| Scripts | `scripts/sample_human_validation.py` |

## ablations

| Field | Value |
|-------|-------|
| Purpose | Prompt/scaffold factorial study |
| Cost | stub: $0; provider: per-cell |
| Runtime | stub: minutes; provider: hours |
| Evidence | engineering → pilot |
| Config | `configs/ablation_matrix_local_stub.yaml` |
| Plan | `experiments/ABLATION_PLAN.md` |
