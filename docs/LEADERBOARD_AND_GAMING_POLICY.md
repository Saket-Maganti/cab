# Leaderboard and Gaming Policy

**Leaderboard is not yet active.** This policy applies before any public leaderboard launch.

## Why gaming is a risk

Agents can overfit to synthetic tool patterns, exploit heuristic scorers, or tune on dev splits. Public leaderboards without held-out discipline invite score chasing without robustness gains.

## Splits

- **Public/dev:** May be used for development and ablations — not for headline claims.
- **Test:** Primary ranking split after freeze; access controlled until benchmark v1.0 release.
- **Held-out templates:** Template IDs never seen during generator development; required for generalization claims.

## Reporting requirements

Submissions must disclose:

1. Model name + snapshot/date
2. Provider endpoint
3. Full prompt template hash
4. Tool descriptions version
5. Temperature, max tokens, retries
6. Cost and latency (median + p95)
7. Contamination declaration (training data overlap statement)

## Prohibited tuning

- Training on test instance text or gold sequences
- Manual per-instance prompt editing on test split
- Oracle/tool-hiding exploits
- Merging incomplete runs into reported aggregates

## Required disclosures

See templates:

- [docs/templates/MODEL_RUN_CARD_TEMPLATE.md](templates/MODEL_RUN_CARD_TEMPLATE.md)
- [docs/templates/AGENT_CARD_TEMPLATE.md](templates/AGENT_CARD_TEMPLATE.md)
- [docs/templates/RUN_CARD_TEMPLATE.md](templates/RUN_CARD_TEMPLATE.md)

## Contamination

Run `audit-contamination` before accepting external submissions. Flag near-duplicate templates and canary leakage.

## Current status

| Item | Status |
|---|---|
| Public leaderboard | **Not active** |
| Test split frozen | pilot_v0.1 frozen |
| External submissions | Not accepted |
| Gaming review process | Documented only |

## Related

- [docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md](DATASET_VERSIONING_AND_RELEASE_POLICY.md)
- [docs/EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md)
