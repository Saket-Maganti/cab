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

The three full-suite failures were deterministic and shared one cause: the
release manifest had not yet inventoried the new docs, scripts and source
modules. No runtime or scientific test failed. The manifest is regenerated
only after source stabilisation, followed by the affected checks and complete
suite.

Final packaging, release checks, clean-room container availability, unified
gate, push/SHA equality and remote CI are appended after the final committed
source and reports exist.
