"""
复合奖励函数 — 平衡安全性与可用性

设计原则:
  - pass 基础分最高, 但如果是误放行则归零
  - block 给中等分(拦截了潜在风险), 但误杀扣分
  - incident 严重扣分(事故发生了)
  - 延迟和成本作为微调因子
"""


def calculate_reward(
    outcome: str,          # "pass" | "block" | "incident"
    latency_ms: int,
    strategy: str,
    is_false_positive: bool = False,
) -> float:
    """计算复合治理奖励"""

    # 策略成本乘数
    STRATEGY_COST = {"strict": 3.0, "standard": 1.5, "lenient": 1.0}

    # 1. 基础结果分 (0.0 ~ 1.0)
    if outcome == "pass":
        base = 1.0
    elif outcome == "block":
        base = 0.7 if not is_false_positive else 0.3  # 有效拦截 vs 误杀
    elif outcome == "incident":
        base = 0.0
    else:
        base = 0.5

    # 2. 性能惩罚 (0.0 ~ -0.2)
    if latency_ms > 1000:
        latency_penalty = 0.2
    elif latency_ms > 500:
        latency_penalty = 0.1
    else:
        latency_penalty = 0.0

    # 3. 成本因子 (成本越高, reward 越低)
    cost_factor = 1.0 / STRATEGY_COST[strategy]

    # 4. 复合奖励
    reward = base * cost_factor - latency_penalty
    return max(0.0, min(1.0, reward))
