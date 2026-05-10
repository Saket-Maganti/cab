from causal_agent_bench.io import create_run_dir, read_jsonl, set_deterministic_seed, write_jsonl


def test_jsonl_helpers_round_trip_dicts(tmp_path):
    path = tmp_path / "rows.jsonl"
    rows = [{"id": "a", "value": 1}, {"id": "b", "value": 2}]
    write_jsonl(path, rows)
    assert read_jsonl(path) == rows


def test_create_run_dir_and_seed(tmp_path):
    set_deterministic_seed(7)
    run_dir = create_run_dir(tmp_path, "smoke run")
    assert run_dir.exists()
    assert run_dir.name == "smoke_run"
