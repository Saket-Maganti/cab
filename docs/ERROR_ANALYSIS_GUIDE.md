# Error Analysis Guide

See [ERROR_TAXONOMY.md](ERROR_TAXONOMY.md) for the canonical 18-way taxonomy and filter definitions.

## Mining Commands

```bash
python -m causal_agent_bench mine-errors --run-dir results/<run_dir>
python scripts/mine_failure_gallery.py --run-dir results/<run_dir>
python -m causal_agent_bench export-failure-gallery --run-dir results/<run_dir>
```

`export-failure-gallery` updates the repo-level [FAILURE_GALLERY.md](FAILURE_GALLERY.md) and `paper/generated/failure_gallery_short.tex` with one qualitative panel per intervention family (tool failure, memory corruption, observation conflict, irrelevant tools, premature success signal, distractor evidence, long-horizon dependency). Without `--run-dir`, it writes illustrative scaffold examples only.

Both commands write a run-local gallery under `error_cases/` by default:

- one `.md` and `.jsonl` file per taxonomy error type,
- `filters/` files for cross-case filters,
- `qualitative_examples.md` for candidate paper examples,
- `taxonomy.json` with label definitions and provenance caveats.

Mined labels are deterministic heuristics for review. Do not report prevalence, model rankings, or label quality from these galleries without real LLM-backed runs and human validation.

## Recommended Review Fields

- Did the agent call the required tools?
- Were arguments valid and task-specific?
- Did the agent rely on corrupted memory or corrupted observations?
- Did the agent notice conflicts?
- Did it recover after tool errors?
- Did it stop too early?
- Was the final answer supported by the trajectory?

## Annotation Notes

Use trajectory JSONL as the primary evidence. Do not infer agent intent from final answer alone.

## Gallery Review Checklist

- Confirm the raw trajectory excerpt supports the mined label.
- Check whether expected behavior comes from the task/intervention, not hidden scorer leakage.
- Verify that final-answer correctness is not being treated as trajectory validity.
- Keep oracle-agent examples labeled as sanity-check upper bounds.
- Link any paper example to config hashes, seeds, model ids, prompt hashes, scorer versions, run directories, and git commits.
