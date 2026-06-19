"""
FinAgent MAB Engine — Thompson Sampling 自适应决策

参考: Qwen Agent Tool 模式 + CrewAI 独立工具设计
每个工具独立注册、自描述、可被 Agent 自动发现和调用。
"""

import numpy as np
from typing import Dict, List, Tuple


class ThompsonBandit:
    """基于 Thompson Sampling 的多臂老虎机自适应引擎"""

    def __init__(self, arms: Tuple[str, ...] = ("strict", "standard", "lenient")):
        self.arms = list(arms)
        self.alpha = {a: 1.0 for a in arms}
        self.beta = {a: 1.0 for a in arms}
        self.history: List[dict] = []
        self.total_trials = 0

    def pull(self) -> Tuple[str, Dict[str, float]]:
        """
        从每个臂的 Beta 分布采样，选择期望奖励最高的策略。

        Returns:
            (策略名, {策略名: 采样值})
        """
        samples = {}
        for arm in self.arms:
            samples[arm] = float(np.random.beta(self.alpha[arm], self.beta[arm]))

        best = max(samples, key=samples.get)
        self.total_trials += 1
        return best, samples

    def update(self, arm: str, reward: float):
        """
        根据实际治理结果更新 Beta 分布参数。

        reward >= 0.7 → 增加 alpha (成功)
        reward < 0.7  → 增加 beta  (失败)
        """
        if reward >= 0.7:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1

        self.history.append({
            "trial": self.total_trials,
            "arm": arm,
            "reward": reward,
            "alpha": dict(self.alpha),
            "beta": dict(self.beta),
        })

    def expected_values(self) -> Dict[str, float]:
        """各策略期望成功率"""
        return {
            a: self.alpha[a] / (self.alpha[a] + self.beta[a])
            for a in self.arms
        }

    def convergence_data(self) -> dict:
        """历史收敛曲线数据（用于 Plotly 渲染）"""
        if not self.history:
            return {"trials": [], "strict": [], "standard": [], "lenient": []}

        data = {"trials": [], "strict": [], "standard": [], "lenient": []}
        for h in self.history:
            data["trials"].append(h["trial"])
            for a in self.arms:
                aa = h["alpha"][a]
                bb = h["beta"][a]
                data[a].append(aa / (aa + bb))
        return data


def compute_reward(
    outcome: str,
    latency_ms: int = 300,
    strategy: str = "standard",
    is_false_positive: bool = False,
) -> float:
    """
    复合奖励函数 — 平衡安全性与可用性。

    设计原则:
      - pass 基础分最高，误放行则归零
      - block 给中等分(拦截潜在风险)，误杀扣分
      - incident 严重扣分(事故已发生)
      - 延迟和成本作为微调因子
    """
    STRATEGY_COST = {"strict": 3.0, "standard": 1.5, "lenient": 1.0}

    # 基础结果分
    if outcome == "pass":
        base = 1.0
    elif outcome == "block":
        base = 0.7 if not is_false_positive else 0.3
    elif outcome == "incident":
        base = 0.0
    else:
        base = 0.5

    # 延迟惩罚
    if latency_ms > 1000:
        latency_penalty = 0.2
    elif latency_ms > 500:
        latency_penalty = 0.1
    else:
        latency_penalty = 0.0

    # 成本因子
    cost_factor = 1.0 / STRATEGY_COST.get(strategy, 1.5)

    reward = base * cost_factor - latency_penalty
    return max(0.0, min(1.0, reward))
