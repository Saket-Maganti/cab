# Manifest-Driven Resource Planning

Acceptance: `CAB_MANIFEST_DRIVEN_RESOURCE_PLANNER_READY`.

Every count below is derived from a frozen public manifest. Manual totals that
disagree raise `STALE_MANUAL_TOTAL`.

| Study | Scenario | Trajectories | Shards | Storage GiB | GPU hours |
|---|---|---:|---:|---:|---:|
| `compact20` | `minimum` | 36 | 1 | 0.003296 | 0.072 |
| `compact20` | `planned` | 216 | 1 | 0.019775 | 0.432 |
| `compact20` | `conservative` | 324 | 1 | 0.029663 | 0.648 |
| `compact20` | `rerun_reserve` | 260 | 1 | 0.023804 | 0.52 |
| `compact20_raac_light` | `minimum` | 36 | 1 | 0.003296 | 0.072 |
| `compact20_raac_light` | `planned` | 432 | 1 | 0.039551 | 0.864 |
| `compact20_raac_light` | `conservative` | 648 | 1 | 0.059326 | 1.296 |
| `compact20_raac_light` | `rerun_reserve` | 519 | 1 | 0.047516 | 1.038 |
| `raac_ablations` | `minimum` | 600 | 1 | 0.054932 | 1.2 |
| `raac_ablations` | `planned` | 81000 | 33 | 7.415771 | 162.0 |
| `raac_ablations` | `conservative` | 108000 | 44 | 9.887695 | 216.0 |
| `raac_ablations` | `rerun_reserve` | 97200 | 39 | 8.898926 | 194.4 |
| `raac_equal_budget` | `minimum` | 600 | 1 | 0.054932 | 1.2 |
| `raac_equal_budget` | `planned` | 18000 | 8 | 1.647949 | 36.0 |
| `raac_equal_budget` | `conservative` | 24000 | 10 | 2.197266 | 48.0 |
| `raac_equal_budget` | `rerun_reserve` | 21600 | 9 | 1.977539 | 43.2 |
| `scale100` | `minimum` | 600 | 1 | 0.054932 | 1.2 |
| `scale100` | `planned` | 9000 | 4 | 0.823975 | 18.0 |
| `scale100` | `conservative` | 12000 | 5 | 1.098633 | 24.0 |
| `scale100` | `rerun_reserve` | 10800 | 5 | 0.98877 | 21.6 |
| `scale100_raac_light` | `minimum` | 600 | 1 | 0.054932 | 1.2 |
| `scale100_raac_light` | `planned` | 18000 | 8 | 1.647949 | 36.0 |
| `scale100_raac_light` | `conservative` | 24000 | 10 | 2.197266 | 48.0 |
| `scale100_raac_light` | `rerun_reserve` | 21600 | 9 | 1.977539 | 43.2 |
| `transfer` | `minimum` | 360 | 1 | 0.032959 | 0.72 |
| `transfer` | `planned` | 5400 | 3 | 0.494385 | 10.8 |
| `transfer` | `conservative` | 7200 | 3 | 0.65918 | 14.4 |
| `transfer` | `rerun_reserve` | 6480 | 3 | 0.593262 | 12.96 |

The matrix also records clean/intervention instances, models, policies,
repeats/seeds, expected files, storage, GPU hours, CPU merge/scoring hours, and
bootstrap replicate cells. Commands: `cab plan volume`, `cab plan resources`,
and `cab plan shards`.
