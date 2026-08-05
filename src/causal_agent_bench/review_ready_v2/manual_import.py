"""Content-based discovery and classification of completed offline review files.

Reviewers completed the substantive Stage-1 and Stage-2 forms through simplified
offline HTML pages rather than through the production issue-declare-submit
sequence.  The completed CSVs therefore arrive as ordinary files with whatever
names the reviewer's browser gave them, in whatever directory they were saved
to.  Nothing downstream may depend on those names.

This module answers one question — *what is this file, scientifically?* — using
only the file's content: its column layout, its opaque item-id namespace, its row
count, and which dimension vocabulary its decisions speak.  A file called
``final_FINAL_v3 (2).csv`` classifies exactly as the same bytes called
``stage1_a.csv`` would, and swapping two filenames changes nothing.

Two hashes are recorded for every file.  The **raw** hash identifies the exact
bytes.  The **canonical** hash identifies the parsed scientific content, so a
harmless newline conversion is provably harmless rather than fatal, while a
single changed cell is provably fatal.
"""

from __future__ import annotations

import csv
import io
import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2.adjudication import (
    REQUIRED_DECISION_FIELDS,
    STAGE1,
    STAGE2,
)
from causal_agent_bench.review_ready_v2.common import canonical_bytes, sha256_bytes, sha256_json
from causal_agent_bench.review_ready_v2.roles import (
    REVIEW_ROLES,
    REVIEWER_A,
    REVIEWER_B,
    ROLE_NAMESPACE,
)
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_DIMENSIONS, REVIEW_FORM_COLUMNS
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_FORM_COLUMNS,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
)

DISCOVERY_SCHEMA_VERSION = "cab_manual_offline_review_discovery_v1"

#: What a classified file is.  ``UNCLASSIFIED`` is not an error by itself — most
#: files in a search root are simply not review evidence — but an unclassified
#: file can never be imported.
STAGE1_REVIEW_FORM = "STAGE1_REVIEW_FORM"
STAGE2_REVIEW_FORM = "STAGE2_REVIEW_FORM"
QUALIFICATION_FORM = "QUALIFICATION_FORM"
STAGE1_ADJUDICATION = "STAGE1_ADJUDICATION"
STAGE2_ADJUDICATION = "STAGE2_ADJUDICATION"
UNCLASSIFIED = "UNCLASSIFIED"

EVIDENCE_KINDS: tuple[str, ...] = (
    QUALIFICATION_FORM,
    STAGE1_REVIEW_FORM,
    STAGE1_ADJUDICATION,
    STAGE2_REVIEW_FORM,
    STAGE2_ADJUDICATION,
)

#: The kinds the Compact-20 scientific chain actually requires.  Qualification is
#: reviewer-screening scaffolding: it decides who may review, not what the slice
#: is, and it contributes no judgement about any pair.
REQUIRED_EVIDENCE_KINDS: tuple[str, ...] = (
    STAGE1_REVIEW_FORM,
    STAGE1_ADJUDICATION,
    STAGE2_REVIEW_FORM,
    STAGE2_ADJUDICATION,
)

#: Adjudication decision columns, in the order the issued template uses.
ADJUDICATION_COLUMNS: tuple[str, ...] = (
    "pair_id",
    "dimension",
    "final_value",
    "exclude_item",
    "rationale",
    "evidence_reference",
    "confidence",
)

#: The opaque prefix a qualification item carries.  Distinguishes a qualification
#: form from a Stage-1 form, which share an identical column layout.
QUALIFICATION_NAMESPACE = "Q4"

STAGE1_DIMENSION_NAMES: frozenset[str] = frozenset(name for name, _, _ in REVIEW_DIMENSIONS)
STAGE2_DIMENSION_NAMES: frozenset[str] = frozenset(STAGE2_SUBSTANTIVE_DIMENSIONS)

#: Files larger than this are never review evidence and are not parsed.  A
#: completed twenty-row form is a few kilobytes; the ceiling only exists so a
#: search root containing a large CSV cannot cost us anything.
MAX_CANDIDATE_BYTES = 4 * 1024 * 1024

#: How deep a search root is walked.  An unbounded walk of a home directory is
#: both slow and a privacy problem.
DEFAULT_MAX_DEPTH = 4

#: Directory names never descended into.
SKIP_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".hypothesis",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "Library",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "site",
        "site-packages",
        "venv",
    }
)

#: A leading character that spreadsheet software may execute on open.  Rejected
#: at import so a note can never become a formula in an exported CSV later.
FORMULA_PREFIXES: tuple[str, ...] = ("=", "+", "-", "@", "\t", "\r")


class ManualImportError(RuntimeError):
    """Discovery or classification refused a candidate file."""


@dataclass(frozen=True)
class Candidate:
    """One classified file, described by content rather than by name."""

    path: Path
    kind: str
    role: str | None
    stage: str | None
    row_count: int
    item_ids: tuple[str, ...]
    raw_sha256: str
    canonical_sha256: str
    namespace: str | None
    problems: tuple[str, ...] = ()

    @property
    def usable(self) -> bool:
        return self.kind != UNCLASSIFIED and not self.problems

    def public_row(self) -> dict[str, Any]:
        """A description safe to print: counts and hashes, never note text."""

        return {
            "kind": self.kind,
            "role": self.role,
            "stage": self.stage,
            "row_count": self.row_count,
            "item_id_count": len(self.item_ids),
            "namespace": self.namespace,
            "raw_sha256": self.raw_sha256,
            "canonical_sha256": self.canonical_sha256,
            "problems": list(self.problems),
        }


@dataclass
class DiscoveryResult:
    """Everything found, and whether it forms one complete importable set."""

    candidates: list[Candidate] = field(default_factory=list)
    searched_roots: list[str] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)

    def by_kind(self, kind: str) -> list[Candidate]:
        return [c for c in self.candidates if c.kind == kind and c.usable]


# --------------------------------------------------------------------------
# canonical content
# --------------------------------------------------------------------------


def _decode(payload: bytes) -> str:
    """Decode strictly, then normalize.  Malformed Unicode is refused outright."""

    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ManualImportError(f"file is not valid UTF-8: {error}") from error
    if "\x00" in text:
        raise ManualImportError("file contains a NUL byte and is not a review form")
    # NFC so that two visually identical notes hash identically; line endings
    # normalized so CRLF from a browser download is not a content change.
    return unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")


def read_csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Parse a CSV into its header and its non-blank rows.

    Uses the strict :mod:`csv` reader rather than dialect sniffing: every issued
    template is comma-separated, and a file that needs sniffing to parse is not
    one of ours.
    """

    reader = csv.DictReader(io.StringIO(_decode(payload)))
    header = tuple(reader.fieldnames or ())
    rows: list[dict[str, str]] = []
    for raw in reader:
        if None in raw or any(key is None for key in raw):
            raise ManualImportError("a row has more fields than the header declares")
        cells = {str(key): str(value or "").strip() for key, value in raw.items()}
        if not any(cells.values()):
            continue
        rows.append(cells)
    return header, rows


def canonical_review_content(
    header: tuple[str, ...], rows: list[dict[str, str]], *, key_column: str
) -> dict[str, Any]:
    """The scientific content of a form, independent of row order and line endings.

    Two files with this same digest carry the same judgements.  A single changed
    cell — including a changed note — changes it.
    """

    return {
        "columns": list(header),
        "key_column": key_column,
        "rows": sorted(
            ({column: row.get(column, "") for column in header} for row in rows),
            key=lambda row: canonical_bytes(row),
        ),
    }


def formula_injection_risks(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Cells that would execute if this content were re-exported to a spreadsheet."""

    risks: list[dict[str, str]] = []
    for row in rows:
        for column, value in sorted(row.items()):
            if value.startswith(FORMULA_PREFIXES):
                risks.append({"column": column, "reason": "leading_formula_character"})
    return risks


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------


def _namespace_of(item_ids: list[str]) -> str | None:
    """The single opaque prefix every id shares, or ``None`` when they differ."""

    prefixes = {item.split("-", 1)[0] for item in item_ids if "-" in item}
    if len(prefixes) != 1:
        return None
    return prefixes.pop()


def _role_for_namespace(namespace: str | None) -> str | None:
    for role in REVIEW_ROLES:
        if ROLE_NAMESPACE[role] == namespace:
            return role
    return None


def _classify_adjudication(rows: list[dict[str, str]]) -> tuple[str, str] | None:
    """``(kind, stage)`` decided by which dimension vocabulary the decisions use."""

    dimensions = {row.get("dimension", "") for row in rows}
    if not dimensions:
        return None
    if dimensions <= STAGE1_DIMENSION_NAMES:
        return STAGE1_ADJUDICATION, STAGE1
    if dimensions <= STAGE2_DIMENSION_NAMES:
        return STAGE2_ADJUDICATION, STAGE2
    return None


def classify_payload(payload: bytes) -> Candidate:
    """Classify raw CSV bytes purely by content.  Never consults a filename."""

    return classify_file(Path("<bytes>"), payload=payload)


def classify_file(path: Path, *, payload: bytes | None = None) -> Candidate:
    """Classify one file, recording both hashes and every content problem found."""

    data = path.read_bytes() if payload is None else payload
    raw_sha = sha256_bytes(data)
    problems: list[str] = []
    try:
        header, rows = read_csv_rows(data)
    except ManualImportError as error:
        return Candidate(
            path=path,
            kind=UNCLASSIFIED,
            role=None,
            stage=None,
            row_count=0,
            item_ids=(),
            raw_sha256=raw_sha,
            canonical_sha256=sha256_json({"unparsed": True}),
            namespace=None,
            problems=(str(error),),
        )

    kind = UNCLASSIFIED
    stage: str | None = None
    role: str | None = None
    namespace: str | None = None
    key_column = "reviewer_item_id"

    if header in (REVIEW_FORM_COLUMNS, STAGE2_FORM_COLUMNS):
        item_ids = [row.get("reviewer_item_id", "") for row in rows]
        namespace = _namespace_of(item_ids)
        if namespace is None:
            problems.append("rows_span_more_than_one_opaque_namespace")
        if namespace == QUALIFICATION_NAMESPACE:
            # Qualification and Stage-1 share a column layout exactly; only the
            # opaque namespace separates them.
            kind = QUALIFICATION_FORM
        else:
            kind = STAGE1_REVIEW_FORM if header == REVIEW_FORM_COLUMNS else STAGE2_REVIEW_FORM
            stage = STAGE1 if kind == STAGE1_REVIEW_FORM else STAGE2
            role = _role_for_namespace(namespace)
            if role is None:
                problems.append("opaque_namespace_matches_no_reviewer_role")
    elif set(header) >= set(REQUIRED_DECISION_FIELDS):
        key_column = "pair_id"
        item_ids = [row.get("pair_id", "") for row in rows]
        resolved = _classify_adjudication(rows)
        if resolved is None:
            problems.append("decision_dimensions_match_no_single_review_stage")
            item_ids = []
        else:
            kind, stage = resolved
    else:
        return Candidate(
            path=path,
            kind=UNCLASSIFIED,
            role=None,
            stage=None,
            row_count=len(rows),
            item_ids=(),
            raw_sha256=raw_sha,
            canonical_sha256=sha256_json(
                canonical_review_content(header, rows, key_column=key_column)
            ),
            namespace=None,
            problems=("column_layout_matches_no_issued_review_template",),
        )

    if not rows:
        problems.append("no_data_rows")
    if kind in (STAGE1_REVIEW_FORM, STAGE2_REVIEW_FORM, QUALIFICATION_FORM):
        seen = [row.get("reviewer_item_id", "") for row in rows]
        if len(seen) != len(set(seen)):
            problems.append("duplicate_reviewer_item_id")
        if any(not item for item in seen):
            problems.append("blank_reviewer_item_id")
    if formula_injection_risks(rows):
        problems.append("cell_would_execute_as_a_spreadsheet_formula")

    return Candidate(
        path=path,
        kind=kind,
        role=role,
        stage=stage,
        row_count=len(rows),
        item_ids=tuple(item_ids),
        raw_sha256=raw_sha,
        canonical_sha256=sha256_json(
            canonical_review_content(header, rows, key_column=key_column)
        ),
        namespace=namespace,
        problems=tuple(sorted(set(problems))),
    )


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------


def default_search_roots(repo_root: Path) -> list[Path]:
    """Search roots in priority order.  Never the whole home directory."""

    roots: list[Path] = []
    explicit = os.environ.get("CAB_HUMAN_REVIEW_INPUT_DIR", "").strip()
    if explicit:
        roots.append(Path(explicit).expanduser())
    roots.append(repo_root / "human_review_files")
    home = Path.home()
    roots.extend([home / "Downloads", home / "Desktop"])
    return [root for root in roots if root.is_dir()]


def _walk(root: Path, max_depth: int) -> list[Path]:
    found: list[Path] = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        depth = len(current.resolve().relative_to(root).parts)
        if depth >= max_depth:
            dirnames.clear()
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRECTORIES]
        for name in filenames:
            path = current / name
            if path.suffix.casefold() != ".csv":
                continue
            found.append(path)
    return sorted(found)


def discover_completed_review(
    search_roots: list[Path], *, max_depth: int = DEFAULT_MAX_DEPTH
) -> DiscoveryResult:
    """Classify every CSV under ``search_roots`` by content.

    Duplicate copies of the same evidence are tolerated when they are identical;
    two *different* files claiming the same role are refused rather than ranked,
    because there is no honest way to choose between two sets of judgements.
    """

    result = DiscoveryResult(searched_roots=[str(root) for root in search_roots])
    seen_raw: dict[str, Path] = {}
    for root in search_roots:
        for path in _walk(root, max_depth):
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                size = path.stat().st_size
            except OSError as error:
                result.rejected.append({"path": str(path), "reason": f"unreadable: {error}"})
                continue
            if size > MAX_CANDIDATE_BYTES:
                result.rejected.append({"path": str(path), "reason": "larger_than_any_review_form"})
                continue
            candidate = classify_file(path)
            if candidate.kind == UNCLASSIFIED:
                result.rejected.append(
                    {
                        "path": str(path),
                        "reason": candidate.problems[0] if candidate.problems else "unclassified",
                    }
                )
                continue
            previous = seen_raw.get(candidate.raw_sha256)
            if previous is not None:
                # A byte-identical duplicate carries no new information.
                result.rejected.append(
                    {"path": str(path), "reason": "byte_identical_duplicate_of_another_candidate"}
                )
                continue
            seen_raw[candidate.raw_sha256] = path
            result.candidates.append(candidate)
    return result


def select_evidence_set(
    result: DiscoveryResult, *, require_qualification: bool = False
) -> dict[str, Candidate]:
    """Resolve the discovery result to exactly one file per required slot.

    Fails closed on ambiguity.  Two different Stage-1 Reviewer-A files is a
    coordinator problem to resolve by hand, never a scoring problem to guess at.
    """

    slots: dict[str, list[Candidate]] = {}
    for candidate in result.candidates:
        if not candidate.usable:
            continue
        if candidate.kind in (STAGE1_REVIEW_FORM, STAGE2_REVIEW_FORM):
            slots.setdefault(f"{candidate.kind}:{candidate.role}", []).append(candidate)
        elif candidate.kind == QUALIFICATION_FORM:
            slots.setdefault(f"{candidate.kind}:{candidate.canonical_sha256}", []).append(candidate)
        else:
            slots.setdefault(candidate.kind, []).append(candidate)

    chosen: dict[str, Candidate] = {}
    for slot, found in sorted(slots.items()):
        distinct = {c.canonical_sha256 for c in found}
        if len(distinct) > 1:
            raise ManualImportError(
                f"FAIL_CLOSED_AMBIGUOUS_REVIEW_EVIDENCE: {slot} matched {len(distinct)} files with "
                "different content; resolve by hand which one is the completed submission"
            )
        chosen[slot] = found[0]

    required = [
        f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}",
        f"{STAGE1_REVIEW_FORM}:{REVIEWER_B}",
        STAGE1_ADJUDICATION,
        f"{STAGE2_REVIEW_FORM}:{REVIEWER_A}",
        f"{STAGE2_REVIEW_FORM}:{REVIEWER_B}",
        STAGE2_ADJUDICATION,
    ]
    missing = [slot for slot in required if slot not in chosen]
    if missing:
        raise ManualImportError(
            "the discovered evidence is incomplete; missing: " + ", ".join(missing)
        )
    if require_qualification and not any(
        slot.startswith(QUALIFICATION_FORM) for slot in chosen
    ):
        raise ManualImportError(
            "QUALIFICATION_EVIDENCE_MISSING: no completed qualification submission was discovered "
            "and no qualification score may be invented"
        )
    return chosen


def discovery_report(result: DiscoveryResult, chosen: dict[str, Candidate]) -> dict[str, Any]:
    """A public, counts-and-hashes-only description.  Never quotes a note."""

    return {
        "schema_version": DISCOVERY_SCHEMA_VERSION,
        "searched_roots": result.searched_roots,
        "candidate_count": len(result.candidates),
        "rejected_count": len(result.rejected),
        "rejected_reasons": sorted({row["reason"] for row in result.rejected}),
        "selected": {slot: candidate.public_row() for slot, candidate in sorted(chosen.items())},
        "qualification_discovered": any(
            slot.startswith(QUALIFICATION_FORM) for slot in chosen
        ),
        "classification_basis": (
            "column layout, opaque item-id namespace, and decision dimension vocabulary; "
            "filenames and directory names are never consulted"
        ),
    }


__all__ = [
    "ADJUDICATION_COLUMNS",
    "DEFAULT_MAX_DEPTH",
    "DISCOVERY_SCHEMA_VERSION",
    "EVIDENCE_KINDS",
    "MAX_CANDIDATE_BYTES",
    "QUALIFICATION_FORM",
    "QUALIFICATION_NAMESPACE",
    "REQUIRED_EVIDENCE_KINDS",
    "STAGE1_ADJUDICATION",
    "STAGE1_REVIEW_FORM",
    "STAGE2_ADJUDICATION",
    "STAGE2_REVIEW_FORM",
    "UNCLASSIFIED",
    "Candidate",
    "DiscoveryResult",
    "ManualImportError",
    "canonical_review_content",
    "classify_file",
    "classify_payload",
    "default_search_roots",
    "discover_completed_review",
    "discovery_report",
    "formula_injection_risks",
    "read_csv_rows",
    "select_evidence_set",
]
