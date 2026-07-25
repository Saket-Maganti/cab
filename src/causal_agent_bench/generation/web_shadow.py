from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from causal_agent_bench.generation.base_tasks import _difficulty_plan, _partial_credit_criteria
from causal_agent_bench.generation.web_shadow_site import load_acme_site
from causal_agent_bench.schemas import BaseTask, InterventionType, TaskGoal

API_TOOLS = ["search_database", "read_file", "lookup_policy", "verify_fact"]
WEB_TOOLS = ["web_open_page", "web_follow_link", "web_search_snapshot", "web_extract_section"]

API_MIRROR_FAMILIES: list[InterventionType] = [
    "tool_failure",
    "tool_corruption",
    "observation_conflict",
    "distractor_evidence",
    "long_horizon_dependency",
]


@dataclass(frozen=True)
class WebShadowScenario:
    key: str
    domain: str
    instruction: str
    expected_answer: str
    success_criteria: list[str]
    required_information: list[str]
    navigation: dict[str, Any]
    oracle_tool_args: dict[str, dict[str, Any]]
    gold_web_sequence: list[str]
    gold_api_sequence: list[str]
    api_mock: dict[str, Any]
    tags: list[str]
    oracle_tool_calls: list[dict[str, Any]] | None = None


def _scenarios() -> list[WebShadowScenario]:
    """25 navigation scenarios over the frozen Acme snapshot."""

    def web_nav(
        *,
        start: str = "/",
        follow: str | None = None,
        target: str,
        search_query: str | None = None,
        section_id: str | None = None,
        broken_href: str | None = None,
        stale_page_url: str | None = None,
        conflict_page_url: str | None = None,
        hidden_section: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "start_url": start,
            "follow_href": follow,
            "target_url": target,
            "search_query": search_query,
            "section_id": section_id,
            "broken_href": broken_href or follow or target,
            "stale_page_url": stale_page_url or target,
            "conflict_page_url": conflict_page_url or target,
            "hidden_section": hidden_section or {},
        }

    rows: list[WebShadowScenario] = [
        WebShadowScenario(
            key="widget_pro_sku",
            domain="web_shadow_product",
            instruction="Find the Widget Pro SKU from the product pages in the frozen site snapshot.",
            expected_answer="WDG-PRO-2024",
            success_criteria=["States SKU WDG-PRO-2024"],
            required_information=["sku"],
            navigation=web_nav(start="/products", follow="/products/widget-pro", target="/products/widget-pro", section_id="sku"),
            oracle_tool_args={
                "web_open_page": {"url": "/products"},
                "web_follow_link": {"href": "/products/widget-pro"},
                "web_extract_section": {"section_id": "sku"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("widget pro sku", "WDG-PRO-2024"),
            tags=["product", "navigation"],
        ),
        WebShadowScenario(
            key="widget_pro_weight",
            domain="web_shadow_product",
            instruction="What is the shipping weight for Widget Pro?",
            expected_answer="2.4 kg",
            success_criteria=["Reports shipping weight 2.4 kg"],
            required_information=["weight"],
            navigation=web_nav(start="/products/widget-pro", target="/products/widget-pro", section_id="weight"),
            oracle_tool_args={
                "web_open_page": {"url": "/products/widget-pro"},
                "web_extract_section": {"section_id": "weight"},
            },
            gold_web_sequence=["web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("widget pro weight", "2.4 kg"),
            tags=["product"],
        ),
        WebShadowScenario(
            key="enterprise_price",
            domain="web_shadow_pricing",
            instruction="What is the enterprise tier list price on the pricing page?",
            expected_answer="$48,000 per year",
            success_criteria=["States enterprise price $48,000 per year"],
            required_information=["enterprise_price"],
            navigation=web_nav(start="/pricing", target="/pricing", section_id="enterprise"),
            oracle_tool_args={
                "web_open_page": {"url": "/pricing"},
                "web_extract_section": {"section_id": "enterprise"},
            },
            gold_web_sequence=["web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "read_file"],
            api_mock=_api_records("enterprise price", "$48,000 per year"),
            tags=["pricing"],
        ),
        WebShadowScenario(
            key="api_rate_limit",
            domain="web_shadow_docs",
            instruction="What is the standard API rate limit in requests per minute?",
            expected_answer="1200 requests per minute",
            success_criteria=["States 1200 requests per minute"],
            required_information=["api_quota"],
            navigation=web_nav(
                start="/docs",
                follow="/docs/api/rate-limits",
                target="/docs/api/rate-limits",
                section_id="quota",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/docs"},
                "web_follow_link": {"href": "/docs/api/rate-limits"},
                "web_extract_section": {"section_id": "quota"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["read_file", "verify_fact"],
            api_mock=_api_file("api_rate_limits.txt", "Standard API keys: 1200 requests per minute."),
            tags=["docs"],
        ),
        WebShadowScenario(
            key="widget_power_draw",
            domain="web_shadow_docs",
            instruction="What is the maximum power draw for Widget Pro under load?",
            expected_answer="18W",
            success_criteria=["States max power draw 18W"],
            required_information=["power"],
            navigation=web_nav(
                start="/docs/widget-pro/specs",
                target="/docs/widget-pro/specs",
                section_id="power",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/docs/widget-pro/specs"},
                "web_extract_section": {"section_id": "power"},
            },
            gold_web_sequence=["web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("widget pro power", "18W"),
            tags=["docs", "product"],
        ),
        WebShadowScenario(
            key="error_e42_fix",
            domain="web_shadow_support",
            instruction="How do you fix error E42 according to the support knowledge base?",
            expected_answer="reset the edge cache partition, then restart sync",
            success_criteria=["Mentions reset edge cache partition and restart sync"],
            required_information=["fix_steps"],
            navigation=web_nav(
                start="/support",
                follow="/support/kb/error-e42",
                target="/support/kb/error-e42",
                section_id="fix",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/support"},
                "web_follow_link": {"href": "/support/kb/error-e42"},
                "web_extract_section": {"section_id": "fix"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["read_file", "verify_fact"],
            api_mock=_api_file("error_e42.md", "Reset the edge cache partition, then restart sync."),
            tags=["support"],
        ),
        WebShadowScenario(
            key="telemetry_retention",
            domain="web_shadow_legal",
            instruction="What is the customer telemetry retention period?",
            expected_answer="13 months",
            success_criteria=["States retention 13 months"],
            required_information=["retention"],
            navigation=web_nav(
                start="/legal",
                follow="/legal/retention",
                target="/legal/retention",
                section_id="retention",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/legal"},
                "web_follow_link": {"href": "/legal/retention"},
                "web_extract_section": {"section_id": "retention"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["lookup_policy", "verify_fact"],
            api_mock=_api_policy("retention", "Customer telemetry retention: 13 months."),
            tags=["legal"],
        ),
        WebShadowScenario(
            key="hardware_warranty",
            domain="web_shadow_legal",
            instruction="What is the hardware warranty period? You may need to navigate legal pages.",
            expected_answer="36 months",
            success_criteria=["States hardware warranty 36 months"],
            required_information=["warranty"],
            navigation=web_nav(
                start="/legal",
                follow="/legal/retention",
                target="/legal/retention",
                section_id="warranty",
                hidden_section={"page": "/legal/retention", "section_id": "warranty"},
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/legal"},
                "web_follow_link": {"href": "/legal/retention"},
                "web_extract_section": {"section_id": "warranty"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["lookup_policy", "read_file", "verify_fact"],
            api_mock=_api_policy("warranty", "Hardware warranty: 36 months from shipment."),
            tags=["legal", "multi_hop"],
        ),
        WebShadowScenario(
            key="search_widget_pro",
            domain="web_shadow_search",
            instruction="Use site search to find Widget Pro SKU information.",
            expected_answer="WDG-PRO-2024",
            success_criteria=["States SKU WDG-PRO-2024 after search"],
            required_information=["sku"],
            navigation=web_nav(search_query="widget pro sku", target="/products/widget-pro", section_id="sku"),
            oracle_tool_args={
                "web_search_snapshot": {"query": "widget pro sku"},
                "web_open_page": {"url": "/products/widget-pro"},
                "web_extract_section": {"section_id": "sku"},
            },
            gold_web_sequence=["web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("widget pro sku search", "WDG-PRO-2024"),
            tags=["search"],
        ),
        WebShadowScenario(
            key="search_enterprise_pricing",
            domain="web_shadow_search",
            instruction="Use site search to find the enterprise tier list price.",
            expected_answer="$48,000 per year",
            success_criteria=["States enterprise price after search navigation"],
            required_information=["enterprise_price"],
            navigation=web_nav(search_query="enterprise price", target="/pricing", section_id="enterprise"),
            oracle_tool_args={
                "web_search_snapshot": {"query": "enterprise price"},
                "web_open_page": {"url": "/pricing"},
                "web_extract_section": {"section_id": "enterprise"},
            },
            gold_web_sequence=["web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "read_file"],
            api_mock=_api_records("enterprise pricing", "$48,000 per year"),
            tags=["search", "pricing"],
        ),
        WebShadowScenario(
            key="lite_sku",
            domain="web_shadow_product",
            instruction="Find the Widget Lite SKU.",
            expected_answer="WDG-LITE-2024",
            success_criteria=["States SKU WDG-LITE-2024"],
            required_information=["sku"],
            navigation=web_nav(start="/products", follow="/products/widget-lite", target="/products/widget-lite", section_id="sku"),
            oracle_tool_args={
                "web_open_page": {"url": "/products"},
                "web_follow_link": {"href": "/products/widget-lite"},
                "web_extract_section": {"section_id": "sku"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("widget lite sku", "WDG-LITE-2024"),
            tags=["product"],
        ),
        WebShadowScenario(
            key="lite_tier_price",
            domain="web_shadow_pricing",
            instruction="What is the Lite tier list price?",
            expected_answer="$1,200 per year",
            success_criteria=["States lite tier $1,200 per year"],
            required_information=["lite_price"],
            navigation=web_nav(start="/pricing", target="/pricing", section_id="lite"),
            oracle_tool_args={
                "web_open_page": {"url": "/pricing"},
                "web_extract_section": {"section_id": "lite"},
            },
            gold_web_sequence=["web_open_page", "web_extract_section"],
            gold_api_sequence=["read_file", "verify_fact"],
            api_mock=_api_records("lite tier price", "$1,200 per year"),
            tags=["pricing"],
        ),
        WebShadowScenario(
            key="enterprise_features",
            domain="web_shadow_product",
            instruction="List a flagship enterprise suite feature mentioned on its product page.",
            expected_answer="SSO",
            success_criteria=["Mentions SSO or audit logging or 99.95% SLA"],
            required_information=["features"],
            navigation=web_nav(
                start="/products/enterprise-suite",
                target="/products/enterprise-suite",
                section_id="features",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/products/enterprise-suite"},
                "web_extract_section": {"section_id": "features"},
            },
            gold_web_sequence=["web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("enterprise suite", "SSO, audit logging, 99.95% SLA"),
            tags=["product"],
        ),
        WebShadowScenario(
            key="widget_ports",
            domain="web_shadow_docs",
            instruction="How many Gigabit Ethernet ports does Widget Pro have?",
            expected_answer="2",
            success_criteria=["States 2 Gigabit Ethernet ports"],
            required_information=["ports"],
            navigation=web_nav(
                start="/docs/widget-pro/specs",
                target="/docs/widget-pro/specs",
                section_id="ports",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/docs/widget-pro/specs"},
                "web_extract_section": {"section_id": "ports"},
            },
            gold_web_sequence=["web_open_page", "web_extract_section"],
            gold_api_sequence=["read_file", "verify_fact"],
            api_mock=_api_file("widget_pro_ports.txt", "2x Gigabit Ethernet"),
            tags=["docs"],
        ),
        WebShadowScenario(
            key="home_to_products",
            domain="web_shadow_navigation",
            instruction="Start from the home page and navigate to the products index.",
            expected_answer="Products",
            success_criteria=["Identifies products index page"],
            required_information=["page_title"],
            navigation=web_nav(start="/", follow="/products", target="/products"),
            oracle_tool_args={
                "web_open_page": {"url": "/"},
                "web_follow_link": {"href": "/products"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link"],
            gold_api_sequence=["search_database"],
            api_mock=_api_records("products index", "Products catalog"),
            tags=["navigation"],
        ),
        WebShadowScenario(
            key="docs_hub",
            domain="web_shadow_navigation",
            instruction="Open the documentation hub and report its page title.",
            expected_answer="Documentation hub",
            success_criteria=["Reports documentation hub title"],
            required_information=["title"],
            navigation=web_nav(start="/", follow="/docs", target="/docs"),
            oracle_tool_args={"web_open_page": {"url": "/"}, "web_follow_link": {"href": "/docs"}},
            gold_web_sequence=["web_open_page", "web_follow_link"],
            gold_api_sequence=["read_file"],
            api_mock=_api_file("docs_hub.txt", "Documentation hub"),
            tags=["navigation", "docs"],
        ),
        WebShadowScenario(
            key="pricing_from_suite",
            domain="web_shadow_navigation",
            instruction="From the enterprise suite product page, navigate to pricing.",
            expected_answer="$48,000 per year",
            success_criteria=["Finds enterprise tier price after cross-page navigation"],
            required_information=["enterprise_price"],
            navigation=web_nav(
                start="/products/enterprise-suite",
                follow="/pricing",
                target="/pricing",
                section_id="enterprise",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/products/enterprise-suite"},
                "web_follow_link": {"href": "/pricing"},
                "web_extract_section": {"section_id": "enterprise"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["search_database", "read_file"],
            api_mock=_api_records("enterprise suite pricing", "$48,000 per year"),
            tags=["navigation", "pricing"],
        ),
        WebShadowScenario(
            key="runbook_to_e42",
            domain="web_shadow_navigation",
            instruction="From the operations runbook, navigate to the Error E42 article.",
            expected_answer="reset the edge cache partition",
            success_criteria=["Finds E42 fix via runbook link"],
            required_information=["fix_steps"],
            navigation=web_nav(
                start="/docs/ops/runbook",
                follow="/support/kb/error-e42",
                target="/support/kb/error-e42",
                section_id="fix",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/docs/ops/runbook"},
                "web_follow_link": {"href": "/support/kb/error-e42"},
                "web_extract_section": {"section_id": "fix"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["read_file", "verify_fact"],
            api_mock=_api_file("runbook_e42.txt", "Reset edge cache partition"),
            tags=["navigation", "support"],
        ),
        WebShadowScenario(
            key="search_rate_limit",
            domain="web_shadow_search",
            instruction="Search the snapshot for API rate limits and report the quota.",
            expected_answer="1200 requests per minute",
            success_criteria=["Reports 1200 requests per minute from search path"],
            required_information=["api_quota"],
            navigation=web_nav(search_query="api rate limit", target="/docs/api/rate-limits", section_id="quota"),
            oracle_tool_args={
                "web_search_snapshot": {"query": "api rate limit"},
                "web_open_page": {"url": "/docs/api/rate-limits"},
                "web_extract_section": {"section_id": "quota"},
            },
            gold_web_sequence=["web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("api rate limit", "1200 requests per minute"),
            tags=["search", "docs"],
        ),
        WebShadowScenario(
            key="search_retention",
            domain="web_shadow_search",
            instruction="Search for telemetry retention and report the period.",
            expected_answer="13 months",
            success_criteria=["States 13 months retention"],
            required_information=["retention"],
            navigation=web_nav(search_query="telemetry retention", target="/legal/retention", section_id="retention"),
            oracle_tool_args={
                "web_search_snapshot": {"query": "telemetry retention"},
                "web_open_page": {"url": "/legal/retention"},
                "web_extract_section": {"section_id": "retention"},
            },
            gold_web_sequence=["web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "lookup_policy"],
            api_mock=_api_records("telemetry retention", "13 months"),
            tags=["search", "legal"],
        ),
        WebShadowScenario(
            key="search_error_e42",
            domain="web_shadow_search",
            instruction="Search for error E42 and summarize the fix.",
            expected_answer="reset the edge cache partition",
            success_criteria=["Summarizes E42 fix from search navigation"],
            required_information=["fix_steps"],
            navigation=web_nav(search_query="error e42", target="/support/kb/error-e42", section_id="fix"),
            oracle_tool_args={
                "web_search_snapshot": {"query": "error e42"},
                "web_open_page": {"url": "/support/kb/error-e42"},
                "web_extract_section": {"section_id": "fix"},
            },
            gold_web_sequence=["web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "read_file"],
            api_mock=_api_records("error e42", "reset edge cache partition"),
            tags=["search", "support"],
        ),
        WebShadowScenario(
            key="open_support_home",
            domain="web_shadow_navigation",
            instruction="Open the support section landing page and name it.",
            expected_answer="Support",
            success_criteria=["Identifies Support page"],
            required_information=["title"],
            navigation=web_nav(start="/", follow="/support", target="/support"),
            oracle_tool_args={"web_open_page": {"url": "/"}, "web_follow_link": {"href": "/support"}},
            gold_web_sequence=["web_open_page", "web_follow_link"],
            gold_api_sequence=["read_file"],
            api_mock=_api_file("support_home.txt", "Support knowledge base"),
            tags=["navigation", "support"],
        ),
        WebShadowScenario(
            key="legal_index",
            domain="web_shadow_navigation",
            instruction="Navigate from home to the legal index page.",
            expected_answer="Legal",
            success_criteria=["Identifies Legal page"],
            required_information=["title"],
            navigation=web_nav(start="/", follow="/legal", target="/legal"),
            oracle_tool_args={"web_open_page": {"url": "/"}, "web_follow_link": {"href": "/legal"}},
            gold_web_sequence=["web_open_page", "web_follow_link"],
            gold_api_sequence=["lookup_policy"],
            api_mock=_api_policy("legal_index", "Legal policies"),
            tags=["navigation", "legal"],
        ),
        WebShadowScenario(
            key="product_to_specs",
            domain="web_shadow_navigation",
            instruction="From Widget Pro product page, open the full specifications doc.",
            expected_answer="18W",
            success_criteria=["Navigates to specs and reports power draw"],
            required_information=["power"],
            navigation=web_nav(
                start="/products/widget-pro",
                follow="/docs/widget-pro/specs",
                target="/docs/widget-pro/specs",
                section_id="power",
            ),
            oracle_tool_args={
                "web_open_page": {"url": "/products/widget-pro"},
                "web_follow_link": {"href": "/docs/widget-pro/specs"},
                "web_extract_section": {"section_id": "power"},
            },
            gold_web_sequence=["web_open_page", "web_follow_link", "web_extract_section"],
            gold_api_sequence=["read_file", "search_database"],
            api_mock=_api_records("widget pro specs power", "18W"),
            tags=["navigation", "docs"],
        ),
        WebShadowScenario(
            key="search_warranty",
            domain="web_shadow_search",
            instruction="Search for hardware warranty and report the duration (navigate legal pages if needed).",
            expected_answer="36 months",
            success_criteria=["Reports 36 month hardware warranty"],
            required_information=["warranty"],
            navigation=web_nav(
                search_query="hardware warranty",
                target="/legal/retention",
                section_id="warranty",
                hidden_section={"page": "/legal/retention", "section_id": "warranty"},
            ),
            oracle_tool_args={
                "web_search_snapshot": {"query": "hardware warranty"},
                "web_open_page": {"url": "/legal/retention"},
                "web_extract_section": {"section_id": "warranty"},
            },
            gold_web_sequence=["web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["lookup_policy", "verify_fact"],
            api_mock=_api_policy("hardware_warranty", "36 months from shipment"),
            tags=["search", "legal", "multi_hop"],
        ),
        WebShadowScenario(
            key="widget_pro_from_search_page",
            domain="web_shadow_navigation",
            instruction="Open the search page, then find Widget Pro via search results.",
            expected_answer="WDG-PRO-2024",
            success_criteria=["Uses search page flow to reach Widget Pro SKU"],
            required_information=["sku"],
            navigation=web_nav(
                start="/search",
                search_query="widget pro",
                target="/products/widget-pro",
                section_id="sku",
            ),
            oracle_tool_args={},
            oracle_tool_calls=[
                {"tool": "web_open_page", "arguments": {"url": "/search"}},
                {"tool": "web_search_snapshot", "arguments": {"query": "widget pro"}},
                {"tool": "web_open_page", "arguments": {"url": "/products/widget-pro"}},
                {"tool": "web_extract_section", "arguments": {"section_id": "sku"}},
            ],
            gold_web_sequence=["web_open_page", "web_search_snapshot", "web_open_page", "web_extract_section"],
            gold_api_sequence=["search_database", "verify_fact"],
            api_mock=_api_records("widget pro from search", "WDG-PRO-2024"),
            tags=["search", "navigation"],
        ),
    ]
    if len(rows) < 25:
        raise ValueError(f"expected at least 25 web shadow scenarios, got {len(rows)}")
    return rows[:25]


def _api_records(query_hint: str, answer: str) -> dict[str, Any]:
    return {
        "records": [
            {
                "id": f"rec_{stable_token(query_hint)}",
                "domain": "web_shadow_api",
                "title": query_hint,
                "summary": answer,
            }
        ],
        "evidence": {f"ev_{stable_token(query_hint)}": {"text": answer, "supports": True}},
    }


def _api_file(file_id: str, content: str) -> dict[str, Any]:
    return {"files": {file_id: content}, "evidence": {file_id: {"text": content, "supports": True}}}


def _api_policy(name: str, text: str) -> dict[str, Any]:
    return {
        "policies": {name: {"text": text, "clauses": [{"id": f"{name}-1", "text": text}]}},
        "evidence": {name: {"text": text, "supports": True}},
    }


def stable_token(text: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in text.lower())[:24]


def generate_web_shadow_base_tasks(
    seed: int,
    num_base_tasks: int = 50,
    *,
    include_api_mirror: bool = True,
    include_web_snapshot: bool = True,
) -> list[BaseTask]:
    """Generate paired API-interface and web-snapshot-interface tasks."""

    scenarios = _scenarios()
    rng = random.Random(seed)
    site = load_acme_site()
    tasks: list[BaseTask] = []
    difficulty_plan = _difficulty_plan(rng, len(scenarios), {"easy": 0.2, "medium": 0.4, "hard": 0.25, "stress": 0.15})

    for index, scenario in enumerate(scenarios):
        difficulty = difficulty_plan[index % len(difficulty_plan)]
        if include_web_snapshot:
            tasks.append(_build_task(scenario, site, interface="web_snapshot", difficulty=difficulty, variant=index))
        if include_api_mirror:
            tasks.append(_build_task(scenario, site, interface="api", difficulty=difficulty, variant=index))

    if num_base_tasks and len(tasks) > num_base_tasks:
        tasks = tasks[:num_base_tasks]
    return tasks


def _build_task(
    scenario: WebShadowScenario,
    site: dict[str, Any],
    *,
    interface: str,
    difficulty: str,
    variant: int,
) -> BaseTask:
    is_web = interface == "web_snapshot"
    tools = WEB_TOOLS if is_web else API_TOOLS
    gold_sequence = scenario.gold_web_sequence if is_web else scenario.gold_api_sequence
    task_id = f"webshadow_{interface}_{scenario.key}_{difficulty}"
    nav = dict(scenario.navigation)
    nav["start_url"] = nav.get("start_url", site.get("start_url", "/"))

    hidden: dict[str, Any] = {
        "expected_final_answer": scenario.expected_answer,
        "navigation": nav,
        "oracle_tool_args": scenario.oracle_tool_args,
        "web_site": site,
        "api_mock": scenario.api_mock,
        "tool_interface": interface,
    }
    if scenario.oracle_tool_calls:
        hidden["oracle_tool_calls"] = list(scenario.oracle_tool_calls)
    instruction = (
        f"{scenario.instruction}\n\n"
        f"Interface: {'static web snapshot tools only (no live browsing)' if is_web else 'simulated API tools only'}.\n"
        f"Difficulty: {difficulty}."
    )
    return BaseTask(
        task_id=task_id,
        domain=scenario.domain,
        difficulty=difficulty,
        goal=TaskGoal(
            user_instruction=instruction,
            success_criteria=list(scenario.success_criteria),
            required_information=list(scenario.required_information),
            forbidden_assumptions=["Using live web browsing or private data"],
            expected_final_answer=scenario.expected_answer,
        ),
        user_instruction=instruction,
        success_criteria=list(scenario.success_criteria),
        forbidden_assumptions=["Using live web browsing or private data"],
        available_tools=list(tools),
        required_tools=list(gold_sequence),
        optional_tools=[tool for tool in tools if tool not in gold_sequence],
        hidden_ground_truth=hidden,
        gold_tool_sequence=list(gold_sequence),
        partial_credit_criteria=_partial_credit_criteria(scenario.success_criteria),
        expected_evidence=list(scenario.required_information),
        max_steps=max(len(gold_sequence) + 2, 5),
        tags=[*scenario.tags, difficulty, "web_shadow", interface],
        metadata={
            "synthetic": True,
            "task_style": "web_shadow",
            "tool_interface": interface,
            "scenario_key": scenario.key,
            "web_site_id": site.get("site_id"),
            "web_site_frozen_at": site.get("frozen_at"),
            "generator_seed": variant,
            "mini_study_ready": True,
            "no_live_network": True,
        },
    )

