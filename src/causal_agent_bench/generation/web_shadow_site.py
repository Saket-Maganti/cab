from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SITE_ID = "acme_shadow_v1"
SITE_FROZEN_AT = "2024-06-01"
DEFAULT_SITE_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "web_shadow" / "acme_site.json"
)


def _page(
    *,
    url: str,
    title: str,
    body: str,
    links: list[dict[str, str]] | None = None,
    sections: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "url": url,
        "title": title,
        "body": body.strip(),
        "links": links or [],
        "sections": sections or {},
    }


def build_acme_site() -> dict[str, Any]:
    """Deterministic frozen web snapshot (no live network)."""

    pages = {
        "/": _page(
            url="/",
            title="Acme Corp Home",
            body="Welcome to Acme Corp. Use search or browse products and documentation.",
            links=[
                {"href": "/search", "text": "Site search"},
                {"href": "/products", "text": "Products"},
                {"href": "/docs", "text": "Documentation"},
                {"href": "/support", "text": "Support"},
                {"href": "/legal", "text": "Legal"},
            ],
        ),
        "/search": _page(
            url="/search",
            title="Search",
            body="Search the frozen Acme snapshot index. Results are static and deterministic.",
            links=[{"href": "/", "text": "Home"}],
        ),
        "/products": _page(
            url="/products",
            title="Products",
            body="Browse hardware and software products.",
            links=[
                {"href": "/products/widget-pro", "text": "Widget Pro"},
                {"href": "/products/widget-lite", "text": "Widget Lite"},
                {"href": "/products/enterprise-suite", "text": "Enterprise Suite"},
            ],
        ),
        "/products/widget-pro": _page(
            url="/products/widget-pro",
            title="Widget Pro",
            body="Widget Pro is the flagship device for industrial telemetry.",
            links=[{"href": "/docs/widget-pro/specs", "text": "Full specifications"}],
            sections={
                "sku": {"heading": "SKU", "content": "SKU: WDG-PRO-2024", "visible": True},
                "weight": {
                    "heading": "Weight",
                    "content": "Shipping weight: 2.4 kg",
                    "visible": True,
                },
            },
        ),
        "/products/widget-lite": _page(
            url="/products/widget-lite",
            title="Widget Lite",
            body="Lightweight variant for edge deployments.",
            sections={
                "sku": {"heading": "SKU", "content": "SKU: WDG-LITE-2024", "visible": True},
            },
        ),
        "/products/enterprise-suite": _page(
            url="/products/enterprise-suite",
            title="Enterprise Suite",
            body="Bundled platform with SSO and audit logging.",
            links=[{"href": "/pricing", "text": "View pricing"}],
            sections={
                "features": {
                    "heading": "Features",
                    "content": "Includes SSO, audit logging, and 99.95% SLA.",
                    "visible": True,
                },
            },
        ),
        "/pricing": _page(
            url="/pricing",
            title="Pricing",
            body="Public list prices for Acme offerings.",
            sections={
                "enterprise": {
                    "heading": "Enterprise tier",
                    "content": "Enterprise tier list price: $48,000 per year.",
                    "visible": True,
                },
                "lite": {
                    "heading": "Lite tier",
                    "content": "Lite tier list price: $1,200 per year.",
                    "visible": True,
                },
            },
        ),
        "/docs": _page(
            url="/docs",
            title="Documentation hub",
            body="API, product, and operations documentation.",
            links=[
                {"href": "/docs/api/rate-limits", "text": "API rate limits"},
                {"href": "/docs/widget-pro/specs", "text": "Widget Pro specs"},
                {"href": "/docs/ops/runbook", "text": "Operations runbook"},
            ],
        ),
        "/docs/api/rate-limits": _page(
            url="/docs/api/rate-limits",
            title="API rate limits",
            body="Default REST quota for standard keys.",
            sections={
                "quota": {
                    "heading": "Standard quota",
                    "content": "Standard API keys: 1200 requests per minute.",
                    "visible": True,
                },
            },
        ),
        "/docs/widget-pro/specs": _page(
            url="/docs/widget-pro/specs",
            title="Widget Pro specifications",
            body="Technical specifications for Widget Pro.",
            sections={
                "power": {
                    "heading": "Power",
                    "content": "Max power draw: 18W under load.",
                    "visible": True,
                },
                "ports": {
                    "heading": "Ports",
                    "content": "2x Gigabit Ethernet, 1x USB-C service port.",
                    "visible": True,
                },
            },
        ),
        "/docs/ops/runbook": _page(
            url="/docs/ops/runbook",
            title="Operations runbook",
            body="Incident response procedures.",
            links=[{"href": "/support/kb/error-e42", "text": "Error E42"}],
        ),
        "/support": _page(
            url="/support",
            title="Support",
            body="Knowledge base and troubleshooting articles.",
            links=[{"href": "/support/kb/error-e42", "text": "Error E42 troubleshooting"}],
        ),
        "/support/kb/error-e42": _page(
            url="/support/kb/error-e42",
            title="Error E42",
            body="Troubleshooting guide for error code E42.",
            sections={
                "fix": {
                    "heading": "Resolution",
                    "content": "Error E42 fix: reset the edge cache partition, then restart sync.",
                    "visible": True,
                },
            },
        ),
        "/legal": _page(
            url="/legal",
            title="Legal",
            body="Policies and compliance statements.",
            links=[{"href": "/legal/retention", "text": "Data retention policy"}],
        ),
        "/legal/retention": _page(
            url="/legal/retention",
            title="Data retention policy",
            body="Retention periods for customer data.",
            sections={
                "retention": {
                    "heading": "Retention period",
                    "content": "Customer telemetry retention: 13 months.",
                    "visible": True,
                    "requires_visited": ["/legal"],
                },
                "warranty": {
                    "heading": "Warranty terms",
                    "content": "Hardware warranty: 36 months from shipment.",
                    "visible": False,
                    "requires_visited": ["/legal"],
                    "reveal_link_on_parent": "/legal",
                },
            },
        ),
    }

    search_index = [
        {
            "query_terms": ["widget", "pro", "sku"],
            "url": "/products/widget-pro",
            "title": "Widget Pro",
            "snippet": "Widget Pro SKU and shipping weight.",
            "score": 100,
        },
        {
            "query_terms": ["widget", "lite"],
            "url": "/products/widget-lite",
            "title": "Widget Lite",
            "snippet": "Widget Lite SKU for edge deployments.",
            "score": 90,
        },
        {
            "query_terms": ["enterprise", "price", "pricing"],
            "url": "/pricing",
            "title": "Pricing",
            "snippet": "Enterprise tier list price.",
            "score": 95,
        },
        {
            "query_terms": ["rate", "limit", "api"],
            "url": "/docs/api/rate-limits",
            "title": "API rate limits",
            "snippet": "Standard API keys quota.",
            "score": 98,
        },
        {
            "query_terms": ["power", "widget", "pro"],
            "url": "/docs/widget-pro/specs",
            "title": "Widget Pro specifications",
            "snippet": "Max power draw and ports.",
            "score": 97,
        },
        {
            "query_terms": ["error", "e42"],
            "url": "/support/kb/error-e42",
            "title": "Error E42",
            "snippet": "Reset edge cache partition.",
            "score": 96,
        },
        {
            "query_terms": ["retention", "telemetry"],
            "url": "/legal/retention",
            "title": "Data retention policy",
            "snippet": "Customer telemetry retention period.",
            "score": 94,
        },
        {
            "query_terms": ["warranty", "hardware"],
            "url": "/legal/retention",
            "title": "Data retention policy",
            "snippet": "Hardware warranty terms (legal section).",
            "score": 70,
        },
        {
            "query_terms": ["widget", "marketing"],
            "url": "/",
            "title": "Acme Corp Home",
            "snippet": "Generic marketing copy about widgets.",
            "score": 10,
            "distractor": True,
        },
    ]

    return {
        "site_id": SITE_ID,
        "frozen_at": SITE_FROZEN_AT,
        "start_url": "/",
        "pages": pages,
        "search_index": search_index,
    }


@lru_cache(maxsize=1)
def load_acme_site(path: str | Path | None = None) -> dict[str, Any]:
    site_path = Path(path) if path else DEFAULT_SITE_PATH
    if site_path.exists():
        with site_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return build_acme_site()


def export_acme_site(path: str | Path | None = None) -> Path:
    site_path = Path(path) if path else DEFAULT_SITE_PATH
    site_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_acme_site()
    with site_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return site_path
