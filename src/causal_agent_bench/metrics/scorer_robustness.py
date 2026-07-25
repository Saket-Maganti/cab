from __future__ import annotations

import re
from datetime import datetime
from typing import Any

ABSTENTION_TERMS = (
    "cannot determine",
    "not enough information",
    "insufficient information",
    "need more information",
    "unable to verify",
    "unclear",
)


def normalize_text(value: Any) -> str:
    text = str(value).lower().strip()
    text = re.sub(r"[^a-z0-9.\-/: ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def exact_match(expected: Any, observed: Any) -> bool:
    return str(expected) == str(observed)


def normalized_match(expected: Any, observed: Any) -> bool:
    return normalize_text(expected) == normalize_text(observed)


def numeric_match(expected: Any, observed: Any, *, tolerance: float = 1e-6) -> bool:
    try:
        return abs(float(expected) - float(observed)) <= tolerance
    except (TypeError, ValueError):
        return False


def list_set_match(expected: list[Any], observed: list[Any], *, order_sensitive: bool = False) -> bool:
    expected_norm = [normalize_text(item) for item in expected]
    observed_norm = [normalize_text(item) for item in observed]
    if order_sensitive:
        return expected_norm == observed_norm
    return sorted(expected_norm) == sorted(observed_norm)


def contains_match(expected: Any, observed: Any) -> bool:
    expected_norm = normalize_text(expected)
    observed_norm = normalize_text(observed)
    if not expected_norm:
        return False
    return expected_norm in observed_norm


def safe_contains_match(expected: Any, observed: Any) -> bool:
    expected_norm = normalize_text(expected)
    observed_norm = normalize_text(observed)
    if not expected_norm or len(expected_norm) < 3:
        return False
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(expected_norm)}(?![a-z0-9])", observed_norm))


def normalize_date(value: Any) -> str | None:
    text = normalize_text(value)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def date_match(expected: Any, observed: Any) -> bool:
    return normalize_date(expected) is not None and normalize_date(expected) == normalize_date(observed)


def is_abstention(text: Any) -> bool:
    normalized = normalize_text(text)
    return any(term in normalized for term in ABSTENTION_TERMS)


def refusal_or_uncertainty_handled(
    observed: Any,
    *,
    abstention_required: bool,
    definitive_answer_expected: bool,
) -> bool:
    abstained = is_abstention(observed)
    if abstention_required:
        return abstained
    if definitive_answer_expected:
        return not abstained
    return True
