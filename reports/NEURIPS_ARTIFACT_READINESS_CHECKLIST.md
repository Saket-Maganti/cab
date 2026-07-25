# NeurIPS Artifact Readiness Checklist (Report Snapshot)

**Generated:** 2026-06-10 (static mirror)  
**Canonical source:** [docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md](../docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md)

This file is a reviewer-facing snapshot. For full checklist detail, use the canonical doc above.

## Current evidence state

| Metric | Value |
|--------|-------|
| Paper-eligible runs | **0** |
| Eligible empirical paper assets | **0** |
| Leakage blocker clusters | **0** |
| Provider gate | `template_safe_but_not_runnable` |
| C1–C8 | planned / unsupported |
| C9 | engineering_only |
| C10 | planned / unsupported |
| Public release | **blocked** |

## Readiness summary

| Area | Status |
|------|--------|
| Benchmark motivation (method) | Ready |
| Dataset construction (pilot) | Ready |
| Intervention taxonomy (definition) | Ready |
| Leakage controls | Ready (0 blocker clusters) |
| Split policy | Ready (pilot) |
| Tool environment docs | Ready |
| Metric definitions | Ready |
| Scoring reproducibility (engineering) | Ready |
| Claim–evidence mapping | Ready (static) |
| Human validation | **Blocked** (no annotations) |
| Provider runs | **Blocked** (no approval) |
| Artifact package | Ready (dev scaffold) |
| Empirical paper claims | **Blocked** |

## Safe verification commands

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_neurips_artifact_upgrade
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml
```

## Classification

`infrastructure_artifact_candidate` — NeurIPS-style **benchmark artifact** review path is open for design/reproducibility; empirical contribution path remains blocked.
