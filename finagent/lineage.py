"""
Data Lineage Tracker — DIKW 双螺旋数据血缘追踪

实现论文中的核心概念:
  - 数据螺旋: 单点数据→全局数据(D→I), 单领域→跨领域(I→K), 已知→预测(K→W)
  - 知识螺旋: D→I需要业务场景, I→K需要理论指导, K→W需要创造引领

每条审计记录在 DIKW 四层的转换过程被完整追踪，形成端到端的"数据血缘"。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class DIKWLayer(str, Enum):
    DATA = "Data"           # 原始数据
    INFORMATION = "Information"  # 加工后的信息
    KNOWLEDGE = "Knowledge"     # 规律性认知
    WISDOM = "Wisdom"           # 预测与决策


class SpiralType(str, Enum):
    DATA_SPIRAL = "data_spiral"      # 数据螺旋
    KNOWLEDGE_SPIRAL = "knowledge_spiral"  # 知识螺旋


@dataclass
class LayerTransition:
    """DIKW 层间转换记录 — 对应双螺旋的一次跃迁"""
    from_layer: DIKWLayer
    to_layer: DIKWLayer
    spiral_type: SpiralType
    input_summary: str        # 输入数据摘要
    output_summary: str       # 输出结果摘要
    transformation: str       # 转换方式描述
    context: str = ""         # 业务场景/理论指导/创造引领
    tool_used: str = ""       # 使用的工具/模型
    confidence: float = 1.0   # 转换置信度
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "from": self.from_layer.value,
            "to": self.to_layer.value,
            "spiral": self.spiral_type.value,
            "input": self.input_summary,
            "output": self.output_summary,
            "transformation": self.transformation,
            "context": self.context,
            "tool": self.tool_used,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DataLineage:
    """完整的 DIKW 数据血缘追踪 — 一条审计记录的四层跃迁路径"""
    audit_id: str
    scenario: str = ""
    transitions: List[LayerTransition] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def record_transition(
        self,
        from_layer: DIKWLayer,
        to_layer: DIKWLayer,
        spiral_type: SpiralType,
        input_summary: str,
        output_summary: str,
        transformation: str,
        context: str = "",
        tool_used: str = "",
        confidence: float = 1.0,
    ):
        """记录一次 DIKW 层间跃迁"""
        t = LayerTransition(
            from_layer=from_layer,
            to_layer=to_layer,
            spiral_type=spiral_type,
            input_summary=input_summary[:200],
            output_summary=output_summary[:200],
            transformation=transformation,
            context=context,
            tool_used=tool_used,
            confidence=confidence,
        )
        self.transitions.append(t)
        return t

    def to_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "scenario": self.scenario,
            "transitions": [t.to_dict() for t in self.transitions],
            "created_at": self.created_at.isoformat(),
            "summary": self.summarize(),
        }

    def summarize(self) -> dict:
        """生成 DIKW 四层摘要"""
        layers = {l: [] for l in DIKWLayer}
        for t in self.transitions:
            layers[t.from_layer].append(t)
            layers[t.to_layer].append(t)

        return {
            "Data": {
                "description": "原始文本输入",
                "transformations": len([t for t in self.transitions if t.from_layer == DIKWLayer.DATA]),
                "tools": list(set(t.tool_used for t in self.transitions if t.from_layer == DIKWLayer.DATA)),
            },
            "Information": {
                "description": "行为特征提取 + 脱敏处理",
                "transformations": len([t for t in self.transitions if t.to_layer == DIKWLayer.INFORMATION]),
                "tools": list(set(t.tool_used for t in self.transitions if t.to_layer == DIKWLayer.INFORMATION)),
            },
            "Knowledge": {
                "description": "合规条文匹配 + LLM 语义分析",
                "transformations": len([t for t in self.transitions if t.to_layer == DIKWLayer.KNOWLEDGE]),
                "tools": list(set(t.tool_used for t in self.transitions if t.to_layer == DIKWLayer.KNOWLEDGE)),
            },
            "Wisdom": {
                "description": "策略决策 + MAB 自适应选择",
                "transformations": len([t for t in self.transitions if t.to_layer == DIKWLayer.WISDOM]),
                "tools": list(set(t.tool_used for t in self.transitions if t.to_layer == DIKWLayer.WISDOM)),
            },
        }

    def dual_helix_view(self) -> dict:
        """
        双螺旋视图 — 分别展示数据螺旋和知识螺旋的推进路径。

        数据螺旋: D→I (单点→全局) → I→K (单领域→跨领域) → K→W (已知→预测)
        知识螺旋: D→I (业务场景驱动) → I→K (理论指导) → K→W (创造引领)
        """
        data_spiral = [t for t in self.transitions if t.spiral_type == SpiralType.DATA_SPIRAL]
        knowledge_spiral = [t for t in self.transitions if t.spiral_type == SpiralType.KNOWLEDGE_SPIRAL]

        return {
            "data_spiral": {
                "label": "数据螺旋: 单点→全局→跨领域→预测",
                "steps": [
                    {"stage": "D→I", "desc": "从单点数据到全局信息", "context": ""},
                    {"stage": "I→K", "desc": "从单领域信息到跨领域知识", "context": ""},
                    {"stage": "K→W", "desc": "从已有知识到预测未来", "context": ""},
                ],
                "completed": len(data_spiral),
            },
            "knowledge_spiral": {
                "label": "知识螺旋: 场景→理论→创造",
                "steps": [
                    {"stage": "D→I", "desc": "需要加入对业务场景的认知", "context": self.scenario},
                    {"stage": "I→K", "desc": "需要理论作指导", "context": "金融监管法规 + 风险评估理论"},
                    {"stage": "K→W", "desc": "需要创造引领", "context": "MAB自适应策略 + 可解释归因"},
                ],
                "completed": len(knowledge_spiral),
            },
        }


# ── 全局血缘库 ──────────────────────────────

_lineage_store: dict[str, DataLineage] = {}


def create_lineage(audit_id: str, scenario: str = "") -> DataLineage:
    """创建一条新的数据血缘追踪记录"""
    lineage = DataLineage(audit_id=audit_id, scenario=scenario)
    _lineage_store[audit_id] = lineage
    return lineage


def get_lineage(audit_id: str) -> Optional[DataLineage]:
    """获取已有血缘记录"""
    return _lineage_store.get(audit_id)


def get_all_lineages() -> List[DataLineage]:
    """获取所有血缘记录"""
    return list(_lineage_store.values())


def lineage_summary() -> dict:
    """全局血缘概览"""
    lineages = get_all_lineages()
    if not lineages:
        return {"total": 0, "by_scenario": {}, "avg_transitions": 0}

    by_scenario = {}
    for l in lineages:
        by_scenario[l.scenario] = by_scenario.get(l.scenario, 0) + 1

    return {
        "total": len(lineages),
        "by_scenario": by_scenario,
        "avg_transitions": sum(len(l.transitions) for l in lineages) / len(lineages),
        "recent": [l.to_dict() for l in sorted(lineages, key=lambda x: x.created_at, reverse=True)[:5]],
    }
