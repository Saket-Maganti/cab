# Protected evaluator hardening report

Foundation state: `PROTECTED_EVALUATOR_HARDENED_PILOT_READY`.

The evaluator now requires digest-pinned images in protected mode, validates
archive bounds and links, enforces a hardened rootless Docker command
(no network, read-only root, dropped capabilities, no-new-privileges, PID/CPU/
memory/output limits, tmpfs, seccomp and mandatory-LSM hook), and audits
structured output for schema violations, prompt leakage and repeated probes.

The trusted boundary includes a one-use encrypted fixture task store, broker
interface, durable approval queue, quotas, immutable receipts and append-only
revocation. Signing is behind signer/verifier protocols. Development HMAC is
visibly fixture-only and rejected in protected mode; optional Ed25519 loads only
from an explicit permission-restricted path. No production private key or
secret is generated or stored.

A benign fixture passed inspection. A development-signed receipt verified,
key v2 was registered and activated, the receipt and key v1 were revoked, and
verification then failed. The deterministic 12-case subprocess classifier test
exercised every attack orchestration path. The real local container campaign
recorded 12 `NOT_EXECUTED` cases because the requested local image/usable
runtime was unavailable; it was not converted into deployment evidence.

Residual pilot work: run the campaign on a provisioned rootless evaluator host,
integrate a production KMS/HSM signer and identity provider, and conduct an
independent protected-evaluator pilot. No such pilot is claimed here.
