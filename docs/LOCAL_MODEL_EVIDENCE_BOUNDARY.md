# Local Model Evidence Boundary

Status: `EVIDENCE_BOUNDARY_MEMO`

Existing local/Ollama traces are real inference artifacts where present, but they are not paper-eligible evidence in the current project state.

## Current Local Evidence

The repo contains local qwen2.5:7b / qwen2.5:7b-instruct planning and run artifacts. The documented local pilot path uses:

- local OpenAI-compatible provider class,
- Ollama-style local server,
- zero-cost budget mode,
- `allow_paid_calls: false`,
- `scientific_evidence_level: preliminary_or_engineering`,
- local deployment class such as `zero_cost_local_preliminary` or `local_open_weight_unvalidated`.

Some local run directories are incomplete or interrupted. They are useful engineering traces, not paper evidence.

## Boundary

Local preliminary traces may support:

- pipeline debugging,
- prompt/protocol debugging,
- scorer sanity debugging,
- local runtime planning,
- identifying malformed-output risks before paid/provider execution.

Local preliminary traces may not support:

- C1-C8,
- C10,
- paper-eligible result tables,
- final model ranking claims,
- provider-backed evidence claims,
- NeurIPS-ready or benchmark-validated language.

## Upgrade Requirements

Local model evidence cannot be treated as paper-eligible unless a future policy explicitly upgrades it with:

- complete run status,
- full model artifact or snapshot metadata,
- server stack and hardware metadata,
- quantization/batching/settings metadata,
- reproducibility notes,
- scorer sanity,
- manual review where claims depend on trajectories,
- separation from commercial provider results,
- claim-ledger and paper-asset eligibility approval.

No such upgrade exists now.

## Use In The First 3-Model Compact-20 Pilot

A strong open/local model may be one planned category, but it must be labeled clearly. Local-only evidence cannot substitute for a strong multi-model/provider benchmark unless the paper scope is explicitly narrowed to local/open deployments.

If local/open results are included in a future 3-model pilot, report them separately from commercial API/provider results unless the audit approves a combined interpretation.

## Current Claim State

No current claims are promoted by local/Ollama traces. C1-C8 and C10 remain planned/unsupported.

