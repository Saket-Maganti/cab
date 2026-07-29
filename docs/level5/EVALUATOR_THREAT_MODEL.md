# Evaluator threat model

Protected assets include task text, interventions, target answers, scorer
internals, private metadata and signing keys. Adversaries may submit malicious
archives or programs, probe the environment, exhaust resources, exfiltrate
through output/timing, exploit prompt/tool injection, hard-code tasks, query a
score oracle, collude or tamper with receipts.

Controls include archive traversal rejection, runtime-only private mounts,
network denial, non-root execution, capability drop, resource/output limits,
secret-free environments, opaque task IDs, aggregate-only results, bounded
probing, audit logs and signed receipts.

Residual risks include covert timing channels, novel encodings, memorization
that cannot be distinguished from competence, shared-model collusion and
container-runtime vulnerabilities. Heuristics never replace isolation, manual
review or a genuine security pilot.
