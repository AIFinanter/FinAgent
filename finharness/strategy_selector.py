"""
Wisdom Layer — 可解释策略选择器 (Qwen Agent 版本)

DIKW 层级: Wisdom (风险评估 + MAB → 治理策略)

基于 Qwen Agent LLM 抽象层，强制输出机械可解释性归因
"""

import json
from typing import Dict

from qwen_agent.llm import get_chat_model

from config import config
from models import RiskAssessment, StrategyDecision, StrategyLevel
from finharness.mab_engine import AdaptiveMABEngine


class ExplainableStrategySelector:
    """
    二级 LLM: 强制可解释性的治理策略决策

    核心要求:
    1. 输出推荐策略
    2. 机械归因 (为什么选这个策略)
    3. 干预点定位 (DIKW 哪一层)
    """

    def __init__(self, mab_engine: AdaptiveMABEngine = None):
        self.llm = get_chat_model(config.llm.to_qwen_llm_cfg())
        self.mab = mab_engine or AdaptiveMABEngine(config.mab.strategies)

    def select_with_mechanism(
        self,
        risk: RiskAssessment,
        mab_suggestion: str,
        mab_samples: Dict[str, float],
    ) -> StrategyDecision:
        """选择最优策略并输出机械可解释性归因"""

        prompt = f"""你是金融AI治理策略优化专家。基于以下信息选择最优治理策略。

风险评估: 分数={risk.risk_score:.2f}, 类型={risk.risk_type.value}, 置信度={risk.confidence:.2f}
行为模型预警: {risk.behavior_anomaly:.2f}
知识库证据: {risk.rag_evidence[:2] if risk.rag_evidence else '无'}
MAB推荐: {mab_suggestion} (采样值: {json.dumps(mab_samples)})

策略池:
- strict: 全部二次审核+实时拦截, 延迟1200ms, 成本3x
- standard: 高风险审核+日常自动, 延迟400ms, 成本1.5x
- lenient: 抽样检查+仅拦截明确违规, 延迟100ms, 成本1x

输出 JSON (严格格式):
{{
  "recommended_strategy": "strict|standard|lenient",
  "mab_confidence": <0.0-1.0>,
  "causal_attribution": "解释为什么MAB数据和风险评估共同指向该策略",
  "intervention_layer": "Data|Information|Knowledge|Wisdom",
  "block_triggers": [string],
  "auto_approve_threshold": <0.0-1.0>,
  "rollback_condition": string,
  "next_evaluation_hours": int
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = list(self.llm.chat(messages))[-1]
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        result = json.loads(content)

        return StrategyDecision(
            recommended=StrategyLevel(result.get("recommended_strategy", "standard")),
            block_triggers=result.get("block_triggers", []),
            auto_approve_threshold=result.get("auto_approve_threshold", 0.3),
            rollback_condition=result.get("rollback_condition", ""),
            mab_confidence=result.get("mab_confidence", 0.5),
            causal_attribution=result.get("causal_attribution", ""),
            intervention_layer=result.get("intervention_layer", "Knowledge"),
            next_evaluation_hours=result.get("next_evaluation_hours", 24),
        )
