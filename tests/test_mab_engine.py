"""Tests for MAB Engine — Thompson Sampling"""

import pytest
from finharness.mab_engine import AdaptiveMABEngine


@pytest.fixture
def mab():
    return AdaptiveMABEngine()


def test_initial_state(mab):
    assert len(mab.strategies) == 3
    for s in mab.strategies:
        assert mab.alpha[s] == 1.0
        assert mab.beta[s] == 1.0
    assert mab.total_trials == 0


def test_assign_returns_valid_strategy(mab):
    chosen, samples = mab.assign()
    assert chosen in mab.strategies
    assert set(samples.keys()) == set(mab.strategies)
    assert all(0.0 <= v <= 1.0 for v in samples.values())


def test_update_alpha_on_success(mab):
    mab.assign()
    old_alpha = mab.alpha["strict"]
    mab.update("strict", 0.9)  # >= 0.7 → alpha +1
    assert mab.alpha["strict"] == old_alpha + 1


def test_update_beta_on_failure(mab):
    mab.assign()
    old_beta = mab.beta["strict"]
    mab.update("strict", 0.3)  # < 0.7 → beta +1
    assert mab.beta["strict"] == old_beta + 1


def test_trial_counter(mab):
    for i in range(5):
        mab.assign()
    assert mab.total_trials == 5


def test_expected_values_range(mab):
    # 跑几轮后检查期望值范围
    for _ in range(10):
        chosen, _ = mab.assign()
        mab.update(chosen, 0.9)

    ev = mab.get_expected_values()
    for s in mab.strategies:
        assert 0.0 <= ev[s] <= 1.0


def test_convergence():
    """验证 Thompson Sampling 收敛：高奖励策略最终期望最高"""
    import random
    random.seed(42)

    mab = AdaptiveMABEngine()
    true_rates = {"strict": 0.8, "standard": 0.5, "lenient": 0.3}

    for _ in range(100):
        chosen, _ = mab.assign()
        success = random.random() < true_rates[chosen]
        mab.update(chosen, 0.9 if success else 0.3)

    ev = mab.get_expected_values()
    # strict 期望值应最高
    assert ev["strict"] > ev["lenient"]
    assert ev["strict"] > ev["standard"]


def test_history_tracking(mab):
    mab.assign()
    mab.update("strict", 0.9)
    assert len(mab.history) == 1
    assert mab.history[0]["strategy"] == "strict"
    assert mab.history[0]["reward"] == 0.9


def test_plot_data_empty(mab):
    data = mab.get_history_for_plot()
    assert data["trials"] == []
    assert data["strict"] == []
