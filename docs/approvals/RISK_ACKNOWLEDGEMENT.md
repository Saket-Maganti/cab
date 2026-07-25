# Provider Pilot Risk Acknowledgement

I understand that:

1. **No empirical paper claims** exist yet (0 paper-eligible runs; C1–C8/C10 unsupported).
2. Provider pilot output stays **`scientific_evidence: false`** until post-run review.
3. Leakage repair must be complete before dry-run (`blocker_cluster_count: 0` for true answer leakage).
4. Template configs are **not runnable**; only an APPROVED copy may proceed to dry-run/live gates.
5. `allow_paid_calls: true` is permitted **only** in an APPROVED copy after live approval.
6. Cost estimates are indicative; unknown pricing is not zero cost.
7. Claim promotion (`--promote-to-supported`) is forbidden until eligibility + human validation requirements pass.
8. C3 and C10 require human annotations; Table 5 placeholders do not support claims.

## Stop conditions (must remain in config)

- `stop_after_trajectories` / `max_trajectories` ≤ 5
- `max_runtime_minutes` ≤ 30
- `max_steps` / `max_steps_per_instance` capped
- `budget.max_calls` enforced
- `fail_fast: true` recommended

Signed: __________________  Date: __________  Role: __________________
