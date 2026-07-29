# CAB CPU First-Half Ledger

Times and memory are local Apple M4 measurements. Commands executed in parallel
overlap in wall time. Peak RSS is the largest `/usr/bin/time -l` value observed.

| Stage | Operation | Result | Real time | Peak RSS |
|---|---|---|---:|---:|
| H1 | CAB doctor | PASS | 0.66 s | 60.5 MiB |
| H1 | Initial registry verify | expected missing local state | 0.58 s | 58.3 MiB |
| H1 | Registry init | PASS, schema 3 | 0.37 s | 60.8 MiB |
| H1 | Registry verify/doctor/version/migration | PASS | 0.51 s measured primary command | 59.8 MiB |
| H1 | Hardening gate | PASS | 0.58 s | 58.3 MiB |
| H1 | Strict docs | PASS | 1.57 s | 59.5 MiB |
| H1 | Review readiness | PASS | 0.51 s | 58.9 MiB |
| H1 | Artifact-store verify | PASS, zero objects | 0.49 s | 58.2 MiB |
| H1 | Standalone fixture graph verify | expected absent artifact | 0.50 s | 58.0 MiB |
| H2 | Compact-20 human/C10 validation | expected exit 2; zero rows | 2.59 s | 195.6 MiB |
| H2 | Protected packet static audit | PASS after path-correct launch | 12.89 s | 180.1 MiB |
| Validation | Ruff | PASS | 0.71 s | 18.9 MiB |
| Validation | mypy | PASS | 0.97 s | 64.8 MiB |
| Validation | Codespell | PASS | 0.79 s | 38.0 MiB |
| Validation | Security/config/structured/import/evidence | PASS | 21.84 s | 187.0 MiB |
| Validation | Focused suite | 131 passed | 10.83 s | 361.2 MiB |
| Validation | Full provider-free suite | 1,171 passed, 1 skipped | 197.81 s | 4.80 GiB |
| Validation | Build/release group | PASS | 27.2 s group wall | within host policy |

The first protected-packet launch failed in 0.45 s because direct script
execution did not expose the repository package path. Retrying with
`PYTHONPATH=.` passed; no source or evidence was changed.

Measured subprocess CPU is at least `0.122 CPU-hours`; this is a conservative
lower bound because several grouped secondary commands were not individually
timed. The measured critical-path validation wall time was approximately
`283.4 seconds`, excluding inspection and report authoring.
