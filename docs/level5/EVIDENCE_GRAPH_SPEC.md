# Evidence graph specification

Node types cover task version, review, C10 decision, split lock, model/policy
version, run, shard, raw trajectory, score, audit, analysis, figure, table,
claim and release. Edges cover generated/scored/reviewed/audited/analysed,
support, invalidation, supersession and reproduction.

Every node carries a content hash, evidence class, visibility and creation time.
Edges require existing endpoints and the graph must remain acyclic. Public
export removes private nodes and incident edges and recursively redacts
sensitive metadata.

Transitions are one-step and fail closed:
design → engineering → fixture → human input required → execution pending →
preliminary real → audited real → paper eligible. A fixture cannot jump into
real evidence.

## Persistence and certified transitions

Nodes, edges and transition history live in SQLite. Node metadata has its own
commitment. Audited and paper-eligible nodes cannot be inserted directly.
Transition to either class requires named audit nodes and active certificates
in the same transaction. Revoked certificates fail closed.

Certificates bind subject, supporting node IDs, evidence classes, signer,
expiry and visibility. They are immutable; revocation and supersession are
appended. Every node, edge, transition, certificate, revocation, result and
correction event extends a hash-chained transparency log. The local log is
tamper-evident, not an externally witnessed transparency service.

The claim compiler checks required node types, minimum evidence class, common
lineage, scorer audit, uncertainty, external reproduction and invalidators.
Fixture support is reported explicitly and never increments a genuine counter.

Results are immutable. A correction creates a versioned replacement and public
notice; withdrawal appends a separate action. Paper tables and figures should
cite node and certificate IDs.
