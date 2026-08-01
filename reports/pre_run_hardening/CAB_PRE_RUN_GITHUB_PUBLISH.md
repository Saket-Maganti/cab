# CAB Pre-Run GitHub Publication

Status: `DIRECT_MAIN_PUBLICATION_COMPLETE`.

Baseline SHA: `c8b0d008a02f4bcc36a24635a1357d4210e073fd`.

The task-owned implementation was published directly to `main` without force
in these commits:

- `3c883cb` — Repair CAB scientific scoring semantics
- `3a3a275` — Rebuild CAB pre-review and confirmatory designs
- `9f773f36639fa0d584362a63be4a6e116cbef2b0` — Finalize CAB pre-run scientific hardening

Local and remote `main` were equal at the implementation tip
`9f773f36639fa0d584362a63be4a6e116cbef2b0`. The corrective publication commit
containing this record refreshes the 745-file release bundle to
`0a0fdc6eda105986eab68933fba1eb33ca405d29247b2295035b0f60e6ebd043`;
because a commit cannot embed its own future SHA, its exact verified branch-tip
SHA is recorded in the external final handoff.

## Bounded CI observation

At the first published implementation tip, the new `Pre-run scientific
hardening` workflow passed. `Batch smoke`, `Docs Check`, `Claim Safety`, and
`Level-5 foundation` also passed. The max-ceiling workflow correctly found the
stale release hash described above; its exact 115-test serial slice passed
locally after regeneration. The separate Pages-deployment workflow failed with
GitHub API 404 because Pages is not enabled for the repository; its MkDocs build
and the independent `Docs Check` workflow passed. Active workflows were never
reported as green. The corrective tip receives a new bounded observation in the
external final handoff.

Only task-owned paths were committed. Pre-existing user-owned status, audit,
environment, paper-eligibility, prompt-pack, and baseline-report changes remain
unstaged.
