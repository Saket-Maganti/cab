# Phase 09 internal reproduction fixture

The provider-free command validates registry, benchmark compilation, a 20-unit
interrupt/resume run, CAS integrity, all 18 chaos cases, evaluator receipt,
evidence graph and certificate.

Observed fixture receipt:

- passed: true;
- interrupted at 7: true;
- resumed to 20: true;
- independent reproduction: false;
- evidence: fixture only.

Acceptance: internal plumbing only, not `INDEPENDENTLY_REPRODUCED`.
