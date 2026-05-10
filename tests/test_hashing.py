from causal_agent_bench.hashing import config_hash, stable_hash


def test_stable_hash_ignores_key_order():
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_config_hash_from_mapping():
    assert config_hash({"seed": 7, "name": "smoke"}) == config_hash({"name": "smoke", "seed": 7})
