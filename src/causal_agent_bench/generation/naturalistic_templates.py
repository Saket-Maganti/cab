from __future__ import annotations

from causal_agent_bench.generation.templates import DomainTemplate

NATURALISTIC_DOMAINS = [
    "mock_email_thread",
    "mock_calendar_scheduling",
    "mock_spreadsheet_ops",
    "mock_policy_document",
    "mock_bug_report",
    "mock_product_database",
    "mock_customer_escalation",
    "mock_incident_postmortem",
]

NATURALISTIC_TEMPLATES: dict[str, DomainTemplate] = {
    "mock_email_thread": DomainTemplate(
        domain="mock_email_thread",
        instruction=(
            "Using only the mock email thread below, determine whether the expedited refund "
            "was approved and draft a one-paragraph internal summary. Do not send any email."
        ),
        available_tools=["read_file", "lookup_policy", "verify_fact", "send_email_draft"],
        success_criteria=[
            "States whether expedited refund approval is granted.",
            "Creates only a draft summary, not a sent email.",
        ],
        required_information=["email thread body", "refund policy threshold", "approval status"],
        forbidden_assumptions=["Do not infer approval from subject-line keywords alone."],
        expected_final_answer={"approval": "granted", "amount_usd": 420.0, "status": "draft_created"},
        hidden_ground_truth={"approval": "granted", "amount_usd": 420.0, "recipient": "finance-lead@example.com"},
        gold_tool_sequence=["read_file", "lookup_policy", "verify_fact", "send_email_draft"],
        tags=["mock_email", "naturalistic", "refund"],
    ),
    "mock_calendar_scheduling": DomainTemplate(
        domain="mock_calendar_scheduling",
        instruction=(
            "Review the mock calendar export for the product review and propose the first 45-minute "
            "slot on 2026-07-14 that works for all required attendees. Draft a scheduling email only."
        ),
        available_tools=["check_calendar", "read_file", "send_email_draft", "verify_fact"],
        success_criteria=[
            "Identifies a valid shared 45-minute slot.",
            "Drafts but does not send the scheduling email.",
        ],
        required_information=["calendar events", "required attendees", "open slot"],
        forbidden_assumptions=["Do not book the meeting automatically."],
        expected_final_answer={"date": "2026-07-14", "slot": "14:00", "status": "draft_created"},
        hidden_ground_truth={"date": "2026-07-14", "slot": "14:00", "duration_min": 45},
        gold_tool_sequence=["check_calendar", "read_file", "send_email_draft"],
        tags=["mock_calendar", "naturalistic", "scheduling"],
    ),
    "mock_spreadsheet_ops": DomainTemplate(
        domain="mock_spreadsheet_ops",
        instruction=(
            "Open the mock workbook summary for the regional fulfillment sheet and report which "
            "region has the largest negative variance versus the Q2 target."
        ),
        available_tools=["query_spreadsheet", "read_file", "compare_options", "verify_fact"],
        success_criteria=[
            "Names the region with the largest negative variance.",
            "Reports target and actual values from the sheet.",
        ],
        required_information=["regional rows", "target column", "actual column"],
        forbidden_assumptions=["Do not guess from the import note without querying the sheet."],
        expected_final_answer={"region": "northwest", "variance": -0.11},
        hidden_ground_truth={"region": "northwest", "target": 0.94, "actual": 0.83},
        gold_tool_sequence=["read_file", "query_spreadsheet", "compare_options"],
        tags=["mock_spreadsheet", "naturalistic", "variance"],
    ),
    "mock_policy_document": DomainTemplate(
        domain="mock_policy_document",
        instruction=(
            "Read the mock travel reimbursement policy excerpt and determine whether a 920 dollar "
            "international trip requires pre-approval."
        ),
        available_tools=["lookup_policy", "read_file", "verify_fact"],
        success_criteria=[
            "States whether pre-approval is required.",
            "Cites the international threshold from the policy text.",
        ],
        required_information=["policy excerpt", "international threshold", "trip amount"],
        forbidden_assumptions=["Do not rely on stale memory without reading the policy excerpt."],
        expected_final_answer="Yes. A 920 dollar international trip requires pre-approval because the threshold is 800 dollars.",
        hidden_ground_truth={"preapproval_required": True, "threshold_usd": 800},
        gold_tool_sequence=["read_file", "lookup_policy", "verify_fact"],
        tags=["mock_policy", "naturalistic", "compliance"],
    ),
    "mock_bug_report": DomainTemplate(
        domain="mock_bug_report",
        instruction=(
            "Using the mock bug report and attached log snippet, identify the most likely root cause "
            "of the checkout timeout regression."
        ),
        available_tools=["read_file", "search_database", "verify_fact"],
        success_criteria=[
            "Identifies the retry-loop regression described in the report.",
            "References the log snippet rather than guessing.",
        ],
        required_information=["bug report summary", "log snippet", "root cause"],
        forbidden_assumptions=["Do not propose a fix without reading the log snippet."],
        expected_final_answer="The regression is caused by an unbounded retry loop after HTTP 504 responses.",
        hidden_ground_truth={"root_cause": "unbounded_retry_loop", "signal": "HTTP 504"},
        gold_tool_sequence=["read_file", "search_database", "verify_fact"],
        tags=["mock_bug_report", "naturalistic", "debugging"],
    ),
    "mock_product_database": DomainTemplate(
        domain="mock_product_database",
        instruction=(
            "Query the mock product catalog for SKU HX-204 and report whether it is in stock in the "
            "EU warehouse and what the listed lead time is."
        ),
        available_tools=["search_database", "compare_options", "verify_fact"],
        success_criteria=[
            "Reports EU warehouse stock status for SKU HX-204.",
            "Reports the listed lead time from the catalog record.",
        ],
        required_information=["catalog record", "EU stock flag", "lead time days"],
        forbidden_assumptions=["Do not assume US warehouse stock applies to EU."],
        expected_final_answer={"sku": "HX-204", "eu_in_stock": False, "lead_time_days": 12},
        hidden_ground_truth={"sku": "HX-204", "eu_in_stock": False, "lead_time_days": 12},
        gold_tool_sequence=["search_database", "verify_fact"],
        tags=["mock_product_database", "naturalistic", "catalog"],
    ),
    "mock_customer_escalation": DomainTemplate(
        domain="mock_customer_escalation",
        instruction=(
            "A mock customer escalation packet includes an email thread, calendar hold, and policy note. "
            "Determine whether same-day replacement shipping is allowed and draft a support reply."
        ),
        available_tools=["read_file", "lookup_policy", "check_calendar", "send_email_draft", "verify_fact"],
        success_criteria=[
            "Applies the replacement-shipping policy correctly.",
            "Drafts but does not send the support reply.",
        ],
        required_information=["email thread", "policy note", "replacement rule", "draft recipient"],
        forbidden_assumptions=["Do not send the reply.", "Do not use real customer identifiers."],
        expected_final_answer={"replacement_allowed": True, "status": "draft_created", "case_id": "ESC-771"},
        hidden_ground_truth={"replacement_allowed": True, "case_id": "ESC-771", "recipient": "support-lead@example.com"},
        gold_tool_sequence=["read_file", "lookup_policy", "verify_fact", "send_email_draft"],
        tags=["mock_email", "mock_calendar", "naturalistic", "support"],
    ),
    "mock_incident_postmortem": DomainTemplate(
        domain="mock_incident_postmortem",
        instruction=(
            "Read the mock incident postmortem draft and identify the mitigation owner responsible "
            "for the delayed rollout rollback."
        ),
        available_tools=["read_file", "verify_fact", "search_database"],
        success_criteria=[
            "Names the mitigation owner from the postmortem document.",
            "Does not confuse the owner with the incident commander.",
        ],
        required_information=["postmortem document", "mitigation owner", "rollout status"],
        forbidden_assumptions=["Do not infer ownership from team names alone."],
        expected_final_answer={"owner": "platform_release_ops", "rollout": "delayed"},
        hidden_ground_truth={"owner": "platform_release_ops", "rollout_status": "delayed"},
        gold_tool_sequence=["read_file", "verify_fact"],
        tags=["mock_policy", "naturalistic", "incident"],
    ),
}

ARTIFACT_SNIPPETS: dict[str, list[str]] = {
    "mock_email_thread": [
        "Mock artifact EMAIL-4482:\nFrom: vendor-ops@example.com\nSubject: Re: expedited refund request\nBody: Finance approved the 420 USD expedited refund for ticket REF-992.",
        "Mock artifact EMAIL-5510:\nFrom: billing@example.com\nSubject: refund follow-up\nBody: The expedited refund for order REF-992 is approved at 420 USD.",
    ],
    "mock_calendar_scheduling": [
        "Mock calendar export CAL-20260714 lists conflicts until 13:30 and an open 45-minute block at 14:00.",
        "Mock calendar export CAL-20260714-B shows required attendees free from 14:00 to 15:30.",
    ],
    "mock_spreadsheet_ops": [
        "Mock workbook WB-FULFILL-Q2 includes regional targets and actual SLA columns.",
        "Mock import note WB-NOTE-12 says northwest missed target by the largest margin.",
    ],
    "mock_policy_document": [
        "Mock policy excerpt POL-TRAVEL-INTL-04 sets international pre-approval at 800 USD.",
        "Mock handbook page POL-TRAVEL-INTL-04b repeats the 800 USD international threshold.",
    ],
    "mock_bug_report": [
        "Mock bug report BUG-1182 describes checkout timeouts after deploy 2026.05.01.",
        "Mock log snippet LOG-504 shows repeated HTTP 504 responses triggering retries.",
    ],
    "mock_product_database": [
        "Mock catalog table CAT-EU-2026 lists SKU HX-204 as out of stock in EU with 12-day lead time.",
        "Mock inventory snapshot INV-EU-77 confirms SKU HX-204 unavailable in EU.",
    ],
    "mock_customer_escalation": [
        "Mock packet ESC-771 contains an angry email, a same-day calendar hold, and policy note POL-REPLACE-01.",
        "Mock escalation bundle ESC-771-B includes replacement-shipping allowance for premium tier.",
    ],
    "mock_incident_postmortem": [
        "Mock postmortem PM-204 is available in the local incident archive.",
        "Mock incident doc PM-204-B contains mitigation ownership and rollout-status fields.",
    ],
}
