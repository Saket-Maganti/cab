# Compact Paper Strategy

## Current Venue Assessment

Current CAB is strongest as an infrastructure/artifact project. It is not ready
for a NeurIPS empirical submission because provider-backed evidence, compact
human validation, and eligible paper assets are absent.

## Current Evidence Boundary

The current repo state is a methods and benchmark-design scaffold only:

- provider/model results: `0`
- completed human validation annotations: `0`
- paper-eligible empirical assets: `0`
- supported C1-C8/C10 claims: `0`
- NeurIPS D&B readiness: `false`

The canonical no-run framing is now `docs/FOCUSED_PROJECT_THESIS.md`, with
claim status in `docs/CLAIM_TRIAGE_NO_RUN.md` and paper wording rules in
`paper/PAPER_WORDING_GUARDRAILS.md`. Empirical claims require future reviewed
Compact-20/50 provider runs, post-run audit, scorer sanity, and human
validation. Until then, the paper remains a methods/benchmark-design scaffold.

## Realistic Compact Paper Path

Position:

> Controlled intervention evaluation for tool-using agents: a compact empirical study.

Best near-term target:

- workshop or COLM-style compact empirical paper after provider pilot, scorer sanity, Compact-20/50 run, and small human validation.

Future path:

- NeurIPS E&D or main-conference path only after larger provider-backed runs, human validation, eligible assets, and submission gate pass.

Submission ladder:

- current no-run state: internal review, proposal, or methods workshop framing only;
- after manual Compact-20 review: reviewed-slice benchmark-design note;
- after tiny provider pilot: provider-integration sanity only;
- after 3-model Compact-20 plus audits: possible compact empirical target;
- after larger runs plus C10 validation: possible NeurIPS D&B path.

See `docs/SUBMISSION_LADDER.md` for the full ladder.

## Evidence Ladder

1. Tiny provider pilot: pipeline/scorer/provider sanity only.
2. Scorer sanity: deterministic scorer versus manual review on real provider outputs.
3. Compact-20: preliminary provider-backed pattern finding.
4. Human validation sample: 30 to 60 reviewed items if enough outputs exist.
5. Compact-50: modest empirical paper candidate if audit passes.
6. Main-scale work later; not part of this upgrade.

## Wording Rules

Allowed now:

- "we introduce"
- "we design"
- "we propose a compact empirical path"

Allowed only after real provider pilot:

- "we provide preliminary evidence"

Allowed only after compact run:

- "compact empirical study"

Forbidden now:

- "we demonstrate"
- "validated benchmark"
- "model rankings"
- "causal proof"
- "general real-world robustness"
- "NeurIPS ready"

## Claim Discipline

Tiny provider outputs, if obtained, support only:

- pipeline sanity,
- scorer sanity,
- provider integration sanity,
- preliminary debugging observations.

They do not support C1-C8, C10, final paper assets, or leaderboard claims.
paper asset eligibility remains false until provider evidence, post-run audit,
and claim gates support the exported table or figure.

## Blocked Provider Pilot / No-API Fallback

Current blocker: the tiny live provider pilot cannot run while `OPENAI_API_KEY`
is unavailable. The repo remains dry-run/preflight-ready only, with
provider-backed evidence at `0`.

With no provider evidence, the strongest honest paper form is methodology,
artifact, or workshop-proposal framing. Dry-run outputs are useful for pipeline
readiness, cost planning, prompt/config inspection, and evidence-governance
checks, but they are not empirical model-performance results.

Manual task/intervention review without model outputs can improve
benchmark-design validity:

- task wording can be clarified,
- high-risk intervention ambiguity can be triaged,
- gold-answer policy can be reviewed,
- compact candidate rows can be excluded before spend.

Manual task review alone does not support model claims, C3 trajectory claims,
C10, model rankings, or NeurIPS readiness. It must be labeled
`engineering_only`, `no_provider_evidence`, and
`not_scientific_model_performance`.

A future approved provider pilot can unlock preliminary empirical evidence only
after live gates pass, the run completes, `allow_paid_calls` is locked back to
`false`, and post-run trajectory/scorer audits are complete. Even then, the tiny
pilot remains provider-integration and scorer-sanity evidence only; C1-C8/C10
promotion remains blocked until the normal claim gates pass.
