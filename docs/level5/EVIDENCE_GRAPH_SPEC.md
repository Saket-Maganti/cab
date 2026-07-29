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
