# Task Template Registry

Machine-readable templates live in [task_template_registry.json](task_template_registry.json). All templates are **synthetic** (`author/source: synthetic`) for deterministic generation.

## Fields

| Field | Purpose |
|---|---|
| `template_id` | Stable ID referenced in generation configs |
| `domain` | One of eight benchmark domains |
| `difficulty` | easy / medium / hard |
| `required_tools` | Minimum tool set for clean success |
| `optional_tools` | Allowed but not required |
| `hidden_ground_truth_fields` | Keys scored against hidden labels |
| `success_criteria_pattern` | Natural-language rubric pattern |
| `forbidden_assumptions` | Safety + scoring constraints |
| `valid_intervention_families` | Allowed paired interventions |
| `expected_robust_behavior` | Under intervention, agent should … |
| `known_risks` | Reviewer/author warnings |
| `version` | Template semver |

## Coverage (v0.1.0)

3 templates × 8 domains = **24 templates**. See JSON for IDs.

## Usage

- Generation configs reference template IDs via domain/difficulty filters.
- `audit-dataset` checks distribution against registry expectations.
- Do **not** treat registry completeness as empirical benchmark validation.

## Related

- [docs/BENCHMARK_TAXONOMY.md](../docs/BENCHMARK_TAXONOMY.md)
- [benchmark_specs/task_domains.yaml](task_domains.yaml)
- [benchmark_specs/intervention_families.yaml](intervention_families.yaml)
