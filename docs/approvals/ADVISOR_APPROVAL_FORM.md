# Advisor Approval Form — Tiny Provider Pilot

**Template only.** Signing this form does **not** run providers or approve paid spend by itself.

## Run scope

| Field | Value |
|---|---|
| Config copy | `configs/provider_pilot_tiny_APPROVED.yaml` (copied from template) |
| Max instances | ≤ 5 |
| Max trajectories | ≤ 5 |
| Max budget (USD) | ≤ 5.00 (default cap) |
| Evidence scope | `provider_pilot_pending_verification` until post-run audit |

## Advisor checklist

- [ ] I reviewed `PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md` or latest `all-no-run-reports` bundle.
- [ ] True answer-leakage blocker clusters are **zero** (or explicitly deferred with written rationale).
- [ ] I will **not** approve empirical claims (C1–C8, C10) from this pilot alone.
- [ ] Human-validation protocol is acceptable for later C3/C10 (not required before dry-run).
- [ ] Dry-run may proceed after budget approval and APPROVED config copy exists.

## Required YAML fields (set only in APPROVED copy)

```yaml
approval:
  advisor_approved: true
  approved_for_dry_run: true   # dry-run only at this stage
  approved_for_live_run: false # remain false until live approval form signed
  approved_by: "<name>"
  approval_date: "YYYY-MM-DD"
  advisor_approval_id: "ADV-YYYY-NNN"
  max_budget_usd: 5.0
```

## Signatures

| Role | Name | Date | ID |
|---|---|---|---|
| Advisor | __________________ | __________ | ADV-_______ |

**Do not set `allow_paid_calls: true` until the budget + live-run forms are signed.**
