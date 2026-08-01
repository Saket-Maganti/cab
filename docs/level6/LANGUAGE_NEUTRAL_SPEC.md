# CAB Language-Neutral Execution and Conformance Specification

Status: Level-6 portability foundation, version 1.

All public objects are UTF-8 JSON. Unknown fields fail validation unless a schema
explicitly permits them. Arrays preserve order; object key order is irrelevant.
Canonical serialization sorts keys, uses no insignificant whitespace, preserves
Unicode, converts negative zero to zero, emits finite numbers with no more than
15 significant digits, and rejects NaN and infinities. Timestamps are RFC 3339,
timezone-aware, and normalized to UTC `Z`. Hashes are lowercase SHA-256 of
canonical UTF-8 bytes unless a field explicitly names Git SHA-1.

Task contracts contain an immutable ID, version, instruction, domain, allowed
tools, artifact commitments, required semantic fact IDs, and response contract.
Intervention contracts contain an ID, family, target, exact mutation, invariants,
route consequences, and scorer-policy binding. Artifact contracts contain an ID,
media type, byte length, digest, visibility, sensitivity, and provenance.

Trajectory events contain an event ID, zero-based step, event type, tool/action
payload, observation payload, UTC timestamp, previous-event hash, and event hash.
Tool results bind the tool, arguments, source artifact, returned fact IDs, and
attempt ID. Errors use stable codes and never rely only on prose.

Scorer input binds task, intervention, trajectory, answer, policies, system
identity, and artifact hashes. Scorer output separates typed answer correctness,
contract compliance, safe response, abstention, clarification, per-attempt
recovery, completion, uncertainty, reason codes, and scorer version.

System identity binds model/provider revision, runtime image, agent/scaffold,
policy, tool registry, dependencies, and redaction policy. Approval receipts,
evidence certificates, and revocations bind exact artifact hashes, issuer keys,
scope, nonce, validity interval, and signatures.

Versions follow explicit schema identifiers. Consumers reject unknown major
versions. Migrations are pure, versioned transformations with before/after
hashes. Errors are structured as `{code, message, path, retryable}`. No error or
missing field may be silently coerced into success.

Golden vectors cover scoring, recovery, abstention, route execution, approval,
resource planning, evidence graphs, certificates, and canonical hashing. The
main implementation and `tools/level6_reference_runner.py` must agree exactly.
Agreement is internal fixture conformance, not an external alternate
implementation reproduction.
