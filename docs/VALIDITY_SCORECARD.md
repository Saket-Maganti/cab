# Validity Scorecard

**Purpose:** Conservative static assessment of benchmark validity infrastructure.  
**Not:** Empirical performance evidence or claim promotion.

---

## Generate

```bash
python3 -m causal_agent_bench validity-scorecard --output-dir reports/validity_scorecard
```

Included in `all-no-run-reports` bundle.

---

## Dimensions (0–100 each)

| Dimension | What it measures |
|-----------|------------------|
| Leakage cleanliness | `blocker_cluster_count` from static leakage scan |
| Split integrity | Frozen pilot splits present; main frozen |
| Intervention isolation | Isolation audit score + high-risk queue |
| Gold-output consistency | Blockers/warnings; manual-review queue |
| Tool-schema consistency | Tool schema validation blockers |
| Human-validation readiness | Protocol/templates; annotations missing |
| Provider-pilot readiness | Preflight gate status |
| Main-benchmark readiness | Main freeze + HR queue state |
| Release readiness | Public v1.0 blocked |

---

## Score bands

| Band | Range | Meaning |
|------|-------|---------|
| `strong_infrastructure` | 80–100 | Review-ready scaffold |
| `adequate_scaffold` | 60–79 | Usable for pilot prep |
| `needs_work` | 40–59 | Manual review required |
| `blocked` | 0–39 | Do not proceed to claims |

---

## Evidence boundary

- `empirical_claims_allowed` is always **false** from this scorecard alone
- `valid_for_main_benchmark` remains **false** until main frozen + HV complete
- Scores can **decrease** after dataset edits — regenerate after any repair

---

## Current expected profile (2026-06-10)

| Dimension | Expected band | Notes |
|-----------|---------------|-------|
| Leakage | strong | 0 blocker clusters |
| Split (pilot) | adequate | pilot_v0.1 frozen |
| Intervention isolation | adequate–needs_work | HR queue pending |
| Gold-output | needs_work | warnings in queue |
| HV readiness | adequate scaffold | no annotations |
| Main readiness | blocked | not frozen |
| Release | blocked | public v1.0 N/A |

Regenerate for authoritative numbers:

```bash
python3 -m causal_agent_bench validity-scorecard --output-dir /tmp/cab_validity
```
