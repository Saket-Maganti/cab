# CAB Level-5 hardening validation ledger

Captured on 2026-07-29. Provider, model and paid local-run markers were
excluded. No protected payload or production signing secret was used.

| Validation | Result |
|---|---|
| Focused Level-5 tests, parallel, excluding slow | 77 passed in 4.47 s |
| Complete Level-5 suite with coverage | 79 passed in 25.19 s |
| Level-5 line coverage gate | 87.68% overall; all critical modules ≥91.12% |
| Ruff | passed |
| mypy, whole configured package | 224 source files, no issues |
| Codespell | passed |
| MkDocs strict | passed, zero warnings, 1.05 s build |
| Scheduler mandatory campaign | passed, 4,000 aggregate executions |
| Five-point crash consistency | 5/5 passed, zero duplicate commits |
| Physical fault campaign | 18/18 passed |
| Red team | 22/22 classified, zero unmitigated, zero critical |
| Clean archive/venv/checkout preliminary | passed; three hashes agree |
| Real evaluator containers | 0 executed, 12 honestly `NOT_EXECUTED` |
| Full provider-free suite, first post-change run | 1,167 passed, 1 skipped, 3 release-inventory failures |
| Release-inventory regression slice after regeneration | 3 passed |
| Final full provider-free suite in isolated clean clone | 1,167 passed, 4 skipped in 165.74 s |
| Package build and Twine metadata | wheel and sdist passed |
| Release check and dry-run | passed; 720 files |
| Final clean archive/venv/checkout | passed from `1a810a0`; zero discrepancies |
| Unified Level-5 hardening gate | `CAB_LEVEL5_HARDENED_FOUNDATION_READY` |
| Remote Level-5 matrix | 8/8 jobs passed |
| Remote standard CI | 5/5 jobs passed |
| Remote supporting workflows | Claim Safety, Docs Check, Max Ceiling and Fast Check passed |

The three full-suite failures were deterministic and shared one cause: the
release manifest had not yet inventoried the new docs, scripts and source
modules. No runtime or scientific test failed. The manifest is regenerated
only after source stabilisation, followed by the affected checks and complete
suite.

The corrected implementation commit
`1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1` matched `origin/main` when these
remote checks ran. The separate GitHub Pages build succeeded, but deployment
returned HTTP 404 because Pages is not enabled for this repository. Container
clean-room and malicious-evaluator execution remain honestly `NOT_EXECUTED`
because a usable local daemon/image was unavailable.
