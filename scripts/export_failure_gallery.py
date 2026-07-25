#!/usr/bin/env python3
"""Export docs/FAILURE_GALLERY.md and paper-ready shortened examples."""

from __future__ import annotations

import argparse

from causal_agent_bench.analysis.failure_gallery_doc import export_failure_gallery_doc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Optional scored run directory. Without it, writes illustrative scaffold examples only.",
    )
    parser.add_argument("--doc-path", default="docs/FAILURE_GALLERY.md")
    parser.add_argument("--paper-path", default="paper/latexpaper/generated/failure_gallery_short.tex")
    parser.add_argument("--max-per-family", type=int, default=1)
    args = parser.parse_args()

    paths = export_failure_gallery_doc(
        run_dir=args.run_dir,
        doc_path=args.doc_path,
        paper_path=args.paper_path,
        max_per_family=args.max_per_family,
    )
    for path in paths:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
