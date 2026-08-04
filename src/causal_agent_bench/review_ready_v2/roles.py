"""The one canonical reviewer role enum, and normalization into it.

Every CLI flag, package name, receipt field and registry entry resolves through
:func:`normalize_role` before it is used, so ``reviewer-a``, ``stage1_reviewer_a``
and ``Reviewer A`` can never denote three different things again.  An unknown
spelling is a hard error rather than a silently new role.
"""

from __future__ import annotations

REVIEWER_A = "REVIEWER_A"
REVIEWER_B = "REVIEWER_B"
ADJUDICATOR = "ADJUDICATOR"

CANONICAL_ROLES: tuple[str, ...] = (REVIEWER_A, REVIEWER_B, ADJUDICATOR)
REVIEW_ROLES: tuple[str, ...] = (REVIEWER_A, REVIEWER_B)

#: Opaque per-role item-id namespace.  A submission whose rows carry another
#: role's prefix is a package swap, not a typo, and is refused.
ROLE_NAMESPACE: dict[str, str] = {REVIEWER_A: "RA", REVIEWER_B: "RB"}

#: Stage-1/Stage-2 package basenames, derived from the canonical role alone.
ROLE_PACKAGE_BASENAME: dict[str, str] = {
    REVIEWER_A: "stage1_reviewer_a",
    REVIEWER_B: "stage1_reviewer_b",
}

_ALIASES: dict[str, str] = {
    # Reviewer A
    "reviewer_a": REVIEWER_A,
    "reviewer-a": REVIEWER_A,
    "reviewera": REVIEWER_A,
    "stage1_reviewer_a": REVIEWER_A,
    "stage1-reviewer-a": REVIEWER_A,
    "stage2_reviewer_a": REVIEWER_A,
    "stage2-reviewer-a": REVIEWER_A,
    "ra": REVIEWER_A,
    "a": REVIEWER_A,
    # Reviewer B
    "reviewer_b": REVIEWER_B,
    "reviewer-b": REVIEWER_B,
    "reviewerb": REVIEWER_B,
    "stage1_reviewer_b": REVIEWER_B,
    "stage1-reviewer-b": REVIEWER_B,
    "stage2_reviewer_b": REVIEWER_B,
    "stage2-reviewer-b": REVIEWER_B,
    "rb": REVIEWER_B,
    "b": REVIEWER_B,
    # Adjudicator
    "adjudicator": ADJUDICATOR,
    "stage1_adjudicator": ADJUDICATOR,
    "stage1-adjudicator": ADJUDICATOR,
    "stage2_adjudicator": ADJUDICATOR,
    "stage2-adjudicator": ADJUDICATOR,
    "adj": ADJUDICATOR,
}


class RoleError(ValueError):
    """A reviewer role could not be resolved to the canonical enum."""


def normalize_role(value: str | None) -> str:
    """Resolve any accepted spelling to the canonical enum, or fail closed."""

    if value is None:
        raise RoleError("a reviewer role is required; expected one of " + ", ".join(CANONICAL_ROLES))
    text = str(value).strip()
    if text in CANONICAL_ROLES:
        return text
    key = text.casefold().replace(" ", "_")
    resolved = _ALIASES.get(key)
    if resolved is None:
        raise RoleError(
            f"unknown reviewer role {value!r}; expected one of {', '.join(CANONICAL_ROLES)}"
        )
    return resolved


def namespace_for(role: str) -> str:
    """Return the opaque item-id prefix that belongs to a reviewing role."""

    canonical = normalize_role(role)
    if canonical not in ROLE_NAMESPACE:
        raise RoleError(f"{canonical} does not own a Stage-1/Stage-2 item namespace")
    return ROLE_NAMESPACE[canonical]


def package_basename(role: str) -> str:
    """Return the on-disk package basename for a reviewing role."""

    canonical = normalize_role(role)
    if canonical not in ROLE_PACKAGE_BASENAME:
        raise RoleError(f"{canonical} is not issued a review package")
    return ROLE_PACKAGE_BASENAME[canonical]


def is_reviewing_role(role: str) -> bool:
    return normalize_role(role) in REVIEW_ROLES


__all__ = [
    "ADJUDICATOR",
    "CANONICAL_ROLES",
    "REVIEWER_A",
    "REVIEWER_B",
    "REVIEW_ROLES",
    "ROLE_NAMESPACE",
    "ROLE_PACKAGE_BASENAME",
    "RoleError",
    "is_reviewing_role",
    "namespace_for",
    "normalize_role",
    "package_basename",
]
