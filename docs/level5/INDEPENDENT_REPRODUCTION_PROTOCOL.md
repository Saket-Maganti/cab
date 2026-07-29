# Independent reproduction protocol

An independent reproducer installs CAB in a clean environment, verifies the
published source/environment hashes, retrieves public-safe artifacts, runs the
declared live arm or fixture as applicable and regenerates selected tables.
They report environment, commands, matched hashes, numerical tolerances,
discrepancies and a signed attestation.

The original authors may coordinate and resolve discrepancies but cannot
self-attest this gate. The internal `cab reproduce` command proves only fixture
plumbing and emits `independent_reproduction=false`.

Private reproducer identity and contact information remain outside Git. Public
reports use a consented pseudonym or organizational attestation.
