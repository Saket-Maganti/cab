# Paper Build

Build from this directory:

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If `latexmk` is available:

```bash
cd paper
latexmk -pdf main.tex
```

The current draft intentionally contains bracketed result placeholders. Do not replace them unless the corresponding claim-ledger row points to a reproducible experiment artifact.
