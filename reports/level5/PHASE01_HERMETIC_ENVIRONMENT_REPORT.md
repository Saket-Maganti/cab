# Phase 01 hermetic environment report

Python 3.11+ is declared; runtime constraints are pinned in `constraints.txt`.
Docker and Apptainer definitions install only the package source and exclude
private/data/result/report roots from the Docker context. macOS/Linux setup
scripts, Kaggle metadata export, CycloneDX-compatible SBOM and dependency
licence inventory are present.

Observed environment doctor: Python 3.11.9 on Apple arm64; all six contract
checks passed. Container execution itself is environment-dependent and was not
claimed.
