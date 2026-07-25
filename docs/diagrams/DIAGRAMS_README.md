# Diagrams

Mermaid source files for CausalAgentBench. **Schematic only — no empirical results.**

## Files

| File | Description |
|---|---|
| [system_architecture.mmd](system_architecture.mmd) | Configs → dataset → runner → scoring → paper → ledger |
| [benchmark_flow.mmd](benchmark_flow.mmd) | Base task → clean/intervention → metrics → ACRS |
| [intervention_pairing.mmd](intervention_pairing.mmd) | Paired perturbation design |
| [run_lifecycle.mmd](run_lifecycle.mmd) | Experiment state machine |
| [evidence_levels.mmd](evidence_levels.mmd) | Evidence level progression |
| [claim_ledger_flow.mmd](claim_ledger_flow.mmd) | Run artifacts → claims → paper |
| [human_validation_flow.mmd](human_validation_flow.mmd) | Human validation pipeline |

## Viewing

- GitHub renders `.mmd` in some contexts; paste into [Mermaid Live Editor](https://mermaid.live) for preview.
- VS Code/Cursor: Mermaid preview extensions.

## Rules

- Do not add performance numbers or model rankings to diagrams.
- Update diagrams when architecture changes; they are source-controlled docs.

See also [../README.md](../README.md) (docs hub).
