"""
MAB Engine — Thompson Sampling 自适应决策引擎

核心逻辑:
  - 每个策略维护一个 Beta(alpha, beta) 分布
  - 每次决策从各策略分布采样, 选最大值
  - 根据实际治理结果更新分布参数
"""

import numpy as np
from typing import Dict, List, Tuple


class AdaptiveMABEngine:
    """基于 Thompson Sampling 的多臂老虎机自适应引擎"""

    def __init__(self, strategies: Tuple[str, ...] = ("strict", "standard", "lenient")):
        self.strategies = list(strategies)
        self.alpha = {s: 1.0 for s in strategies}
        self.beta = {s: 1.0 for s in strategies}
        self.history: List[dict] = []
        self.total_trials = 0

    def assign(self) -> Tuple[str, Dict[str, float]]:
        """
        基于 Thompson Sampling 采样选择当前最优策略

        Returns:
            (策略名, {策略名: 采样值})
        """
        samples = {}
        for s in self.strategies:
            samples[s] = float(np.random.beta(self.alpha[s], self.beta[s]))

        best = max(samples, key=samples.get)
        self.total_trials += 1
        return best, samples

    def update(self, strategy: str, reward: float):
        """
        根据实际治理结果更新分布参数

        reward >= 0.7: 增加 alpha (成功次数)
        reward < 0.7:  增加 beta (失败次数)
        """
        if reward >= 0.7:
            self.alpha[strategy] += 1
        else:
            self.beta[strategy] += 1

        self.history.append({
            "trial": self.total_trials,
            "strategy": strategy,
            "reward": reward,
            "alpha": dict(self.alpha),
            "beta": dict(self.beta),
        })

    def get_expected_values(self) -> Dict[str, float]:
        """获取各策略的期望值 (用于可视化)"""
        return {
            s: self.alpha[s] / (self.alpha[s] + self.beta[s])
            for s in self.strategies
        }

    def get_history_for_plot(self) -> dict:
        """获取历史数据用于 Plotly 画收敛曲线"""
        if not self.history:
            return {"trials": [], "strict": [], "standard": [], "lenient": []}

        data = {"trials": [], "strict": [], "standard": [], "lenient": []}
        for h in self.history:
            data["trials"].append(h["trial"])
            for s in self.strategies:
                a = h["alpha"][s]
                b = h["beta"][s]
                data[s].append(a / (a + b))
        return data
