# CAB Level-5 decision log

## D001 — Extend canonical systems

The existing metrics, RAAC, scoring, run and safety systems remain canonical.
The Level-5 package provides control-plane contracts and does not redefine
scientific estimands.

## D002 — Local-first storage

SQLite and a filesystem CAS are supported defaults. Protected payloads and
reviewer identity maps remain separate from both Git and public registry rows.

## D003 — Fixture evidence is structurally isolated

Fixture runs, reviews, evaluator receipts, red-team campaigns and certificates
remain `FIXTURE_ONLY`. C10 and claim promotion reject them.

## D004 — No live execution

No model/provider execution was initiated. Phase 12 prerequisites are absent:
genuine C10, slice lock and explicit live approval.

## D005 — No false external claims

The internal reproduction receipt says `independent_reproduction=false`.
Evaluator and community pilot counts stay zero.

## D006 — Preserve user work

Three pre-existing untracked paths under `promptpacks/` and `reports/` are
excluded from staging and modification.

## D007 — Release state is computed, not declared

`CAB_LEVEL5_COMPLETE` requires every real count and external gate. Source code
or fixtures alone can produce only the platform-foundation state.
