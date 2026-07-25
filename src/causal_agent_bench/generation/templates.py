from __future__ import annotations

from dataclasses import dataclass

DOMAINS = [
    "travel_planning",
    "calendar_email_workflow",
    "file_qa",
    "spreadsheet_qa",
    "shopping_comparison",
    "research_assistant",
    "policy_compliance",
    "coding_debugging",
    "operations_planning",
    "customer_support_workflow",
    "finance_admin_workflow",
    "data_cleaning_workflow",
]

PILOT_DOMAIN_ALIASES = {
    "travel": "travel",
    "travel_planning": "travel",
    "calendar_email": "calendar_email",
    "calendar_email_workflow": "calendar_email",
    "file_spreadsheet_qa": "file_spreadsheet",
    "file_spreadsheet": "file_spreadsheet",
    "file_qa": "file_qa",
    "spreadsheet_qa": "spreadsheet_qa",
    "operations_planning": "multi_hop_operations",
    "multi_hop_operations": "multi_hop_operations",
}

PUBLIC_PILOT_DOMAINS = list(DOMAINS)

DIFFICULTY_STEPS = {
    "easy": 1,
    "medium": 3,
    "hard": 5,
    "stress": 6,
}


@dataclass(frozen=True)
class DomainTemplate:
    domain: str
    instruction: str
    available_tools: list[str]
    success_criteria: list[str]
    required_information: list[str]
    forbidden_assumptions: list[str]
    expected_final_answer: str | dict
    hidden_ground_truth: dict
    gold_tool_sequence: list[str]
    tags: list[str]


TEMPLATES: dict[str, DomainTemplate] = {
    "travel": DomainTemplate(
        domain="travel",
        instruction="Find the best refundable Boston hotel option under the stated constraints and report the option id and total price.",
        available_tools=["search_database", "compare_options", "calculate_price"],
        success_criteria=[
            "Names the selected refundable hotel option.",
            "Includes the correct total price with tax.",
        ],
        required_information=["hotel refundability", "hotel price", "tax rate"],
        forbidden_assumptions=["Do not assume a non-refundable option is acceptable.", "Do not book anything."],
        expected_final_answer={"option_id": "saver_hotel", "total": 176.0},
        hidden_ground_truth={"best_option_id": "saver_hotel", "total": 176.0, "tax_rate": 0.1},
        gold_tool_sequence=["search_database", "compare_options", "calculate_price"],
        tags=["travel", "price_comparison", "refundability"],
    ),
    "calendar_email": DomainTemplate(
        domain="calendar_email",
        instruction="Check Mina's calendar on 2026-06-03 and draft an email proposing the first open afternoon slot.",
        available_tools=["check_calendar", "send_email_draft"],
        success_criteria=["Identifies the first open afternoon slot.", "Creates only a draft email."],
        required_information=["calendar events", "open afternoon slot", "recipient"],
        forbidden_assumptions=["Do not send the email.", "Do not assume morning slots satisfy the request."],
        expected_final_answer={"date": "2026-06-03", "slot": "15:00", "status": "draft_created"},
        hidden_ground_truth={"first_open_slot": "15:00", "recipient": "mina@example.com"},
        gold_tool_sequence=["check_calendar", "send_email_draft"],
        tags=["calendar", "email", "workflow"],
    ),
    "file_spreadsheet": DomainTemplate(
        domain="file_spreadsheet",
        instruction="Use the launch note and revenue spreadsheet to answer which launch is discussed and what Q2 revenue was.",
        available_tools=["read_file", "query_spreadsheet"],
        success_criteria=["Names the launch from the file.", "Reports Q2 revenue from the spreadsheet."],
        required_information=["launch note content", "Q2 spreadsheet row"],
        forbidden_assumptions=["Do not infer revenue without querying the spreadsheet."],
        expected_final_answer={"launch": "Beta", "q2_revenue": 4200},
        hidden_ground_truth={"launch": "Beta", "q2_revenue": 4200},
        gold_tool_sequence=["read_file", "query_spreadsheet"],
        tags=["file", "spreadsheet", "qa"],
    ),
    "file_qa": DomainTemplate(
        domain="file_qa",
        instruction="Read the incident summary and answer which mitigation owner is assigned to the delayed rollout.",
        available_tools=["read_file", "verify_fact", "search_database"],
        success_criteria=[
            "Names the mitigation owner from the file.",
            "Does not infer an owner from unrelated project names.",
        ],
        required_information=["incident summary content", "mitigation owner"],
        forbidden_assumptions=["Do not use project naming patterns as evidence."],
        expected_final_answer={"owner": "ops_review_team", "rollout": "delayed"},
        hidden_ground_truth={"owner": "ops_review_team", "rollout_status": "delayed"},
        gold_tool_sequence=["read_file", "verify_fact"],
        tags=["file", "qa", "incident"],
    ),
    "spreadsheet_qa": DomainTemplate(
        domain="spreadsheet_qa",
        instruction="Query the synthetic fulfillment sheet and report which region missed the SLA target by the largest margin.",
        available_tools=["query_spreadsheet", "compare_options", "verify_fact"],
        success_criteria=[
            "Identifies the region with the largest SLA miss.",
            "Reports the target and observed SLA values.",
        ],
        required_information=["regional SLA rows", "target SLA", "observed SLA"],
        forbidden_assumptions=["Do not average rows without querying the sheet."],
        expected_final_answer={"region": "west", "target_sla": 0.95, "observed_sla": 0.88},
        hidden_ground_truth={"region": "west", "target_sla": 0.95, "observed_sla": 0.88},
        gold_tool_sequence=["query_spreadsheet", "compare_options", "verify_fact"],
        tags=["spreadsheet", "qa", "sla"],
    ),
    "shopping_comparison": DomainTemplate(
        domain="shopping_comparison",
        instruction="Compare camera bundles A and B by total cost after tax and recommend the cheaper bundle.",
        available_tools=["compare_options", "calculate_price"],
        success_criteria=["Chooses the cheaper bundle.", "Reports total cost after tax."],
        required_information=["bundle prices", "tax rate"],
        forbidden_assumptions=["Do not ignore tax."],
        expected_final_answer={"option_id": "camera_b", "total": 216.0},
        hidden_ground_truth={"best_option_id": "camera_b", "total": 216.0, "tax_rate": 0.08},
        gold_tool_sequence=["compare_options", "calculate_price"],
        tags=["shopping", "comparison", "price"],
    ),
    "research_assistant": DomainTemplate(
        domain="research_assistant",
        instruction="Find evidence about whether the Apex report supports the claim that latency dropped below 100 ms.",
        available_tools=["search_database", "verify_fact"],
        success_criteria=["States whether the claim is supported.", "Cites the controlled evidence."],
        required_information=["Apex report evidence", "claim verification"],
        forbidden_assumptions=["Do not treat keyword overlap as support."],
        expected_final_answer="The claim is not supported; the report says 118 ms, not below 100 ms.",
        hidden_ground_truth={"claim_supported": False, "reported_latency_ms": 118},
        gold_tool_sequence=["search_database", "verify_fact"],
        tags=["research", "evidence", "fact_check"],
    ),
    "policy_compliance": DomainTemplate(
        domain="policy_compliance",
        instruction="Check the refund policy and determine whether a 700 dollar refund requires manager approval.",
        available_tools=["lookup_policy", "verify_fact"],
        success_criteria=["States whether approval is required.", "Cites the threshold."],
        required_information=["refund threshold", "refund amount"],
        forbidden_assumptions=["Do not use stale memory without checking current policy."],
        expected_final_answer="Yes. A 700 dollar refund requires manager approval because the threshold is 500 dollars.",
        hidden_ground_truth={"approval_required": True, "threshold": 500},
        gold_tool_sequence=["lookup_policy", "verify_fact"],
        tags=["policy", "compliance", "refunds"],
    ),
    "coding_debugging": DomainTemplate(
        domain="coding_debugging",
        instruction="Read the retry helper and issue note, then identify the bug.",
        available_tools=["read_file", "search_database"],
        success_criteria=["Identifies the off-by-one retry bug.", "References max_retries + 1."],
        required_information=["retry helper code", "issue note"],
        forbidden_assumptions=["Do not propose a fix without reading the helper."],
        expected_final_answer="The bug is an off-by-one retry loop using max_retries + 1.",
        hidden_ground_truth={"bug_type": "off_by_one", "bad_expression": "max_retries + 1"},
        gold_tool_sequence=["read_file", "search_database"],
        tags=["coding", "debugging", "off_by_one"],
    ),
    "multi_hop_operations": DomainTemplate(
        domain="multi_hop_operations",
        instruction="Plan a compliant vendor follow-up: check availability, policy constraints, choose the best vendor, and draft the email.",
        available_tools=["check_calendar", "lookup_policy", "query_spreadsheet", "compare_options", "send_email_draft"],
        success_criteria=[
            "Uses availability information.",
            "Applies vendor policy constraints.",
            "Chooses the best vendor.",
            "Drafts the follow-up email.",
        ],
        required_information=["availability", "vendor policy", "vendor score", "email recipient"],
        forbidden_assumptions=["Do not send the email.", "Do not ignore security addendum requirements."],
        expected_final_answer={"vendor": "vendor_beta", "time": "11:00", "must_mention": "security addendum"},
        hidden_ground_truth={"vendor": "vendor_beta", "time": "11:00", "policy": "security addendum"},
        gold_tool_sequence=["check_calendar", "lookup_policy", "query_spreadsheet", "compare_options", "send_email_draft"],
        tags=["operations", "multi_hop", "vendor"],
    ),
    "customer_support_workflow": DomainTemplate(
        domain="customer_support_workflow",
        instruction="Prepare a support response for a synthetic refund escalation by checking policy, verifying the case facts, and drafting a reply.",
        available_tools=["lookup_policy", "search_database", "verify_fact", "send_email_draft"],
        success_criteria=[
            "Applies the correct refund rule.",
            "Verifies the synthetic case facts before drafting.",
            "Creates only a draft response.",
        ],
        required_information=["refund policy", "case facts", "draft recipient"],
        forbidden_assumptions=["Do not send the email.", "Do not use any real customer data."],
        expected_final_answer={"case_id": "case_synth_104", "status": "draft_created", "refund_allowed": True},
        hidden_ground_truth={"case_id": "case_synth_104", "refund_allowed": True, "recipient": "support-lead@example.com"},
        gold_tool_sequence=["lookup_policy", "search_database", "verify_fact", "send_email_draft"],
        tags=["customer_support", "refund", "draft"],
    ),
    "finance_admin_workflow": DomainTemplate(
        domain="finance_admin_workflow",
        instruction="Using only synthetic finance records, check whether the admin reimbursement batch exceeds the approval threshold and draft a reviewer note.",
        available_tools=["query_spreadsheet", "lookup_policy", "calculate_price", "send_email_draft"],
        success_criteria=[
            "Computes the synthetic batch total.",
            "Applies the approval threshold.",
            "Creates only a draft reviewer note.",
        ],
        required_information=["batch line items", "approval threshold", "reviewer recipient"],
        forbidden_assumptions=["Do not send the email.", "Do not use real financial or personal data."],
        expected_final_answer={"batch_id": "batch_synth_admin_07", "total": 1280.0, "approval_required": True},
        hidden_ground_truth={"batch_id": "batch_synth_admin_07", "total": 1280.0, "threshold": 1000.0},
        gold_tool_sequence=["query_spreadsheet", "calculate_price", "lookup_policy", "send_email_draft"],
        tags=["finance_admin", "synthetic", "approval"],
    ),
    "data_cleaning_workflow": DomainTemplate(
        domain="data_cleaning_workflow",
        instruction="Inspect the synthetic import note and sheet summary, then identify the cleaning rule needed before analysis.",
        available_tools=["read_file", "query_spreadsheet", "verify_fact", "compare_options"],
        success_criteria=[
            "Identifies the required cleaning rule.",
            "Cites evidence from the note or sheet summary.",
        ],
        required_information=["import note", "sheet anomaly summary", "cleaning rule"],
        forbidden_assumptions=["Do not assume missing values are zeros."],
        expected_final_answer={"cleaning_rule": "standardize_blank_status_to_unknown", "affected_column": "status"},
        hidden_ground_truth={"cleaning_rule": "standardize_blank_status_to_unknown", "affected_column": "status"},
        gold_tool_sequence=["read_file", "query_spreadsheet", "verify_fact"],
        tags=["data_cleaning", "synthetic", "qa"],
    ),
}


def difficulty_sequence(base_sequence: list[str], difficulty: str) -> list[str]:
    target = DIFFICULTY_STEPS.get(difficulty, 3)
    sequence = list(base_sequence)
    extension = ["verify_fact", "search_database", "read_file", "query_spreadsheet", "lookup_policy", "compare_options"]
    for tool in extension:
        if len(sequence) >= target:
            break
        if tool not in sequence:
            sequence.append(tool)
    return sequence[:target]


def normalize_domain(domain: str) -> str:
    return PILOT_DOMAIN_ALIASES.get(domain, domain)
