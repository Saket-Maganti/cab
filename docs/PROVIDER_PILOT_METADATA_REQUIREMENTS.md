# Provider pilot metadata requirements

A run directory is **paper-eligible** only when the shared classifier (`classify_run_entry` in `safety/common.py`) and export guards agree. Missing or ambiguous metadata is treated as **unsafe / needs review**.

This document lists fields required **after run completion** before setting `scientific_evidence: true` or promoting any claim.

---

## Required completion state

| Field / signal | Required value | Source |
|----------------|----------------|--------|
| `run_status` | `complete` | `checkpoint.json`, `infer_completion_state` |
| `completion_state` | `complete` | Same |
| `INCOMPLETE_RUN.json` | **absent** | Run directory |
| `completed_trajectories` | equals `expected_trajectories` when both present | Run index / checkpoint |
| Interrupted marker | **absent** | No interrupted status |

---

## Required scientific / provider metadata

| Field | Required value | Notes |
|-------|----------------|-------|
| `scientific_evidence` | strict `true` (not `"false"`, not unknown string) | Set only after human review post-run |
| `provider_type` | Real provider (e.g. `openai`, `anthropic`, `gemini`, `openrouter`) | Not `local`, `stub`, `mock`, `oracle`, `synthetic` |
| `providers` | At least one commercial API provider | See `COMMERCIAL_API_PROVIDERS` in `runners/evidence_scope.py` |
| `not_real_llm_behavior` | absent or `false` | Must not be true |
| `deployment_class` | not `mock_diagnostic_only` | |
| `engineering_only` | absent or `false` | |
| `evidence_scope` / `evidence_level` | not engineering-only scopes | e.g. not `mock_diagnostic_only`, `pilot_stub_engineering_only`, `preliminary_or_engineering` |
| `config_hash` | non-empty string | `config_hash.txt` / metadata |
| `run_name` | non-empty | metadata |
| `model_ids` or per-trajectory `model_name` | present for non-oracle agents | Required for paper fill verification |

---

## Classification targets (classifier output)

| `classification` | `paper_eligible` | Use |
|------------------|------------------|-----|
| `provider_backed_pilot` | `true` | Tiny pilot success |
| `main_benchmark` | `true` | Larger verified main runs (later) |
| `mock_diagnostic`, `stub_engineering`, `local_preliminary` | `false` | Never promote |
| `incomplete`, `interrupted` | `false` | Never promote |
| `unknown_needs_review` | `false` | Fix metadata first |

---

## Paid-run / budget metadata (if `allow_paid_calls: true`)

| Field | Required |
|-------|----------|
| `allow_paid_calls` | `true` only when intentionally enabled |
| `budget` / `budget_cap_usd` | Documented cap |
| `cost_estimate_preflight` or `actual_estimated_cost_usd` | Present for audit |
| `provider_runs[].model_id` | Set per agent |
| Pricing registry path used | `configs/model_pricing.yaml` |

---

## Required artifact sidecars (post `export-paper-assets`)

For each table/figure cited toward a claim:

| Sidecar field | Required |
|---------------|----------|
| `scientific_evidence` | `true` |
| `eligibility.eligible_for_paper_claims` | `true` |
| `evidence_scope` | Matches verified run scope |
| Placeholder text | **absent** in CSV/TeX body |

Regenerate after run:

```bash
python3 -m causal_agent_bench validate-paper-assets --output-dir reports/provider_pilot_review
python3 -m causal_agent_bench claim-evidence --no-tex --output-dir reports/provider_pilot_review
```

---

## Post-run governance commands

```bash
python3 -m causal_agent_bench run-health --output-dir reports/provider_pilot_review
python3 scripts/check_evidence_safety.py
```

Inspect JSON: `reports/provider_pilot_review/run_health_report.json` for the new `run_id`.

---

## Examples

### Eligible metadata (after review)

```json
{
  "run_name": "provider_pilot_tiny_APPROVED",
  "config_hash": "a1b2c3d4e5f6",
  "evidence_scope": "commercial_api_pilot_unvalidated",
  "provider_type": "openai",
  "providers": ["openai"],
  "scientific_evidence": true,
  "agents": ["direct_tool_provider_pilot"],
  "model_ids": ["gpt-4.1-mini"],
  "allow_paid_calls": true,
  "not_real_llm_behavior": false,
  "deployment_class": "commercial_api_pilot_unvalidated",
  "budget": {"max_total_usd": 5.0, "max_calls": 40}
}
```

Classifier expectation: `classification=provider_backed_pilot`, `paper_eligible=true`, completion complete, trajectories consistent.

### Ineligible — mock

```json
{
  "run_name": "mock_diag_run",
  "config_hash": "mock1",
  "evidence_scope": "mock_diagnostic_only",
  "provider_type": "mock",
  "scientific_evidence": false,
  "not_real_llm_behavior": true,
  "deployment_class": "mock_diagnostic_only"
}
```

### Ineligible — interrupted

```json
{
  "run_name": "pilot_interrupted",
  "config_hash": "int1",
  "evidence_scope": "commercial_api_pilot_unvalidated",
  "provider_type": "openai",
  "scientific_evidence": false,
  "completed_trajectories": 2,
  "expected_trajectories": 5
}
```

Plus file: `INCOMPLETE_RUN.json` → always ineligible.

### Ineligible — missing metadata

```json
{}
```

Or directory with only `checkpoint.json` and no `run_metadata.json` → `missing_metadata`, `unknown_needs_review`.

### Ineligible — oracle-only agent

```json
{
  "run_name": "provider_pilot_oracle_sanity",
  "config_hash": "ora1",
  "evidence_scope": "oracle_sanity_only",
  "provider_type": "local",
  "scientific_evidence": false,
  "agents": ["scripted_oracle_agent"],
  "not_real_llm_behavior": true,
  "deployment_class": "oracle_sanity_only"
}
```

Classifier: `oracle-only run` or `mock_diagnostic` / not `provider_backed_pilot`. Never promote claims.

### Ineligible — provider-looking config with oracle agent

```json
{
  "run_name": "provider_pilot_tiny_APPROVED",
  "config_hash": "badmix",
  "evidence_scope": "commercial_api_pilot_unvalidated",
  "provider_type": "openai",
  "scientific_evidence": false,
  "agents": ["direct_tool_provider_pilot", "scripted_oracle_agent"],
  "providers": ["openai"],
  "model_ids": ["gpt-4.1-mini"]
}
```

Even with a commercial provider, **oracle trajectories are not scientific evidence**. Remove oracle from APPROVED provider configs; use a separate oracle sanity run for plumbing only.

### Ineligible — `scientific_evidence: false` (string or bool)

```json
{
  "run_name": "provider_pilot_tiny_APPROVED",
  "evidence_scope": "commercial_api_pilot_unvalidated",
  "provider_type": "openai",
  "scientific_evidence": "false",
  "agents": ["direct_tool_provider_pilot"]
}
```

Strict parsers treat `"false"` as false — run remains ineligible until explicitly verified and set to boolean `true` after post-run checklist.

---

## Manual metadata update (only after checklist)

If the run is complete and classifiers pass but `scientific_evidence` is still `false` from defaults:

1. Edit `run_metadata.json` and `metadata.json` together (keep in sync).
2. Set `"scientific_evidence": true` only when every row in this document passes.
3. Re-run `run-health` and `claim-evidence` before any promotion.

Do not set `scientific_evidence: true` for mock/stub/local/interrupted runs.
