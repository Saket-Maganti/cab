# Evidence persistence and certification report

Status: passed at fixture-contract scope.

The persistent graph stored two versioned nodes and one audited-by edge, traced
lineage, rejected a cycle and rejected direct promotion to certified evidence.
A fixture run-integrity certificate was issued and verified through the signer
interface; certified transitions required both audit nodes and certificate IDs.
The durable claim compiler resolved only persisted evidence.

An original result was corrected by an immutable version-2 result with reason,
reviewer hash and public notice, then withdrawn without deleting history.
Certificate revocation immediately invalidated verification. Transparency-log
verification passed, and its database trigger prevented update tampering.
Separate metadata and forged-chain attacks were detected by graph and
transparency verification.

Public export omits private material and includes structural commitments. All
demo objects lived in isolated fixture registries and incremented no genuine
scientific counter.
