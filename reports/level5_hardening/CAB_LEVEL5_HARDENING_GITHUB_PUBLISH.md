# CAB Level-5 hardening GitHub publication

Captured on 2026-07-29.

## Publication

Changes were pushed directly to `main` without force:

| Commit | Purpose |
|---|---|
| `d1819b0b213c696c4fa0c4982ae0dc5fbae894b7` | Harden CAB Level-5 operational foundation |
| `6eb3bed9ba6ee692fbea15ae9587af9d6aecfb93` | Complete CAB Level-5 production-readiness pass |
| `1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1` | Stabilize plugin timeout contract on macOS |

At validation time, local `HEAD` and `refs/heads/main` on `origin` both resolved
to `1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1`. The report-bearing documentation
commit is intentionally verified after it exists rather than trying to embed a
self-referential SHA in its own contents.

## Remote workflow evidence

The corrected implementation commit was observed on GitHub:

| Workflow | Run | Result |
|---|---:|---|
| Level-5 foundation | [30444796169](https://github.com/Saket-Maganti/cab/actions/runs/30444796169) | passed, 8/8 jobs |
| Claim Safety | [30444796117](https://github.com/Saket-Maganti/cab/actions/runs/30444796117) | passed |
| Docs Check | [30444796116](https://github.com/Saket-Maganti/cab/actions/runs/30444796116) | passed |
| Max Ceiling Provider-Free Gates | [30444796113](https://github.com/Saket-Maganti/cab/actions/runs/30444796113) | passed |
| Fast Check | [30444796115](https://github.com/Saket-Maganti/cab/actions/runs/30444796115) | passed |
| CI | [30444796161](https://github.com/Saket-Maganti/cab/actions/runs/30444796161) | passed, 5/5 jobs |

The Level-5 workflow passed supply-chain and hardening-quality jobs plus the
complete operating-system/runtime matrix:

- Ubuntu with Python 3.11, 3.12, and 3.13;
- macOS with Python 3.11, 3.12, and 3.13.

The standard CI workflow passed lint/type/spelling, release/paper/artifact
gates, and full tests on Python 3.11, 3.12, and 3.13. The Security audit for
the implementation pass also completed successfully in
[run 30444302216](https://github.com/Saket-Maganti/cab/actions/runs/30444302216).

The first implementation run exposed one macOS timeout-fixture failure. Its
50 ms scheduling margin was widened while preserving the production 100 ms
timeout contract; the corrected six-platform matrix passed.

The first report-bearing run later exposed a separate xdist race: the maximum
ceiling file inventory enumerated a temporary coverage shard after coverage
had removed it. The inventory now stats each path once and omits only paths
that disappear during the snapshot; a deterministic regression test covers
that lifecycle. The final fix commit and its remote checks are recorded by Git
history and the final handoff response because a committed report cannot embed
its own SHA.

## GitHub Pages boundary

The strict documentation build and Docs Check are green. The separate `Docs`
deployment workflow built and uploaded the site successfully at implementation
commit `6eb3bed`, but `actions/deploy-pages` returned HTTP 404 because GitHub
Pages is not enabled for the repository. The repository workflow itself
documents the required owner action: enable Pages and select GitHub Actions as
the source. No repository setting was changed implicitly, and the deployment
failure is not reported as a documentation-build pass.

## Safety

The three baseline user-owned untracked paths were not staged. Protected
payloads, production signing secrets, generated private review data, and real
provider outputs were not published.
