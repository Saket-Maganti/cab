from __future__ import annotations

from causal_agent_bench.analysis.iclr_preexecution import (
    clustered_bootstrap_shard,
    cost_efficiency_frontier,
    merge_clustered_bootstrap_shards,
    missingness_diagnostics,
    mixed_effects_binary_contract,
    naturalistic_predictive_validity,
    opportunity_denominator_check,
    paired_equivalence_test,
    raac_clean_tradeoff,
)


def test_paired_equivalence_blocks_empty_and_handles_degenerate_signal() -> None:
    blocked = paired_equivalence_test([], [], equivalence_margin=0.05)
    assert blocked["state"] == "blocked_insufficient_pairs"
    exact = paired_equivalence_test(
        [1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0],
        equivalence_margin=0.05,
    )
    assert exact["equivalent"] is True
    assert exact["state"] == "degenerate_exact_difference"


def test_missingness_and_opportunity_denominators_fail_closed() -> None:
    rows = [
        {"agent": "a", "condition": "clean", "score": 1.0},
        {"agent": "a", "condition": "intervention", "score": None},
    ]
    missing = missingness_diagnostics(rows, required_fields=["score"])
    assert missing["field_missing_counts"]["score"] == 1
    assert missing["complete_case_count"] == 1
    opportunities = opportunity_denominator_check(
        [
            {"can_recover": True, "recovered": True},
            {"can_recover": False, "recovered": True},
        ],
        opportunity_field="can_recover",
        outcome_field="recovered",
    )
    assert opportunities["state"] == "invalid"
    assert opportunities["rate"] == 1.0


def test_naturalistic_predictive_validity_blocks_small_panel() -> None:
    report = naturalistic_predictive_validity([])
    assert report["state"] == "blocked_insufficient_complete_rows"
    assert report["scientific_evidence"] is False


def test_naturalistic_predictive_validity_is_deterministic() -> None:
    rows = []
    for index in range(12):
        value = index / 11
        rows.append(
            {
                "model_family": f"family-{index % 3}",
                "naturalistic_success": value,
                "clean_success": value,
                "acrs": 0.2 + value * 0.7,
                "clean_conditioned_robustness": 0.1 + value * 0.8,
                "recovery_score": 0.3 + value * 0.6,
                "abstention_score": 0.4 + value * 0.5,
                "worst_family_robustness": 0.05 + value * 0.9,
            }
        )
    first = naturalistic_predictive_validity(rows, n_boot=100, seed=7)
    second = naturalistic_predictive_validity(rows, n_boot=100, seed=7)
    assert first == second
    assert first["state"] == "ok"
    assert first["correlations"]["acrs"]["pearson"] > 0.99


def test_mixed_effects_contract_requires_clusters_and_variation() -> None:
    blocked = mixed_effects_binary_contract(
        [{"base_task_id": "one", "success": 1, "policy": "x"}],
        outcome_field="success",
        fixed_effects=["policy"],
    )
    assert blocked["state"] == "blocked"
    assert "insufficient_clusters" in blocked["blockers"]


def test_raac_tradeoff_and_efficiency_frontier() -> None:
    rows = [
        {
            "policy": "STANDARD_TOOL_USE",
            "clean_success": 0.9,
            "robust_success": 0.5,
            "extra_calls": 0,
            "wall_clock_seconds": 1,
        },
        {
            "policy": "RAAC_LIGHT",
            "clean_success": 0.9,
            "robust_success": 0.7,
            "extra_calls": 1,
            "wall_clock_seconds": 2,
        },
    ]
    tradeoff = raac_clean_tradeoff(rows)
    assert tradeoff["state"] == "ok"
    light = next(row for row in tradeoff["comparisons"] if row["policy"] == "RAAC_LIGHT")
    assert light["robust_success_delta_vs_baseline"] == 0.2
    frontier = cost_efficiency_frontier(
        [
            {"policy": "a", "mean_cost": 1.0, "robust_success": 0.5},
            {"policy": "b", "mean_cost": 2.0, "robust_success": 0.4},
            {"policy": "c", "mean_cost": 2.0, "robust_success": 0.8},
        ]
    )
    assert [row["name"] for row in frontier["frontier"]] == ["a", "c"]
    assert frontier["dominated"] == ["b"]


def test_bootstrap_shards_resume_merge_and_reject_duplicates() -> None:
    pairs = [
        {
            "base_task_id": f"task-{index}",
            "clean_success": 1,
            "intervention_success": index % 2,
        }
        for index in range(8)
    ]
    first = clustered_bootstrap_shard(
        pairs,
        seed=11,
        replicate_start=0,
        replicate_stop=50,
    )
    second = clustered_bootstrap_shard(
        pairs,
        seed=11,
        replicate_start=50,
        replicate_stop=100,
    )
    merged = merge_clustered_bootstrap_shards(
        [second, first],
        expected_replicates=100,
    )
    assert merged["state"] == "ok"
    assert merged["observed_replicates"] == 100
    repeated = clustered_bootstrap_shard(
        pairs,
        seed=11,
        replicate_start=0,
        replicate_stop=50,
    )
    assert repeated == first
    duplicate = merge_clustered_bootstrap_shards(
        [first, repeated, second],
        expected_replicates=100,
    )
    assert duplicate["state"] == "invalid"
    assert "duplicate_replicates" in duplicate["issues"]
