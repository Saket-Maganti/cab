# Paper Directory

This folder holds **paper coordination docs** and a self-contained **LaTeX bundle** under `latexpaper/`.

## LaTeX build

Upload `latexpaper/` to Overleaf or build locally:

```bash
cd paper/latexpaper
latexmk -pdf main.tex
```

From the repository root:

```bash
make paper-check
make paper-draft
make paper-submission-check
```

## Layout

| Path | Purpose |
|---|---|
| `latexpaper/` | Self-contained LaTeX source (upload this folder to a LaTeX editor) |
| `PAPER_STATUS.md` | Refresh status, placeholders, blockers |
| `PAPER_SYNC_MAP.md` | Section ↔ artifact ↔ evidence map |
| `PAPER_SECTION_CONTRACT.md` | No-run section-to-claim contract |
| `paper_section_contract.json` | Machine-readable paper section guard |
| `CONTRIBUTION_MAP.md` | Contributions ↔ evidence status |
| `EVIDENCE_GAP_MAP.md` | C1–C10 evidence requirements |
| `REVIEWER_PACKET.md` | Reviewer/co-author FAQ (no results claimed) |

## Fill results from runs

The draft uses `latexpaper/generated/*.tex` fragments with bracketed placeholders. After a verified run:

```bash
python3 scripts/fill_paper_from_run.py --run-dir results/<timestamp>_<run_name>
```

See [docs/PAPER_RESULTS_FILL.md](../docs/PAPER_RESULTS_FILL.md). Do not cite engineering-only stub fills as scientific evidence.

Before editing result-sensitive sections, run:

```bash
python3 scripts/check_paper_section_contract.py --mode draft
```
