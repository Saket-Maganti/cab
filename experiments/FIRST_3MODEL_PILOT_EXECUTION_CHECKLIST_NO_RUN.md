# First 3-Model Compact-20 Execution Checklist, No Run

Status: `NON_RUNNABLE_CHECKLIST`

This checklist is for future execution planning only. It does not authorize any provider, local LLM, or benchmark run.

## Prerequisites Before Any Run

- Compact-20 task review is complete for all selected rows.
- Compact-20 gold-policy review is complete for all selected rows.
- Any excluded candidate has a reviewed replacement.
- C10 review plan is assigned a status: before-run, after-run, or claim-blocking.
- The approved slice path exists and is separate from the pending candidate manifest.
- Provider/model choices are approved in writing.
- Budget cap and max-call cap are approved in writing.
- No API or provider secret is stored in YAML or repo files.
- Evidence safety check passes.
- The run index is fresh or the stale state is documented as inventory-only.

## API And Environment Requirements

- Provider credentials must live in the shell environment only.
- The operator must verify credential presence without printing values.
- Provider/model IDs must be captured in metadata.
- Pricing registry entries must be present or unknown-price stop conditions must block execution.
- No config may contain a literal secret, bearer token, or key-shaped value.

## Local Model Requirements If Used

- Local model use must be approved separately.
- Server stack, model artifact, quantization, hardware, and base URL class must be recorded.
- Local/open-weight results must remain separately labeled unless a later evidence policy upgrades them.
- Existing qwen2.5:7b traces do not count as paper-eligible evidence for this pilot.

## Manual Compact-20 Review Completion

The run is blocked until every selected row has:

- `task_clear` filled,
- `intervention_isolated` filled,
- `gold_policy_clear` filled,
- `include_in_compact20` filled,
- reviewer ID,
- review date,
- notes for any ambiguity.

## C10 Review Status

C10 remains unsupported unless:

- two-reviewer or approved-review protocol is complete,
- disagreements are adjudicated,
- agreement metrics are computed,
- reviewed rows link back to Compact-20 candidate IDs.

If C10 review is incomplete after the provider run, C10 must stay forbidden in paper wording.

## Config Approval Requirements

- Start from `configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml`.
- Copy to a separately named approved config only after review.
- Keep the template unchanged as non-runnable.
- Approved config must have explicit max trajectories, max calls, budget cap, and model list.
- `allow_paid_calls` may be changed only in the approved config, only at the authorized execution moment.
- The template must remain `allow_paid_calls: false` and `approved_for_live_run: false`.

## Budget Cap Requirements

- Cap total cost before execution.
- Cap provider calls before execution.
- Stop on unknown price.
- Stop on projected cost overrun.
- Stop on provider retry storms.
- Record estimated and actual cost metadata.

## Preflight Commands For Future Use Only

These are future preflight commands. They were not run as part of this no-execution plan.

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench validate-config --config configs/<APPROVED_3MODEL_COMPACT20_CONFIG>.yaml
python3 -m causal_agent_bench plan-run --config configs/<APPROVED_3MODEL_COMPACT20_CONFIG>.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/<APPROVED_3MODEL_COMPACT20_CONFIG>.yaml
python3 -m causal_agent_bench provider-pilot-preflight --config configs/<APPROVED_3MODEL_COMPACT20_CONFIG>.yaml
```

Do not run `causal_agent_bench run` from this checklist.

## Stop Conditions

Stop before execution if:

- no provider credential is available,
- approval is ambiguous,
- Compact-20 review is incomplete,
- C10 status is undocumented,
- budget or price is unknown,
- config contains a secret,
- preflight reports `ready_for_live_provider_run: false`,
- selected slice differs from reviewed rows.

Stop during future execution if:

- cost cap is reached,
- provider errors exceed the approved retry limit,
- malformed trajectories exceed the preregistered tolerance,
- model metadata is missing,
- scorer sanity fails,
- any command would run `main_200`, `main_500`, Compact-50, or a broad sweep.

## Post-Run Audit Requirements

Required after a future run:

- run health,
- evidence safety,
- scorer sanity,
- provider metadata audit,
- model metadata audit,
- cost audit,
- trajectory completeness audit,
- pair-link audit,
- paper asset eligibility audit,
- claim-evidence matrix,
- manual/C10 linkage audit.

## Scorer Sanity Requirements

- Scorer outputs must exist for every trajectory.
- Clean and intervention scores must be pairable.
- ACRS/rank calculations must be reproducible.
- Malformed-output handling must be visible.
- Scorer issue flags must be included in result tables.
- A sample of trajectory labels must be reviewed before C3-style language.

## Paper Asset Eligibility Requirements

A table or figure is paper-eligible only when:

- it is generated from complete audited provider-backed run artifacts,
- result placeholders are absent,
- metadata sidecars mark the source as eligible,
- no local-preliminary or mock/stub results are pooled without explicit labeling,
- claim ledger and evidence safety still pass,
- C1-C8/C10 wording remains within the evidence actually produced.

## Explicitly Not Authorized

- No provider calls.
- No local LLM calls.
- No `causal_agent_bench run`.
- No `main_200`.
- No `main_500`.
- No Compact-20 execution.
- No Compact-50 execution.
- No fake results.
- No fake annotations.
- No claim promotion.

