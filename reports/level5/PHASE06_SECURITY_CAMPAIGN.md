# Phase 06 security campaign

Malicious fixtures cover private prompt echoes, filesystem enumeration,
score-oracle probing, encoded dumps, hard-coded task IDs, archive traversal and
receipt tampering. Docker command tests enforce network none, read-only root,
non-root user, all capabilities dropped, no-new-privileges, process/memory/CPU
limits, tmpfs and a read-only private task mount.

The mock evaluator receipt passed and verified with a marked development key.
No real private task or production secret was used.

Acceptance: `CAB_PROTECTED_EVALUATOR_FIXTURE_READY`. A production-like security
pilot remains required.
