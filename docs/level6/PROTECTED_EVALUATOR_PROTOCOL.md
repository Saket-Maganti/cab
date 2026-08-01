# Protected Evaluator Challenge and Appeals Protocol

A submission binds an encrypted payload digest, signature, system identity,
budget, confidentiality terms, and replay nonce. Execution occurs in a protected
runtime with least privilege, immutable input commitments, rate limits, network
policy, resource accounting, and redacted logs.

The run receipt binds the submission, protected task-set commitment,
environment, result attestation, replay audit, and rate-limit bucket. Results may
be challenged or appealed with evidence hashes. Corrections and revocations
preserve the original receipt and require signed final decisions. Confidentiality
does not suppress material scientific or security corrections.

Committed demos are fixtures only and do not count as protected evaluator or
community pilots.
