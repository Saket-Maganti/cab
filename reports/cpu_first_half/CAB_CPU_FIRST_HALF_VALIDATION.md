# CAB CPU First-Half Validation

## Tests

```text
Focused human/C10/split/merge/scoring/statistics/evidence/claim suite:
131 passed

Full provider-free suite:
1171 passed, 1 skipped
```

The skipped test was retained as reported; no skip was converted into a pass.

## Static, security, and data

- Ruff: PASS
- mypy: PASS, 224 source files
- Codespell: PASS
- Tracked structured data: PASS, 399/399
- Security and production-secret scan: PASS
- Evidence safety: PASS across all live result directories
- Protected private-candidate public-surface scan: PASS, zero fragment matches
- Private roots ignored: PASS
- Package import: PASS, seven required modules
- Unsafe archive handling: PASS in focused/full evaluator and protected-heldout tests
- `git diff --check`: deferred until final task-owned diff, then recorded in the publish report

The persisted run index was stale, but the live scan included every result
directory and found no unindexed run that would classify as paper eligible.
The index was not regenerated because it is outside this task's evidence
boundary.

## Documentation and release

- `mkdocs build --strict`: PASS
- Python sdist/wheel build: PASS
- release check: PASS
- release dry run: PASS
- Level-5 hardening gate: PASS with expected scientific blockers

## Scientific validation

The genuine counters remain exactly zero. C10 is pending, Compact-20 is not
locked, no GPU shard was imported, and no empirical analysis or Scale decision
was produced.
