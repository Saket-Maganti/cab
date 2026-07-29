# CAB ICLR Complete CPU Execution Report

## Executive Summary

Status: `CAB_CPU_EXECUTION_COMPLETE_WITH_EXPECTED_HUMAN_BLOCK`

CPU-00 through CPU-14 were executed in order. Every legal CPU validation
finished successfully after narrow repairs or corrected command expectations.
Expected human/evidence gates remained closed. The final unified state is
`HUMAN_VALIDATION_REQUIRED` with `build_complete=true` and exit code 2.

No model, GPU, provider, or human-evidence stage ran. Git publication details
are recorded in `reports/CAB_CPU_GITHUB_PUBLISH.md`.

## Environment

| Item | Value |
|---|---|
| Mac | Mac16,13; Apple M4 |
| Memory / logical CPUs | 16 GiB / 10 |
| OS | macOS 26.5.2 arm64 |
| Python / pytest | 3.11.9 / 9.0.2 |
| Ruff / mypy / Codespell | 0.15.8 / 2.1.0 / 2.4.2 |
| Baseline free disk | 81.86 GiB |
| Repository footprint | 1.88 GiB |

## Command Ledger

| Stage | Final command/result | Seconds | Peak child RSS MiB | Exit | Reruns |
|---|---|---:|---:|---:|---:|
| CPU-00 | unified gate: expected human block | 54.831 | 1,875.4 | 2 | 1 |
| CPU-01 | `make fast-check` | 63.760 | 620.2 | 0 | 1 |
| CPU-02 | 142 focused tests passed | 68.955 | 2,562.7 | 0 | 0 |
| CPU-03 | Ruff, mypy, Codespell, diff check passed | 1.083 | 62.2 | 0 | 2 narrow |
| CPU-04 | 372 structured files + config/split checks | 1.879 | 233.6 | 0 | 0 |
| CPU-05 | security, leakage, release, 27 tests | 74.104 | 833.5 | 0 | 0 |
| CPU-06 | blank human/C10 gate + 23 tests | 3.358 | 330.7 | 2 expected | 0 |
| CPU-07 | private aggregate audit + 25 tests | 15.082 | 225.3 | 0 | 0 |
| CPU-08 | M4 resource preflight | 0.323 | 29.0 | 0 | 0 |
| CPU-09 | nine notebook fixtures / 72 receipts | 0.452 | 44.3 | 0 | 0 |
| CPU-10 | 62 analysis tests + 1,000 bootstrap | 5.611 | 359.7 | 0 | 4 harness corrections |
| CPU-11 | paper, claims, assets | 2.638 | 52.2 | 0 | 1 expectation correction |
| CPU-12 | full provider-free suite | 176.326 | 6,675.4 | 0 | 0 |
| CPU-13 | release/reproducibility gates | 62.0 | 471.3 | 0 | 1 |
| CPU-14 | final unified gate | 52.853 | 3,192.8 | 2 expected | 0 |

Peak RSS is the maximum aggregate child-process value reported by the
recording wrapper. APFS free-space deltas were noisy: the session observed
about 7.7 GiB less free space at the end, mostly during parallel test/cache
activity, while the repository inventory remained about 1.88 GiB. No raw
evidence or cache was deleted.

## Validation Summary

- Focused scientific-safety regression: 142 passed.
- Full provider-free suite (`-n4`): 1,091 passed, 1 skipped, 0 failed in
  175.59 seconds.
- Additional focused lanes: 27 security/release, 23 human-packet, 25 private
  candidate, 62 fixture-analysis, and 29 final reproducibility tests passed.
- Ruff: pass. mypy: pass across 205 source files. Codespell: pass.
- Structured data: 372/372 tracked JSON, JSONL, YAML/YML, and notebooks passed.
- Security: 0 errors, 0 warnings; tracked private payloads: 0.
- Leakage gate: pass with 0 internal blockers.
- Private candidates: 100 Scale-100 and 60 naturalistic tasks passed aggregate
  structural validation; human validity remains pending.
- Notebooks: 9/9 passed offline; 72 fixture receipts; live execution refused.
- Paper: 14 pages; seven empirical placeholders retained; claim and
  bibliography gates passed.
- Release bundle: 654 files; hash
  `42d1fa2275910f56d92f8df6f58fa40cb44bf6cd3994a753b50909fd2869045e`.
- Artifact prerequisite check: pass after installing the declared editable dev
  package.

## Runtime and Bottleneck Analysis

The full suite was the slowest stage at 176.3 seconds, followed by the
security/leakage group (74.1 seconds), focused serial suite (69.0 seconds),
fast-check (63.8 seconds), and each unified readiness evaluation (52.9–54.8
seconds). Readiness is expensive because it recomputes live inventories,
paper eligibility, run indexing, leakage state, and release state.

Notebook fixtures (0.45 seconds), paper compilation (2.19 seconds), and the
1,000-replicate tiny fixture bootstrap (0.35 seconds) are not bottlenecks.
Duplicate work is concentrated in repeated security, release, paper, and
readiness subchecks. Release-hash regeneration itself costs about 0.4 seconds.

## Resource Analysis and M4 Recommendations

- `-n4` is stable for the full provider-free suite on this 16 GiB M4.
- Use `-n4` for tests when at least 8 GiB is free; use `-n2` for concurrent
  workloads or memory pressure; use serial mode for readable failure diagnosis.
- Keep the resource preflight's conservative two-worker mode for future
  trajectory processing.
- Use four bootstrap shards of 250 for pilot work and resumable disjoint ranges
  for final work.
- Keep at least 20 GiB free before scientific execution.
- Retain raw evidence and validated hashes; only prune reproducible fixture,
  historical audit, and tool caches after review.

Future CPU forecasts (`PROJECTED_FROM_CURRENT_MEASUREMENTS`, not measurements):

| Future lane | Projected CPU time |
|---|---:|
| Compact-20 postrun merge, score, audit, analysis | 5–15 min |
| Scale-100 postrun processing | 25–60 min |
| Naturalistic postrun processing | 15–40 min |
| Final 10,000-replicate bootstrap | 1–5 min plus I/O |
| Final paper-asset generation/validation | under 5 min |

These ranges scale the measured fixture and test costs and remain subordinate
to future immutable manifest sizes. GPU/model runtime estimates in the M4
preflight remain `ESTIMATE_NOT_MEASURED`.

## Repairs

1. Added a durable CPU command recorder and registered both new scripts in the
   canonical release manifest.
2. Fixed import ordering and `datetime.UTC` usage in the recorder.
3. Added tracked structured-data validation with a public-safe JSON report.
4. Installed the repository's declared editable dev package so the canonical
   artifact prerequisite check could import the package.
5. Corrected harness expectations for the Codespell entry point, draft paper
   asset warnings, and bootstrap result-field assertions. These were command
   harness corrections, not scientific-code changes.

No tests or evidence gates were weakened.

## Scientific State

| Genuine evidence | Count |
|---|---:|
| Human review rows | 0 |
| Real model trajectories | 0 |
| Audited real runs | 0 |
| Paper-eligible empirical assets | 0 |
| Supported empirical claims | 0 |

No provider call, local model inference, GPU work, human judgment fabrication,
claim promotion, or fixture-to-paper promotion occurred.

## Deferred Work

Slice locking and frozen manifest generation wait on genuine human review and
C10. Compact-20 postrun processing waits on real GPU outputs. Scale-100,
naturalistic, RAAC, and final confirmatory analyses wait on audited study
outputs. Paper-eligible export and final empirical release wait on all
claim-specific evidence gates. Exact command templates and prerequisites are
in `reports/CAB_CPU_DEFERRED_RUNS.md`.

## Exact Next Action

Have two independent qualified human reviewers complete the locked Compact-20
review packet.

## Files Changed

The commit contains this report, the required CPU reports and ledgers, the CPU
recorder, structured-data validator, refreshed release metadata, and the
canonical fail-closed human-gate output. Preserved user-owned Prompt 1 and
prompt-pack paths remain unstaged.

## Git Publication

Repository: `Saket-Maganti/cab`; branch: `main`; force push: no. Final local
and remote SHA verification and bounded CI status are recorded in
`reports/CAB_CPU_GITHUB_PUBLISH.md` and the task's final response.
