# CAB Research OS architecture

## Purpose

CAB Research OS is the control plane around CAB's existing scientific kernel.
The kernel remains authoritative for intervention validity, paired estimands,
ACRS, RAAC, scoring and uncertainty. The Level-5 layer adds governed authoring,
immutable experiment identity, recoverable execution, evidence lineage,
protected evaluation and release gates.

## Bounded contexts

| Context | Canonical implementation | Boundary |
|---|---|---|
| Scientific kernel | Existing `metrics`, `raac`, `scoring`, `safety` modules | No Level-5 component may redefine its estimands or gates |
| Benchmark factory | `level5.benchmark` | Emits candidate tasks and review packets, never C10 judgments |
| Human validation | `level5.review`, `level5.review_server` and canonical C10 validator | Only attested human rows may advance C10 |
| Experiment registry | `level5.registry` | Public-safe metadata only; no protected payloads |
| Orchestrator | `level5.execution.LocalScheduler` | Immutable manifest, bounded retry, resume and collection |
| Backends | `level5.execution.Backend` | Capability discovery; no model/policy substitution |
| Artifact store | `level5.execution.ContentAddressedStore` | Immutable bytes addressed by SHA-256 outside Git |
| Observability | `level5.reliability.EventLog` | Local JSON, correlation IDs and redaction |
| Evaluator | `level5.evaluator` | Trusted task resolution and sandbox contract |
| Evidence graph | `level5.evidence.EvidenceGraph` | Hash lineage and legal evidence transitions |
| Certification | `level5.evidence` certificates and claim compiler | Certificates describe integrity; they are not claims |
| Public SDK/plugins | `causal_agent_bench.sdk`, `level5.plugins` | Versioned public imports and isolated plugin failures |
| Governance/release | `level5.governance` | Corrections, maturity states and fail-closed completion gate |

## Control flow

1. A typed authoring spec compiles to separate public/private views and a receipt.
2. Genuine human review and canonical C10 must precede a scientific slice lock.
3. A study compiles to an immutable run manifest before scheduling.
4. Scheduling writes checkpoints and artifacts atomically; every attempt remains linked.
5. Raw artifacts are immutable. Rescoring creates new derived nodes.
6. Evidence nodes and edges establish the path from task version to claim.
7. A claim is eligible only when every required node is paper-eligible.
8. The Level-5 gate also requires genuine external reproduction and pilots.

## Data placement

- Git: schemas, policies, public-safe hashes, fixtures, aggregate reports and code.
- Registry: public-safe identities, state, hashes, events and provenance.
- CAS: raw and derived large artifacts.
- Private task store: protected payloads, mounted only inside the trusted evaluator.
- Private reviewer store: identity mapping and consent records, never public exports.

## Failure model

All cross-context hand-offs use immutable hashes. Missing parents, changed manifests,
corrupt artifacts, invalid evidence transitions and private registry fields fail
closed. SQLite is the local default; the contracts allow future adapters without
changing scientific semantics.
