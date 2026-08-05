"""Find the attached CAB bundle on Kaggle by content, never by filename.

A Kaggle notebook receives its inputs under ``/kaggle/input/<dataset>/...``,
where ``<dataset>`` is whatever the uploader named the dataset and the archive
inside is whatever the uploader named the file.  Both get renamed.  Matching on
``*/pyproject.toml``, or on an expected ZIP name, breaks the moment someone
renames anything — and then the notebook fails in a way that looks like a
scientific problem rather than a naming one.

This module identifies a bundle the only way that is stable: by looking at what
is *inside* it.  A weighted set of sentinel paths scores each candidate, the
highest-confidence unique candidate wins, and genuine ambiguity fails closed
with a readable table rather than picking one.

Stdlib only, and deliberately so: it has to run before the repository it is
looking for has been extracted, so it cannot import anything from that
repository.  The notebook generator inlines this file's source directly, which
keeps the notebooks and the tested module from ever drifting apart.
"""

from __future__ import annotations

import hashlib
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DISCOVERY_SCHEMA_VERSION = "cab_kaggle_input_discovery_v1"

#: Bundle classifications, decided by manifest content.
REPOSITORY_BUNDLE = "REPOSITORY_BUNDLE"
COMPACT20_OUTPUT = "COMPACT20_OUTPUT"
SCALE100_OUTPUT = "SCALE100_OUTPUT"
RAAC_OUTPUT = "RAAC_OUTPUT"
NATURALISTIC_OUTPUT = "NATURALISTIC_OUTPUT"
FINAL_ANALYSIS_INPUT = "FINAL_ANALYSIS_INPUT"
UNKNOWN_BUNDLE = "UNKNOWN_BUNDLE"

#: An environment variable that names an exact archive or directory.  Checked
#: first, but still validated: an override that points at the wrong bundle type
#: fails rather than being trusted.
OVERRIDE_ENV_VAR = "CAB_KAGGLE_INPUT_PATH"

#: Weighted sentinels for a repository bundle.  No single sentinel is decisive:
#: ``pyproject.toml`` alone matches half the ZIPs on Kaggle.
REPOSITORY_SENTINELS: tuple[tuple[str, int], ...] = (
    ("CAB_KAGGLE_INPUT_MANIFEST.json", 6),
    ("reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json", 5),
    ("reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json", 5),
    ("src/causal_agent_bench/", 4),
    ("environment/kaggle_environment.json", 3),
    ("configs/", 2),
    ("scripts/", 2),
    ("data/manifests/", 2),
    ("pyproject.toml", 1),
)

#: Weighted sentinels for a run-output bundle.
OUTPUT_SENTINELS: tuple[tuple[str, int], ...] = (
    ("CAB_KAGGLE_OUTPUT_MANIFEST.json", 6),
    ("run_manifest.json", 4),
    ("execution_authorization.json", 4),
    ("shard_manifest.json", 3),
    ("trajectories/", 3),
    ("raw/", 1),
)

#: A candidate must clear this to be selectable at all.
MIN_CONFIDENCE_SCORE = 8

#: Refuse an archive that expands to more than this, or whose expansion ratio
#: exceeds the cap.  Both are zip-bomb guards, not scientific limits.
MAX_EXPANDED_BYTES = 4 * 1024**3
MAX_EXPANSION_RATIO = 200

#: How deep ``/kaggle/input`` is walked looking for archives and directories.
MAX_SCAN_DEPTH = 6


class KaggleInputError(RuntimeError):
    """Input discovery refused, and said exactly why."""


@dataclass
class Candidate:
    """One archive or directory, described by what it contains."""

    path: Path
    is_archive: bool
    bundle_type: str
    score: int
    member_count: int
    size_bytes: int
    sha256: str
    root_prefix: str
    problems: tuple[str, ...] = ()

    @property
    def selectable(self) -> bool:
        return (
            not self.problems
            and self.bundle_type != UNKNOWN_BUNDLE
            and self.score >= MIN_CONFIDENCE_SCORE
        )

    def row(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "kind": "archive" if self.is_archive else "directory",
            "bundle_type": self.bundle_type,
            "sentinel_score": self.score,
            "member_count": self.member_count,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "root_prefix": self.root_prefix,
            "problems": list(self.problems),
        }


# --------------------------------------------------------------------------
# hashing and safety
# --------------------------------------------------------------------------


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unsafe_member(name: str) -> str | None:
    """Why a ZIP member must not be extracted, or ``None`` when it is fine."""

    if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
        return "absolute_path_member"
    parts = Path(name.replace("\\", "/")).parts
    if any(part == ".." for part in parts):
        return "path_traversal_member"
    return None


def _archive_problems(path: Path) -> tuple[list[str], list[str]]:
    """``(member_names, problems)`` for one archive, without extracting it."""

    problems: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            expanded = sum(info.file_size for info in infos)
            compressed = sum(info.compress_size for info in infos) or 1
            for info in infos:
                reason = _unsafe_member(info.filename)
                if reason:
                    problems.append(reason)
                    break
                # Directory entries and regular files only; a symlink, device or
                # socket is never materialised.  Many ZIP writers leave the file
                # type bits empty, which means "unspecified", not "special", so
                # only an explicitly non-regular type is rejected.
                file_type = (info.external_attr >> 16) & 0o170000
                if file_type and file_type not in (0o100000, 0o040000):
                    problems.append("non_regular_member")
                    break
            if expanded > MAX_EXPANDED_BYTES:
                problems.append("expands_beyond_the_size_ceiling")
            if expanded / compressed > MAX_EXPANSION_RATIO:
                problems.append("expansion_ratio_beyond_the_ceiling")
    except zipfile.BadZipFile:
        return [], ["not_a_readable_zip_archive"]
    except OSError as error:
        return [], [f"unreadable: {error}"]
    return names, sorted(set(problems))


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------


def common_root_prefix(names: list[str]) -> str:
    """The single top-level directory every member shares, or ``""``.

    An archive may or may not have a wrapping folder, and its name is arbitrary
    when it exists; everything downstream works relative to whatever this finds.
    """

    tops = {name.split("/", 1)[0] for name in names if name and not name.startswith("/")}
    if len(tops) != 1:
        return ""
    top = tops.pop()
    if not any(name.startswith(f"{top}/") for name in names):
        return ""
    return top


def _score(names: list[str], sentinels: tuple[tuple[str, int], ...], root: str) -> int:
    prefix = f"{root}/" if root else ""
    relative = [name[len(prefix) :] if prefix and name.startswith(prefix) else name for name in names]
    total = 0
    for sentinel, weight in sentinels:
        if sentinel.endswith("/"):
            if any(name.startswith(sentinel) for name in relative):
                total += weight
        elif sentinel in relative:
            total += weight
    return total


def _output_bundle_type(names: list[str], root: str) -> str:
    """Which study an output bundle belongs to, by manifest name and content."""

    prefix = f"{root}/" if root else ""
    relative = {name[len(prefix) :] if prefix and name.startswith(prefix) else name for name in names}
    markers = {
        COMPACT20_OUTPUT: ("compact20", "compact_20"),
        SCALE100_OUTPUT: ("scale100", "scale_100"),
        RAAC_OUTPUT: ("raac",),
        NATURALISTIC_OUTPUT: ("naturalistic",),
        FINAL_ANALYSIS_INPUT: ("final_analysis",),
    }
    joined = " ".join(sorted(relative)).casefold()
    matched = [
        bundle for bundle, needles in markers.items() if any(needle in joined for needle in needles)
    ]
    # More than one study marker means the archive does not identify one study.
    return matched[0] if len(matched) == 1 else UNKNOWN_BUNDLE


def classify_names(names: list[str]) -> tuple[str, int, str]:
    """``(bundle_type, score, root_prefix)`` from member names alone."""

    root = common_root_prefix(names)
    repository = _score(names, REPOSITORY_SENTINELS, root)
    output = _score(names, OUTPUT_SENTINELS, root)
    if repository >= output and repository:
        return REPOSITORY_BUNDLE, repository, root
    if output:
        return _output_bundle_type(names, root), output, root
    return UNKNOWN_BUNDLE, 0, root


def classify_archive(path: Path) -> Candidate:
    names, problems = _archive_problems(path)
    bundle_type, score, root = classify_names(names) if names else (UNKNOWN_BUNDLE, 0, "")
    return Candidate(
        path=path,
        is_archive=True,
        bundle_type=bundle_type,
        score=score,
        member_count=len(names),
        size_bytes=path.stat().st_size if path.is_file() else 0,
        sha256=file_sha256(path) if path.is_file() and not problems else "",
        root_prefix=root,
        problems=tuple(problems),
    )


def classify_directory(path: Path) -> Candidate:
    """An already-extracted bundle, attached as a plain directory."""

    names: list[str] = []
    for current, dirnames, filenames in os.walk(path):
        relative = Path(current).relative_to(path)
        if len(relative.parts) > MAX_SCAN_DEPTH:
            dirnames.clear()
            continue
        for name in filenames:
            names.append(str(relative / name) if relative.parts else name)
        for name in dirnames:
            names.append((str(relative / name) if relative.parts else name) + "/")
    bundle_type, score, _ = classify_names(names)
    return Candidate(
        path=path,
        is_archive=False,
        bundle_type=bundle_type,
        score=score,
        member_count=len(names),
        size_bytes=0,
        sha256="",
        root_prefix="",
    )


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------


def scan(search_root: Path, *, max_depth: int = MAX_SCAN_DEPTH) -> list[Candidate]:
    """Every plausible candidate under ``search_root``, archives and directories."""

    candidates: list[Candidate] = []
    if not search_root.is_dir():
        return candidates
    root = search_root.resolve()
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        here = Path(current)
        depth = len(here.resolve().relative_to(root).parts)
        if depth >= max_depth:
            dirnames.clear()
        for name in sorted(filenames):
            path = here / name
            if path.suffix.casefold() != ".zip" or path.is_symlink():
                continue
            candidates.append(classify_archive(path))
        # A Kaggle dataset directory may itself *be* the extracted bundle.
        if depth <= 2:
            for name in sorted(dirnames):
                directory = here / name
                if directory.is_symlink():
                    continue
                candidate = classify_directory(directory)
                if candidate.score >= MIN_CONFIDENCE_SCORE:
                    candidates.append(candidate)
    return candidates


def select(
    candidates: list[Candidate], *, expected_bundle_type: str | None = None
) -> Candidate:
    """Pick the one unique highest-confidence candidate, or fail closed."""

    usable = [candidate for candidate in candidates if candidate.selectable]
    if expected_bundle_type:
        usable = [c for c in usable if c.bundle_type == expected_bundle_type]
    if not usable:
        raise KaggleInputError(
            "NO_MATCHING_KAGGLE_INPUT: no attached archive or directory carries the expected "
            f"CAB sentinels{f' for {expected_bundle_type}' if expected_bundle_type else ''}.\n"
            + render_table(candidates)
        )
    best = max(candidate.score for candidate in usable)
    leaders = [candidate for candidate in usable if candidate.score == best]
    # Byte-identical copies of the same bundle are not an ambiguity.
    distinct = {candidate.sha256 for candidate in leaders if candidate.sha256}
    if len(leaders) > 1 and len(distinct) > 1:
        raise KaggleInputError(
            "FAIL_CLOSED_AMBIGUOUS_KAGGLE_INPUT: more than one attached bundle scores equally "
            "and their contents differ. Detach the one you do not want, or set "
            f"{OVERRIDE_ENV_VAR}.\n" + render_table(leaders)
        )
    return leaders[0]


def render_table(candidates: list[Candidate]) -> str:
    """A private-safe inventory: paths, sizes, hashes, types and scores."""

    if not candidates:
        return "  (no candidates found under the search root)"
    lines = ["  path | type | score | members | sha256 | problems"]
    for candidate in sorted(candidates, key=lambda item: (-item.score, str(item.path))):
        lines.append(
            f"  {candidate.path} | {candidate.bundle_type} | {candidate.score} | "
            f"{candidate.member_count} | {candidate.sha256[:16] or '-'} | "
            f"{','.join(candidate.problems) or '-'}"
        )
    return "\n".join(lines)


def safe_extract(candidate: Candidate, destination_root: Path) -> Path:
    """Extract to a hash-named directory, re-checking every member as we go.

    Named by content hash so that re-running a notebook reuses the same
    directory, and two different bundles can never land on top of each other.
    """

    if not candidate.is_archive:
        return candidate.path
    destination = destination_root / f"cab_input_{candidate.sha256[:16]}"
    marker = destination / ".cab_extraction_complete"
    if marker.is_file():
        return destination
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(candidate.path) as archive:
        for info in archive.infolist():
            reason = _unsafe_member(info.filename)
            if reason:
                raise KaggleInputError(f"refusing to extract {info.filename!r}: {reason}")
            target = (destination / info.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise KaggleInputError(
                    f"refusing to extract {info.filename!r}: it escapes the destination"
                )
            archive.extract(info, destination)
    marker.write_text("complete\n")
    return destination


def locate_bundle_root(extracted: Path, *, bundle_type: str = REPOSITORY_BUNDLE) -> Path:
    """Find the logical root inside an extracted bundle, whatever it is wrapped in."""

    sentinels = (
        ("pyproject.toml", "src/causal_agent_bench")
        if bundle_type == REPOSITORY_BUNDLE
        else ("CAB_KAGGLE_OUTPUT_MANIFEST.json",)
    )

    def matches(directory: Path) -> bool:
        return all((directory / sentinel).exists() for sentinel in sentinels)

    if matches(extracted):
        return extracted
    for depth in range(1, 4):
        for candidate in sorted(extracted.glob("/".join(["*"] * depth))):
            if candidate.is_dir() and matches(candidate):
                return candidate
    raise KaggleInputError(
        f"the extracted bundle at {extracted} has no {bundle_type} root; expected "
        f"{' and '.join(sentinels)} somewhere within the first three levels"
    )


def discover_kaggle_input(
    *,
    search_root: Path = Path("/kaggle/input"),
    working_root: Path = Path("/kaggle/working"),
    expected_bundle_type: str | None = REPOSITORY_BUNDLE,
) -> dict[str, Any]:
    """Find, verify and extract the attached bundle.  The whole entry point.

    Honours ``CAB_KAGGLE_INPUT_PATH`` when set, but validates the override the
    same way as a discovered candidate: pointing it at the wrong kind of bundle
    is an error, not an instruction.
    """

    override = os.environ.get(OVERRIDE_ENV_VAR, "").strip()
    if override:
        path = Path(override).expanduser()
        if not path.exists():
            raise KaggleInputError(f"{OVERRIDE_ENV_VAR} points at {path}, which does not exist")
        candidate = classify_archive(path) if path.is_file() else classify_directory(path)
        candidates = [candidate]
    else:
        candidates = scan(search_root)

    selected = select(candidates, expected_bundle_type=expected_bundle_type)
    extracted = safe_extract(selected, working_root)
    root = locate_bundle_root(extracted, bundle_type=selected.bundle_type)
    return {
        "schema_version": DISCOVERY_SCHEMA_VERSION,
        "selected": selected.row(),
        "bundle_type": selected.bundle_type,
        "archive_sha256": selected.sha256,
        "bundle_root": str(root),
        "extracted_to": str(extracted),
        "override_used": bool(override),
        "candidate_count": len(candidates),
        "candidates": [candidate.row() for candidate in candidates],
        "selection_basis": "content sentinels and manifest contents; never the filename",
    }


def verify_bundle_manifest(bundle_root: Path) -> dict[str, Any]:
    """Re-hash every member the bundle manifest declares."""

    import json

    manifest_path = bundle_root / "CAB_KAGGLE_INPUT_MANIFEST.json"
    if not manifest_path.is_file():
        raise KaggleInputError(f"no CAB_KAGGLE_INPUT_MANIFEST.json at {bundle_root}")
    manifest = json.loads(manifest_path.read_text())
    mismatched: list[str] = []
    missing: list[str] = []
    for member in manifest.get("members", []):
        target = bundle_root / member["path"]
        if not target.is_file():
            missing.append(member["path"])
            continue
        if file_sha256(target) != member["sha256"]:
            mismatched.append(member["path"])
    checks = {
        "every_declared_member_present": not missing,
        "every_member_hash_matches": not mismatched,
        "member_count_matches": len(manifest.get("members", []))
        == int(manifest.get("member_count", -1)),
        "declares_no_private_material": manifest.get("private_material_included") is False,
    }
    return {
        "bundle_type": manifest.get("bundle_type"),
        "created_from_commit": manifest.get("created_from_commit"),
        "bundle_content_sha256": manifest.get("bundle_content_sha256"),
        "missing_members": missing,
        "mismatched_members": mismatched,
        "checks": checks,
        "passed": all(checks.values()),
    }


__all__ = [
    "COMPACT20_OUTPUT",
    "DISCOVERY_SCHEMA_VERSION",
    "FINAL_ANALYSIS_INPUT",
    "MAX_EXPANSION_RATIO",
    "MIN_CONFIDENCE_SCORE",
    "NATURALISTIC_OUTPUT",
    "OUTPUT_SENTINELS",
    "OVERRIDE_ENV_VAR",
    "RAAC_OUTPUT",
    "REPOSITORY_BUNDLE",
    "REPOSITORY_SENTINELS",
    "SCALE100_OUTPUT",
    "UNKNOWN_BUNDLE",
    "Candidate",
    "KaggleInputError",
    "classify_archive",
    "classify_directory",
    "classify_names",
    "common_root_prefix",
    "discover_kaggle_input",
    "file_sha256",
    "locate_bundle_root",
    "render_table",
    "safe_extract",
    "scan",
    "select",
    "verify_bundle_manifest",
]
