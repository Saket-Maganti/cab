# Benchmark factory and plugin hardening report

Status: passed.

Benchmark authoring is bounded to 1 MiB, depth 16 and 10,000 nodes. YAML aliases
and multi-document inputs are rejected; tool schemas reject external
references and excessive complexity. Compilation validates scorer,
normalization, manipulation visibility, provenance and target invariants.
Lifecycle records and split commitments persist. Diversity reports now measure
domain, source, author and intervention-family concentration.

Plugins carry metadata and provenance hashes, compatible API versions,
diagnostic timeouts and explicit permissions. Gate override, certificate,
claim, review and protected-evaluator capabilities are forbidden. Sensitive
private-evidence permissions fail closed. Invalid, incompatible, duplicate and
timed-out plugins were rejected; the fixture scorer was persistently recorded
as validated.
