# Ablation plan

## Engineering-only (run now, seconds)

- `configs/pilot_mock_agents_failure_modes.yaml` — mock behavior modes
- `configs/ablations/*_local_stub.yaml` — prompt/scaffold ablations on stub
- `configs/pilot_zero_cost_debug_matrix.yaml` — multi mock agent debug

## Preliminary local (when Ollama time available)

- Micro direct-tool ablations on `pilot_free_local_micro_3.yaml`
- Fast 5–10 instance slices before any 120×3 run

## Provider ablations (paid, later)

- `configs/ablation_matrix_local_stub.yaml` → replace stub with provider cells
- Require `allow_paid_calls: true` + explicit budget

## Evidence rules

- Stub/mock ablations → engineering tables only
- Local Ollama ablations → preliminary observations
- Provider ablations → pilot candidate after validation
