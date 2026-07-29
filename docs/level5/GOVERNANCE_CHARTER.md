# CAB governance charter

Maintainers steward releases, schemas and security. Scientific reviewers own
validity decisions; security reviewers own evaluator release blockers;
contributors own provenance and licensing for their submissions. A person with
a declared conflict does not make the final decision on that item.

Benchmark, intervention, scorer, backend, adapter, analysis and documentation
contributions follow versioned templates and automated validation. None may
bypass C10, evidence transitions, protected-data boundaries or release gates.

CAB publishes supported versions, release cadence, migration notes and
end-of-life dates. Security reports use private disclosure where necessary.
Privacy, attribution and consent obligations survive task retirement.

A release requires the provider-free suite, line-coverage gate, strict docs,
package checks, security scans, red-team campaign and hardened foundation gate.
A plugin or benchmark contribution cannot override these checks.

Credible contamination moves the affected task version to `CONTAMINATED`,
blocks dependent claims and triggers a versioned replacement. Retirement never
deletes evidence or correction history. Authors and reviewers may appeal with
new evidence; a conflicted decision-maker cannot decide the appeal.

Do not file protected payloads, credentials, reviewer identities or evaluator
escape details in a public issue. Use private disclosure, preserve artifacts by
hash, revoke affected keys and receipts, and publish a redacted correction
after containment.
