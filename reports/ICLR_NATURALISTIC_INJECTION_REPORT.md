# Naturalistic Transfer v2 Prompt-Injection Report

Status: static pass; human artifact-level review required.

| Check | Result |
|---|---:|
| Tasks requiring injection scan | 60 |
| Missing injection-scan declarations | 0 |
| Prompt-injection pattern matches | 0 |
| Absolute-path leakage matches | 0 |
| Secret-pattern matches | 0 |
| Answer-isolation failures | 0 |
| Hidden/evaluator fields declared visible | 0 |

The static scanner covers known instruction-override phrases, unsafe local
paths, secret-like values, label-revealing IDs, and evaluator-field exposure.
It cannot prove the absence of every contextual attack. Two human reviewers
must inspect each artifact and intervention before C10 and slice locking.
