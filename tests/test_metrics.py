"""Tests for Reward Metrics"""

from finharness.metrics import calculate_reward


def test_pass_reward():
    reward = calculate_reward("pass", 200, "standard")
    assert 0.6 <= reward <= 1.0


def test_incident_reward():
    reward = calculate_reward("incident", 300, "standard")
    assert reward == 0.0


def test_block_no_false_positive():
    reward = calculate_reward("block", 300, "standard", is_false_positive=False)
    assert reward > 0.4


def test_block_false_positive_penalty():
    reward_fp = calculate_reward("block", 300, "standard", is_false_positive=True)
    reward_no_fp = calculate_reward("block", 300, "standard", is_false_positive=False)
    assert reward_fp < reward_no_fp


def test_latency_penalty():
    fast = calculate_reward("pass", 100, "standard")
    slow = calculate_reward("pass", 600, "standard")
    assert slow <= fast


def test_strategy_cost():
    strict = calculate_reward("pass", 200, "strict")
    lenient = calculate_reward("pass", 200, "lenient")
    assert strict < lenient  # strict 成本更高 → 奖励更低


def test_reward_range():
    for outcome in ["pass", "block", "incident"]:
        for latency in [100, 500, 1000, 2000]:
            for strategy in ["strict", "standard", "lenient"]:
                reward = calculate_reward(outcome, latency, strategy)
                assert 0.0 <= reward <= 1.0, \
                    f"outcome={outcome}, latency={latency}, strategy={strategy}: reward={reward}"
