# Intervention compiler specification

An intervention is valid only when it introduces exactly one controlled
mechanism and preserves the answer-contract target hash. The compiler validates
the tool schema, manipulation check, expected opportunity and role separation
before producing an instance.

Identifiers are SHA-256-derived from canonical base/intervention objects. The
receipt records the base hash, intervention hash, public hash, optional private
hash and compiler version. Recompiling the same inputs produces the same
instance and content hashes; the timestamp is informational.

Private fields never enter the public instance. Protected payloads may be
written only when the caller explicitly selects a private output directory
outside Git.
