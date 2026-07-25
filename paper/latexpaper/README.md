# CausalAgentBench Paper (LaTeX)

Self-contained LaTeX bundle. Upload this folder to Overleaf or any LaTeX editor to build the paper PDF.

## Build

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or with `latexmk`:

```bash
latexmk -pdf main.tex
```

From the repository root:

```bash
make paper-draft
```

## Layout

| Path | Purpose |
|---|---|
| `main.tex` | Root document |
| `sections/` | Section sources |
| `generated/` | Auto-filled fragments (placeholders until `fill-paper-from-run`) |
| `figures/` | Schematic placeholder figures (not empirical results) |
| `references.bib` | Bibliography |

## Placeholders

Bracketed numeric placeholders in the abstract and tables are intentional until verified experiment runs are linked. Do not fill them manually for submission.

Fill from the repo after a verified run:

```bash
python3 scripts/fill_paper_from_run.py --run-dir results/<timestamp>_<run_name>
```

See [../PAPER_STATUS.md](../PAPER_STATUS.md) and [../../docs/PAPER_RESULTS_FILL.md](../../docs/PAPER_RESULTS_FILL.md).
