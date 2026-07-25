# Documentation Archive, Deprecation, and Relocation Plan

Status: plan only. No file was deleted, moved, or reclassified as evidence by
this audit. The worktree contains user-owned changes, so relocation requires a
separate reviewed change.

## Active surface

`docs/CAB_FOCUSED_PROJECT_SURFACE.md` is the canonical short index. Keep these
families active:

- repository and documentation entry points;
- scorer, metric, split, provenance, and human-review contracts;
- evidence, claims, security, privacy, licensing, and release policies;
- current execution handbooks and gate outputs;
- records required to reproduce a frozen dataset or audited run.

## Deprecate in place before relocating

Add a visible `Status: superseded` header and a link to the replacement before
any move. Candidates include:

| Candidate family | Replacement/authority | Proposed destination |
|---|---|---|
| Repeated dated readiness/status reports | Current canonical gate and current-state report | `docs/archive/status_snapshots/` or `archive/reports/status_snapshots/` |
| Superseded prompt-pack plans | Implemented source, tests, and current handbook | `archive/promptpacks/` |
| Redundant venue/paper strategy variants | Selected paper plan plus claim ledger | `docs/archive/paper_strategy/` |
| Mock reviewer packets superseded by genuine review | Audited human-review packet | `docs/archive/mock_review/` |

These are candidates, not completed moves.

## Never delete

- claim-ledger history and evidence classifications;
- approval, budget, and risk acknowledgements;
- human-review source packets, adjudication records, and templates;
- freeze manifests, run manifests, hash ledgers, and release manifests;
- reports documenting blockers, failed gates, or past public claims;
- license, privacy, security, and provenance records.

## Relocation procedure

1. Freeze the active-surface index and capture a clean reference inventory.
2. Identify inbound Markdown, code, configuration, and paper references.
3. Add a supersession header and replacement link at the old path.
4. Obtain explicit maintainer approval for the proposed mapping.
5. Use a history-preserving move; do not rewrite scientific evidence.
6. Repair references and regenerate the release manifest.
7. Run `make max-ceiling-ci-serial` and the repository consistency audit.
8. Preserve a relocation ledger with old path, new path, reason, approver, and
   effective version.

## Release rule

The public bundle may omit internal planning documents, but it must retain every
file named by the release manifest and all evidence, license, privacy, and
provenance records needed to interpret included artifacts.
