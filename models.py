"""
FinAgent — 金融大模型安全审计 Agent 系统

基于 Qwen Agent 框架构建。
架构: 自定义 Tools → Assistant Agent → 审计报告 + MAB 策略决策
"""

import os
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════
#  Data Models (de-branded, clean)
# ═══════════════════════════════════════════════════════════

class RiskType(str, Enum):
    COMPLIANCE = "compliance"
    DATA_LEAK = "data_leak"
    MISLEADING = "misleading"
    HALLUCINATION = "hallucination"
    SAFE = "safe"


class StrategyLevel(str, Enum):
    STRICT = "strict"
    STANDARD = "standard"
    LENIENT = "lenient"


@dataclass
class AuditInput:
    """审计输入"""
    id: str = "default"
    scenario: str = "phishing"
    raw_text: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_score: float = 0.0
    risk_type: RiskType = RiskType.SAFE
    confidence: float = 0.5
    indicators: list = field(default_factory=list)
    rag_evidence: list = field(default_factory=list)
    behavior_anomaly: float = 0.0
    llm_raw_response: str = ""


@dataclass
class StrategyDecision:
    """策略决策"""
    recommended: StrategyLevel = StrategyLevel.STANDARD
    block_triggers: list = field(default_factory=list)
    auto_approve_threshold: float = 0.3
    mab_confidence: float = 0.5
    causal_attribution: str = ""
    intervention_layer: str = "Knowledge"
    next_evaluation_hours: int = 24


@dataclass
class AuditReport:
    """完整审计报告"""
    input_id: str = ""
    risk_assessment: RiskAssessment = field(default_factory=RiskAssessment)
    strategy: StrategyDecision = field(default_factory=StrategyDecision)
    actions_taken: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    mab_reward: float | None = None
