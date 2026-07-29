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

## Durable application

The hardened service stores users, sessions, assignments, drafts, judgments,
adjudications, amendments and audit events in SQLite. The database directory
must have no group or world access.

Production deployment must connect an external identity provider. The bundled
adapter accepts only `local-development:<user-id>` assertions and produces
fixture evidence. Reviewers and adjudicators must consent, attest that they are
the direct human, and attest that no AI or proxy will perform the review.
Sessions use random tokens and CSRF tokens; only hashes are stored. Cookies are
HttpOnly, SameSite=Strict and rotated.

Administrators assign at least two independent qualified reviewers per item.
Reviewers may autosave, declare a conflict or submit one immutable judgment.
Disagreement requires an independent adjudicator. Corrections require an
administrator amendment request and a replacement that names the superseded
judgment; the original remains immutable.

The web UI renders reviewer queues, judgment forms, adjudication and
administrator coverage/workload/agreement views. Request sizes are bounded and
responses carry no-store, CSP, frame-denial, referrer and content-type
protections. Client-supplied role headers have no authority.

Public export hashes item and reviewer identities and omits notes. Fixture
judgments remain excluded from genuine C10 counters. Back up the SQLite file
before pilot milestones and restore only to a newly verified path.
