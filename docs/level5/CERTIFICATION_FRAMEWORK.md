# Certification framework

Certificate types cover task validity, split integrity, run integrity, scorer
audit, analysis reproducibility, model robustness profile, paper-asset
eligibility and release reproducibility.

Each certificate records a version, subject, issuer, evidence node IDs/classes,
time, deterministic ID and signature interface. Development fixtures use an
explicit development key. Production certificates require external key
management and protected signing operations.

A certificate asserts only that its declared integrity contract passed. It is
not itself a scientific claim. Claim promotion additionally requires the
complete paper-eligible evidence subgraph and claim-ledger policy.
