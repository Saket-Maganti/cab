# CAB final integrity closure — full validation report

Recorded at `2026-08-05T06:00:59.116975+00:00` against `f63464b97148c3e87cdcf09bd0a6b325e193dff0`.

Provider-free throughout. No provider call was made, no model was run, and
no genuine human review was performed or simulated.

## Tests

| suite | result |
| --- | --- |
| `full provider-free suite (tests/)` | 1505 passed, 1 skipped, 0 failed |
| `skip reason` | tests/test_llm_agents.py:690 — OpenAI integration test requires OPENAI_API_KEY and OPENAI_MODEL_ID; no provider call was made |
| `tests/test_final_integrity_closure.py` | 102 passed (66 hostile attacks + 36 positive and policy tests) |
| `tests/test_review_workflow_integrity.py` | passed |
| `tests/test_reviewer_distribution_patch.py` | passed |
| `tests/test_review_ready_v2.py` | passed |
| `tests/test_review_ready_v2_power_and_freeze.py` | 18 passed |
| `tests/test_pre_run_scientific_hardening.py` | 9 passed |
| `pytest-xdist` | available; the suite was also run with -o addopts='' -p no:randomly for a deterministic count |

## Static, security and policy checks

| check | result |
| --- | --- |
| ruff | All checks passed |
| mypy | Success: no issues found in 298 source files |
| codespell | pass (warnings only, on non-UTF-8 private binary files that are not tracked) |
| scripts/security_check.py | security-check: PASS |
| scripts/run_fast_checks.py | completed, all lanes green |
| scripts/audit_configs.py | PASS (0 issues, 115 pre-existing warnings) |
| scripts/audit_repo_consistency.py | PASS (0 issues, 0 warnings) |
| scripts/check_claim_ledger.py | claim ledger is valid |
| scripts/check_evidence_safety.py | OK (120 live run dirs scanned; C1-C8/C10 mock support blocked) |
| scripts/check_reviewer_proofing.py | passed, 20 attacks documented |
| verify-freeze | CAB_SCIENTIFIC_FREEZE_V2_VALID, mismatched_paths: [] |
| verify-provenance | CAB_GENERATOR_PROVENANCE_PORTABLE |
| active path registry | verified as part of build-reports |
| retired packet and qualification registries | verified as part of build-reports |
| private-material tracking scan (git ls-files private_data) | empty |
| secret-name scan | no key or secret material tracked; matches are documentation and the external-key loader |

## Packaging and reproducibility

| artifact | value |
| --- | --- |
| wheel (build 1) | `ec640d9beb3d30b7fcba057d6061490d97c8c119d5a3305be8703d0ec47029df` |
| wheel (build 2) | `0faa22eb26c19dc2333fa62ede43d9a54d1d1c827ac478fef171e14780ab0c16` |
| sdist (build 1) | `60cdd0292920550f0ac66281e1bc6ed54fd28a8406599745557e63d89d6163e2` |
| sdist (build 2) | `441ec8b91802947b596000fb64f9e24f80dfdf7434382f08d45716be28490aaf` |
| normalized wheel content digest | `90d7f5677bf298128477f411e18afae663bf062559fe37239c23fb90bc14621e` |
| normalized sdist content digest | `7c2774629a1df724a462c98e162365ea12fc7cd508d91fde03e0a579d3cd5179` |
| normalized contents reproduce | True |
| `twine check` | PASSED for both artifacts |

Raw archive hashes differ between builds because zip and tar embed
modification times. The *contents* are byte-identical, which is what
reproducibility means here; the normalized digests above are the
comparable values.

## Hostile audit

- attacks attempted: **66**
- rejected: **66**
- falsely accepted: **0**
- status: **CAB_HOSTILE_INTEGRITY_AUDIT_PASSED**

## Current scientific state

```text
genuine human judgments: 0
genuine adjudications: 0
genuine model trajectories: 0
paper-eligible empirical assets: 0
supported empirical claims: 0
C10: pending genuine review
model execution: blocked
```
