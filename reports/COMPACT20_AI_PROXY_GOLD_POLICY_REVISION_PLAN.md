# Compact-20 AI Proxy Gold-Policy Revision Plan

Status: `ai_proxy_test_only`

This plan is synthetic/proxy guidance for testing downstream review handling. It is not a human decision log and must not be used to patch frozen data.

## Proxy Family Assessment

| family | proxy assessment | required real action before paper use |
|---|---|---|
| `memory_corruption` | Expected answer marked unchanged in the manifest; `5` rows are proxy-clean for pipeline testing only. | Human reviewer must confirm goal preservation, evidence path, and answer policy. |
| `tool_removal` | Answer-changing behavioral override; `5` rows require policy verification. | Human reviewer must decide whether answer change, abstention, or exclusion is appropriate. |
| `tool_failure` | Current policy is unclear between unchanged and behavioral override; `5` rows require review. | Human reviewer must verify whether a recovery path exists and whether abstention/cannot-determine is acceptable. |
| `observation_conflict` | High-risk conflict policy; `5` rows require review. | Human reviewer must resolve conflict rules or exclude rows with multiple plausible answers. |

## Proxy Issues Requiring Manual Review

| family | rows needing real review |
|---|---:|
| `observation_conflict` | `5` |
| `tool_failure` | `5` |
| `tool_removal` | `5` |

## Hard Limits

- No auto-fix is authorized.
- No frozen data may be edited from this proxy review.
- No C10, C1-C8, model-performance, or paper-asset claim is promoted.
