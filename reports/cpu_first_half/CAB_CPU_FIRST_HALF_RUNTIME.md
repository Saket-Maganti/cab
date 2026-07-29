# CAB CPU First-Half Runtime

Host: Apple M4, 10 logical CPUs, 16 GiB memory, Python 3.11.9.

## Measured summary

- Critical-path validation wall time: approximately `283.4 s`
- Conservative measured subprocess CPU lower bound: `0.122 CPU-hours`
- Peak recorded RSS: `4.80 GiB` during the four-worker full suite
- Full suite: `197.81 s` real, `342.64 s` user, `39.18 s` system
- Focused suite: `10.83 s` real, `19.58 s` user, `3.70 s` system
- Human/C10 validation: `2.59 s`, peak RSS `195.6 MiB`
- Protected-packet static validation: `12.89 s`, peak RSS `180.1 MiB`
- Build/release parallel group: `27.2 s` wall

No bootstrap, rescoring, merge, Compact analysis, or GPU import was run, so
there are no fabricated resource measurements for CPU-H3 through CPU-H10.

The one retry was a path-correct launch of the protected-packet validator.
There were no scientific retries, dropped runs, or evidence mutations.
