"""
FinGuard DIKW 治理流水线编排器

DIKW 数智流架构:
  Data → Information → Knowledge → Wisdom
  脱敏  → 行为预测    → LLM评分+RAG → 策略治理+MAB

底层框架: Qwen Agent (RAG/LLM)
"""

from typing import List, Optional

from config import config
from models import (
    FinDataInput,
    GovernanceReport,
    RiskAssessment,
    StrategyDecision,
)
from finguard.data_layer import DataSanitizer
from finguard.info_layer import BehavioralFoundationModel
from finguard.knowledge_layer import LLMRiskScorer
from knowledge_base.rag_engine import ComplianceRAG
from finharness.mab_engine import AdaptiveMABEngine
from finharness.strategy_selector import ExplainableStrategySelector
from finharness.metrics import calculate_reward


class FinGuardPipeline:
    """DIKW 治理流水线编排器"""

    def __init__(self):
        # D: 脱敏
        self.sanitizer = DataSanitizer()
        # I: 行为预测
        self.behavior_model = BehavioralFoundationModel()
        # MAB: 策略引擎
        self.mab = AdaptiveMABEngine(config.mab.strategies)
        # K: RAG + LLM 评分
        self.scorer = LLMRiskScorer()
        # W: 策略选择
        self.selector = ExplainableStrategySelector(self.mab)
        # RAG 延迟初始化 (需要 LLM)
        self._rag: Optional[ComplianceRAG] = None

    @property
    def rag(self) -> Optional[ComplianceRAG]:
        if self._rag is None:
            try:
                self._rag = ComplianceRAG(
                    regulations_file=config.rag.regulations_file,
                    llm=self.scorer.llm,
                    max_ref_token=config.rag.max_ref_token,
                    parser_page_size=config.rag.parser_page_size,
                    rag_keygen_strategy=config.rag.rag_keygen_strategy,
                    rag_searchers=config.rag.rag_searchers,
                )
            except Exception:
                self._rag = None
        return self._rag

    async def evaluate(self, input_data: FinDataInput) -> GovernanceReport:
        """
        完整的 DIKW 评估流水线

        D → I → K → W
        """
        # ── D: 脱敏 ──
        sanitized, compliance = self.sanitizer.sanitize(input_data.raw_text)

        # ── I: 行为预测 ──
        features = self.behavior_model.extract_features(input_data.metadata)
        anomaly = float(self.behavior_model.predict_anomaly(features))

        # ── K: RAG检索 + LLM评分 ──
        rag_evidence = []
        if self.rag:
            try:
                rag_evidence = self.rag.retrieve(sanitized)
            except Exception:
                pass

        risk = self.scorer.score(
            {"scenario": input_data.scenario, "sanitized_text": sanitized},
            rag_evidence,
            anomaly,
        )

        # ── MAB: 策略分配 ──
        strategy_name, mab_samples = self.mab.assign()

        # ── W: 可解释策略选择 ──
        decision = self.selector.select_with_mechanism(
            risk, strategy_name, mab_samples
        )

        # ── 生成报告 ──
        report = GovernanceReport(
            input_id=input_data.id,
            risk_assessment=risk,
            strategy=decision,
            actions_taken=self._generate_actions(decision),
            recommendations=self._generate_recommendations(risk, decision),
        )
        return report

    def feedback_loop(
        self,
        strategy: str,
        outcome: str,
        latency_ms: int = 300,
        is_false_positive: bool = False,
    ) -> float:
        """
        奖励反馈闭环: 更新 MAB 参数

        触发条件:
        - outcome = "incident": β + 1 → 下次降低该策略权重
        - outcome = "pass":    α + 1 → 增强该策略权重
        - outcome = "block":   视误杀情况调整
        """
        reward = calculate_reward(outcome, latency_ms, strategy, is_false_positive)
        self.mab.update(strategy, reward)
        return reward

    def _generate_actions(self, decision: StrategyDecision) -> List[str]:
        """根据决策生成具体执行动作"""
        actions = []
        strategy = decision.recommended.value

        if strategy == "strict":
            actions.append("🔴 启用全部二次审核流程")
            actions.append("🔴 设置实时拦截规则")
            actions.append("🔴 标记为高风险需人工复核")
        elif strategy == "standard":
            actions.append("🟡 启用高风险内容二次审核")
            actions.append("🟡 日常低风险内容自动放行")
            actions.append("🟡 记录日志用于定期审计")
        else:  # lenient
            actions.append("🟢 仅拦截明确违规内容")
            actions.append("🟢 抽样检查 (10% 比例)")
            actions.append("🟢 流程全部自动化")

        return actions

    def _generate_recommendations(
        self, risk: RiskAssessment, decision: StrategyDecision
    ) -> List[str]:
        """生成治理建议"""
        recs = []
        if risk.risk_score > 0.7:
            recs.append("⚠️ 风险评分偏高，建议增加审核频次")
        if risk.risk_type.value == "data_leak":
            recs.append("🔐 检测到潜在数据泄露，建议启动泄露排查流程")
        if risk.risk_type.value == "compliance":
            recs.append("📋 检测到合规风险，建议法务团队介入审查")
        if risk.behavior_anomaly > 0.5:
            recs.append("👤 行为模型标记异常，建议验证用户身份")
        recs.append(f"⏱️ {decision.next_evaluation_hours}小时内进行下一次评估")
        return recs


# 全局单例
pipeline = FinGuardPipeline()
