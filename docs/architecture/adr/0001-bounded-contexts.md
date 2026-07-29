# ADR 0001: Bounded contexts around the scientific kernel

Status: accepted

CAB keeps its existing metrics, RAAC, scoring and safety modules as the
scientific kernel. Level-5 services call those systems through contracts and do
not clone them. This prevents divergent definitions of validity, evidence and
claims.
