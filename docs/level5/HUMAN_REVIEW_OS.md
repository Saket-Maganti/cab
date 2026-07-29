# Human review OS

The review system provides qualified reviewer schemas, privacy-safe IDs,
conflict/expertise disclosure, consent, compensation disclosure, blind balanced
assignment, immutable judgments, logged amendments, confidence/time fields and
separate adjudication.

`cab review serve` starts a local-only versioned HTTP service with an append-only
JSONL ledger. Non-local binding is rejected. Submitted judgment IDs are
immutable, role headers are required, payloads are bounded and responses carry
no-store and content-security headers.

Agreement reporting includes raw agreement, Wilson intervals, Cohen's kappa,
nominal Krippendorff alpha, prevalence, time anomalies and straight-line flags.
Metrics trigger review; none alone auto-rejects a reviewer.

C10 rejects missing rows, fixture rows, AI/proxy attestations, incomplete
coverage, invalid contracts and unresolved disagreements.
