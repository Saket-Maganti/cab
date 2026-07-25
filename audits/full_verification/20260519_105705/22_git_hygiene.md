# 22 Git Hygiene

## Final requested commands

`git status --short` was run at the end of the audit. The output is large because the worktree was already dirty before this audit. It includes many modified tracked files plus many untracked project assets, configs, docs, data, scripts, tests, and the new audit folder.

Audit-specific paths visible in targeted status:

```text
?? audits/full_verification/20260519_105705/
?? configs/web_shadow_api_stub.yaml
?? configs/web_shadow_web_stub.yaml
?? release/release_manifest.json
?? src/causal_agent_bench/phase2.py
```

`git diff --stat` was run at the end. Because many relevant files are untracked, it only reports tracked-file changes:

```text
99 files changed, 8436 insertions(+), 720 deletions(-)
```

## Commit guidance

No commit was made. Suggested commit message if the audit changes are kept:

`audit: verify CausalAgentBench pipeline and claims integrity`

