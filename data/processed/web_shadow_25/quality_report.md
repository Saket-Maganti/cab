# Generation Quality Report

Passed: `False`

## Counts

- Base tasks: 50
- Interventions: 250
- Instances: 300

## Distributions

### Domains

- `web_shadow_docs`: 6
- `web_shadow_legal`: 4
- `web_shadow_navigation`: 14
- `web_shadow_pricing`: 4
- `web_shadow_product`: 8
- `web_shadow_search`: 12
- `web_shadow_support`: 2

### Difficulties

- `easy`: 10
- `hard`: 12
- `medium`: 20
- `stress`: 8

### Intervention Families

- `distractor_evidence`: 25
- `long_horizon_dependency`: 25
- `observation_conflict`: 25
- `tool_corruption`: 25
- `tool_failure`: 25
- `web_broken_link`: 25
- `web_conflicting_page`: 25
- `web_hidden_evidence`: 25
- `web_irrelevant_search_result`: 25
- `web_stale_page`: 25

## Statistics

- Average max steps: 5
- Average required tools: 2.24
- Duplicate task IDs: 0
- Duplicate instance IDs: 0

## Intervention Validity Scores

- `fail`: 174
- `pass`: 90
- `warning`: 36

| Instance | Score | Family | Notes |
|---|---:|---|---|
| `webshadow_api_api_rate_limit_hard.clean` | `pass` | `clean` | None. |
| `webshadow_api_api_rate_limit_hard.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `webshadow_api_api_rate_limit_hard.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `webshadow_api_api_rate_limit_hard.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `webshadow_api_api_rate_limit_hard.tool_corruption` | `pass` | `tool_corruption` | None. |
| `webshadow_api_api_rate_limit_hard.tool_failure` | `warning` | `tool_failure` | final-answer scoring requires explicit audit attention |
| `webshadow_api_docs_hub_medium.clean` | `pass` | `clean` | None. |
| `webshadow_api_docs_hub_medium.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `webshadow_api_docs_hub_medium.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `webshadow_api_docs_hub_medium.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `webshadow_api_docs_hub_medium.tool_corruption` | `pass` | `tool_corruption` | None. |
| `webshadow_api_docs_hub_medium.tool_failure` | `warning` | `tool_failure` | final-answer scoring requires explicit audit attention |
| `webshadow_api_enterprise_features_stress.clean` | `fail` | `clean` | base task issue: success criteria are not machine-checkable enough for deterministic scoring |
| `webshadow_api_enterprise_features_stress.distractor_evidence` | `fail` | `distractor_evidence` | base task issue: success criteria are not machine-checkable enough for deterministic scoring |
| `webshadow_api_enterprise_features_stress.long_horizon_dependency` | `fail` | `long_horizon_dependency` | base task issue: success criteria are not machine-checkable enough for deterministic scoring |
| `webshadow_api_enterprise_features_stress.observation_conflict` | `fail` | `observation_conflict` | base task issue: success criteria are not machine-checkable enough for deterministic scoring |
| `webshadow_api_enterprise_features_stress.tool_corruption` | `fail` | `tool_corruption` | base task issue: success criteria are not machine-checkable enough for deterministic scoring |
| `webshadow_api_enterprise_features_stress.tool_failure` | `fail` | `tool_failure` | base task issue: success criteria are not machine-checkable enough for deterministic scoring |
| `webshadow_api_enterprise_price_medium.clean` | `pass` | `clean` | None. |
| `webshadow_api_enterprise_price_medium.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| ... | ... | ... | 280 additional instances omitted. |

### Tool Patterns

- `lookup_policy`: 1
- `lookup_policy -> read_file -> verify_fact`: 1
- `lookup_policy -> verify_fact`: 2
- `read_file`: 2
- `read_file -> search_database`: 1
- `read_file -> verify_fact`: 5
- `search_database`: 1
- `search_database -> lookup_policy`: 1
- `search_database -> read_file`: 4
- `search_database -> verify_fact`: 7
- `web_open_page -> web_extract_section`: 6
- `web_open_page -> web_follow_link`: 4

## Issues

### base_task_issues
- `webshadow_web_snapshot_widget_pro_weight_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_widget_pro_weight_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_web_snapshot_widget_power_draw_easy`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_widget_power_draw_easy`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_web_snapshot_enterprise_features_stress`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_enterprise_features_stress`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_web_snapshot_widget_ports_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_widget_ports_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_web_snapshot_open_support_home_hard`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_open_support_home_hard`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_web_snapshot_legal_index_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_legal_index_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_web_snapshot_product_to_specs_medium`: success criteria are not machine-checkable enough for deterministic scoring
- `webshadow_api_product_to_specs_medium`: success criteria are not machine-checkable enough for deterministic scoring

### intervention_issues
- `webshadow_web_snapshot_widget_pro_sku_hard.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_widget_pro_sku_hard.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_widget_pro_sku_hard.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_widget_pro_sku_hard.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_widget_pro_sku_hard.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_widget_pro_weight_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_widget_pro_weight_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_widget_pro_weight_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_widget_pro_weight_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_widget_pro_weight_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_enterprise_price_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_enterprise_price_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_enterprise_price_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_enterprise_price_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_enterprise_price_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_api_rate_limit_hard.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_api_rate_limit_hard.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_api_rate_limit_hard.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_api_rate_limit_hard.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_api_rate_limit_hard.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_widget_power_draw_easy.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_widget_power_draw_easy.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_widget_power_draw_easy.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_widget_power_draw_easy.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_widget_power_draw_easy.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_error_e42_fix_hard.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_error_e42_fix_hard.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_error_e42_fix_hard.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_error_e42_fix_hard.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_error_e42_fix_hard.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_telemetry_retention_stress.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_telemetry_retention_stress.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_telemetry_retention_stress.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_telemetry_retention_stress.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_telemetry_retention_stress.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_hardware_warranty_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_hardware_warranty_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_hardware_warranty_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_hardware_warranty_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_hardware_warranty_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_search_widget_pro_hard.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_search_widget_pro_hard.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_search_widget_pro_hard.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_search_widget_pro_hard.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_search_widget_pro_hard.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_search_enterprise_pricing_easy.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_search_enterprise_pricing_easy.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_search_enterprise_pricing_easy.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_search_enterprise_pricing_easy.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_search_enterprise_pricing_easy.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_lite_sku_easy.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_lite_sku_easy.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_lite_sku_easy.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_lite_sku_easy.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_lite_sku_easy.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_lite_tier_price_hard.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_lite_tier_price_hard.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_lite_tier_price_hard.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_lite_tier_price_hard.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_lite_tier_price_hard.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_enterprise_features_stress.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_enterprise_features_stress.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_enterprise_features_stress.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_enterprise_features_stress.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_enterprise_features_stress.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_widget_ports_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_widget_ports_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_widget_ports_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_widget_ports_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_widget_ports_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_home_to_products_easy.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_home_to_products_easy.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_home_to_products_easy.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_home_to_products_easy.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_home_to_products_easy.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_docs_hub_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_docs_hub_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_docs_hub_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_docs_hub_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_docs_hub_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_pricing_from_suite_stress.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_pricing_from_suite_stress.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_pricing_from_suite_stress.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_pricing_from_suite_stress.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_pricing_from_suite_stress.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_runbook_to_e42_easy.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_runbook_to_e42_easy.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_runbook_to_e42_easy.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_runbook_to_e42_easy.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_runbook_to_e42_easy.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_search_rate_limit_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_search_rate_limit_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_search_rate_limit_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_search_rate_limit_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_search_rate_limit_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_search_retention_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_search_retention_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_search_retention_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_search_retention_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_search_retention_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_search_error_e42_stress.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_search_error_e42_stress.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_search_error_e42_stress.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_search_error_e42_stress.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_search_error_e42_stress.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_open_support_home_hard.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_open_support_home_hard.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_open_support_home_hard.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_open_support_home_hard.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_open_support_home_hard.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_legal_index_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_legal_index_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_legal_index_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_legal_index_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_legal_index_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_product_to_specs_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_product_to_specs_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_product_to_specs_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_product_to_specs_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_product_to_specs_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'
- `webshadow_web_snapshot_search_warranty_medium.web_broken_link`: changed_factor does not match family target factor: expected 'hyperlink reliability in static snapshot navigation', got 'hyperlink reliability'
- `webshadow_web_snapshot_search_warranty_medium.web_stale_page`: changed_factor does not match family target factor: expected 'page freshness in frozen HTML snapshot', got 'page freshness'
- `webshadow_web_snapshot_search_warranty_medium.web_conflicting_page`: changed_factor does not match family target factor: expected 'cross-page factual consistency', got 'page-level factual consistency'; intervention patch changes too many fields for web_conflicting_page: 3 > 2; scoring notes do not describe the expected changed-answer behavior
- `webshadow_web_snapshot_search_warranty_medium.web_irrelevant_search_result`: changed_factor does not match family target factor: expected 'search ranking relevance in static index', got 'search ranking relevance'
- `webshadow_web_snapshot_search_warranty_medium.web_hidden_evidence`: changed_factor does not match family target factor: expected 'visibility of required on-page evidence', got 'evidence visibility'

### instance_issues

None.

### duplicate_instances

None.

### duplicate_tasks

None.

## Warnings

- domain imbalance: distribution is uneven: {'web_shadow_docs': 6, 'web_shadow_legal': 4, 'web_shadow_navigation': 14, 'web_shadow_pricing': 4, 'web_shadow_product': 8, 'web_shadow_search': 12, 'web_shadow_support': 2}
- difficulty imbalance: distribution is uneven: {'easy': 10, 'hard': 12, 'medium': 20, 'stress': 8}
- intervention validity risk high for webshadow_web_snapshot_widget_pro_sku_hard.web_conflicting_page: web_conflicting_page

## Warning Examples

### high_validity_risk_interventions
- `webshadow_web_snapshot_widget_pro_sku_hard.web_conflicting_page`
- `webshadow_api_widget_pro_sku_hard.observation_conflict`
- `webshadow_web_snapshot_widget_pro_weight_medium.web_conflicting_page`
- `webshadow_api_widget_pro_weight_medium.observation_conflict`
- `webshadow_web_snapshot_enterprise_price_medium.web_conflicting_page`
### expected_answer_change_interventions
- `webshadow_web_snapshot_widget_pro_sku_hard.web_broken_link`
- `webshadow_web_snapshot_widget_pro_sku_hard.web_conflicting_page`
- `webshadow_api_widget_pro_sku_hard.tool_failure`
- `webshadow_api_widget_pro_sku_hard.observation_conflict`
- `webshadow_web_snapshot_widget_pro_weight_medium.web_broken_link`
### long_tool_sequences
None.
### intervention_instances
- `webshadow_web_snapshot_widget_pro_sku_hard.web_broken_link`
- `webshadow_web_snapshot_widget_pro_sku_hard.web_stale_page`
- `webshadow_web_snapshot_widget_pro_sku_hard.web_conflicting_page`
- `webshadow_web_snapshot_widget_pro_sku_hard.web_irrelevant_search_result`
- `webshadow_web_snapshot_widget_pro_sku_hard.web_hidden_evidence`
