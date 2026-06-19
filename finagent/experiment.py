"""
A/B Experiment Engine — 策略对照实验 & 实物期权评估

实现论文中的核心概念:
  - STEP-Process: 以A/B测试为代表的因果推断方法，科学评估数字化运营的经济价值
  - 实物期权理论: 分步分层投资，每阶段有选择权价值

对比 MAB (Thompson Sampling) 与 A/B Test 的差异:
  - A/B Test: 等比例分流，统计显著性检验，适合一次性验证
  - MAB: 动态调整分流比例，持续优化，适合在线学习
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import math


# ═══════════════════════════════════════════════════════════
#  A/B Experiment
# ═══════════════════════════════════════════════════════════

@dataclass
class ExperimentGroup:
    """实验组"""
    name: str
    strategy: str           # strict | standard | lenient
    sample_size: int = 0
    successes: int = 0      # 正向结果数
    failures: int = 0       # 负向结果数
    total_latency_ms: int = 0

    @property
    def success_rate(self) -> float:
        if self.sample_size == 0:
            return 0.0
        return self.successes / self.sample_size

    @property
    def avg_latency(self) -> float:
        if self.sample_size == 0:
            return 0.0
        return self.total_latency_ms / self.sample_size

    def record(self, outcome: str, latency_ms: int = 0):
        self.sample_size += 1
        if outcome == "pass":
            self.successes += 1
        elif outcome in ("block", "incident"):
            self.failures += 1
        self.total_latency_ms += latency_ms


@dataclass
class ABExperiment:
    """A/B 对照实验 — 科学评估治理策略的经济价值"""

    name: str
    description: str = ""
    control: ExperimentGroup = field(default_factory=lambda: ExperimentGroup("control", "standard"))
    treatments: List[ExperimentGroup] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "running"  # running | completed | stopped

    @property
    def total_samples(self) -> int:
        return self.control.sample_size + sum(t.sample_size for t in self.treatments)

    def best_group(self) -> ExperimentGroup:
        """返回成功率最高的组"""
        all_groups = [self.control] + self.treatments
        return max(all_groups, key=lambda g: g.success_rate)

    def lift_vs_control(self, treatment: ExperimentGroup) -> dict:
        """计算 treatment 相对 control 的提升"""
        if self.control.sample_size == 0:
            return {"lift": 0, "significant": False}

        control_rate = self.control.success_rate
        treatment_rate = treatment.success_rate
        if control_rate == 0:
            lift = float('inf') if treatment_rate > 0 else 0
        else:
            lift = (treatment_rate - control_rate) / control_rate

        # Wald z-test for proportions
        n1, n2 = self.control.sample_size, treatment.sample_size
        p1, p2 = control_rate, treatment_rate
        if n1 > 0 and n2 > 0:
            p_pool = (self.control.successes + treatment.successes) / (n1 + n2)
            se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
            z_score = (p2 - p1) / se if se > 0 else 0
            # Two-tailed test at 95% confidence
            significant = abs(z_score) > 1.96
        else:
            z_score = 0
            significant = False

        return {
            "treatment": treatment.name,
            "control_rate": round(control_rate, 4),
            "treatment_rate": round(treatment_rate, 4),
            "lift": f"{lift:.1%}",
            "lift_raw": round(lift, 4),
            "z_score": round(z_score, 2),
            "significant": significant,
            "confidence": "95%",
            "verdict": "✅ 显著优于对照组" if (significant and lift > 0)
                       else "⚠️ 显著差于对照组" if (significant and lift < 0)
                       else "➖ 无显著差异",
        }

    def to_dict(self) -> dict:
        groups_data = []
        for g in [self.control] + self.treatments:
            groups_data.append({
                "name": g.name,
                "strategy": g.strategy,
                "sample_size": g.sample_size,
                "success_rate": round(g.success_rate, 4),
                "avg_latency_ms": round(g.avg_latency, 1),
            })

        return {
            "name": self.name,
            "description": self.description,
            "total_samples": self.total_samples,
            "status": self.status,
            "groups": groups_data,
            "best_group": self.best_group().name if self.total_samples > 0 else "N/A",
            "lift_analysis": [self.lift_vs_control(t) for t in self.treatments] if self.control.sample_size > 0 else [],
            "created_at": self.created_at.isoformat(),
        }


# ── 全局实验管理 ──────────────────────────────

_experiments: dict[str, ABExperiment] = {}


def create_experiment(name: str, description: str = "", strategies: list = None) -> ABExperiment:
    """创建一个新的 A/B 实验"""
    if strategies is None:
        strategies = ["strict", "standard", "lenient"]

    control = ExperimentGroup("control", strategies[1] if len(strategies) > 1 else "standard")
    treatments = [
        ExperimentGroup(f"treatment_{s}", s)
        for s in strategies if s != control.strategy
    ]

    exp = ABExperiment(name=name, description=description, control=control, treatments=treatments)
    _experiments[name] = exp
    return exp


def get_experiment(name: str) -> Optional[ABExperiment]:
    return _experiments.get(name)


def get_all_experiments() -> dict:
    return {name: exp.to_dict() for name, exp in _experiments.items()}


# ═══════════════════════════════════════════════════════════
#  VRIO 竞争力分析
# ═══════════════════════════════════════════════════════════

def vrio_analysis(audit_features: dict) -> dict:
    """
    VRIO 模型分析 — 评估数据资产是否构成可持续竞争优势。

    V: Valuable (有价值) — 数据/能力能否增加价值？
    R: Rarity (稀缺) — 是否大部分竞争者没有？
    I: Inimitability (不可模仿) — 是否不容易被模仿？
    O: Organization (组织) — 企业是否被有效组织起来利用？

    四个条件同时满足 → 可持续竞争优势
    """
    scores = {}

    # V: 有价值 — 基于风险检出能力
    risk_detected = audit_features.get("risk_score", 0) > 0.3
    scores["V_valuable"] = {
        "score": risk_detected,
        "label": "有价值" if risk_detected else "价值有限",
        "rationale": "系统成功检出潜在风险，为业务创造安全价值" if risk_detected
                     else "当前未检出显著风险，价值有待验证",
    }

    # R: 稀缺 — 基于是否使用 LLM + RAG (vs 规则引擎)
    uses_llm = audit_features.get("uses_llm", False)
    uses_rag = audit_features.get("rag_evidence_count", 0) > 0
    scores["R_rarity"] = {
        "score": uses_llm and uses_rag,
        "label": "稀缺" if (uses_llm and uses_rag) else "不稀缺",
        "rationale": "LLM+RAG 组合提供深度语义理解 + 实时合规检索能力" if (uses_llm and uses_rag)
                     else "关键词规则引擎可被轻易复制，不构成稀缺能力",
    }

    # I: 不可模仿 — 基于是否有定制化知识库 + MAB 自适应
    has_custom_kb = audit_features.get("rag_evidence_count", 0) >= 3
    has_mab_adaptation = audit_features.get("mab_trials", 0) > 10
    scores["I_inimitability"] = {
        "score": has_custom_kb and has_mab_adaptation,
        "label": "不可模仿" if (has_custom_kb and has_mab_adaptation) else "可模仿",
        "rationale": "定制化合规知识库 + MAB自适应学习构成竞争壁垒" if (has_custom_kb and has_mab_adaptation)
                     else "缺少定制化积累和自适应优化，能力可被模仿",
    }

    # O: 组织 — 基于是否有反馈闭环
    has_feedback = audit_features.get("feedback_count", 0) > 0
    scores["O_organization"] = {
        "score": has_feedback,
        "label": "组织有效" if has_feedback else "组织待完善",
        "rationale": "建立了反馈闭环，组织层面有效利用数据资产" if has_feedback
                     else "缺少反馈机制，数据资产未在组织层面形成闭环",
    }

    all_pass = all(s["score"] for s in scores.values())
    pass_count = sum(1 for s in scores.values() if s["score"])

    return {
        "dimensions": scores,
        "pass_count": pass_count,
        "total": 4,
        "verdict": {
            0: "⚠️ 竞争劣势 — 数据资产未形成竞争力",
            1: "⚠️ 竞争劣势 — 仅满足个别条件",
            2: "➖ 竞争均势 — 与行业平均水平持平",
            3: "📈 临时竞争优势 — 接近但未达到可持续",
            4: "🏆 可持续竞争优势 — 四个条件全部满足",
        }.get(pass_count, "未知"),
        "recommendation": _vrio_recommendation(scores),
    }


def _vrio_recommendation(scores: dict) -> str:
    """根据 VRIO 分析生成改进建议"""
    recs = []
    if not scores["V_valuable"]["score"]:
        recs.append("提升风险检测灵敏度，确保系统能创造实际安全价值")
    if not scores["R_rarity"]["score"]:
        recs.append("接入 LLM 审计 + RAG 合规知识库，摆脱可被复制的规则引擎模式")
    if not scores["I_inimitability"]["score"]:
        recs.append("积累定制化合规数据 + 持续运行 MAB 自适应学习，建立不可模仿的竞争壁垒")
    if not scores["O_organization"]["score"]:
        recs.append("建立反馈闭环机制，将审计结果纳入组织决策流程")
    return "; ".join(recs) if recs else "维持当前优势，持续积累数据资产"


# ═══════════════════════════════════════════════════════════
#  特征重要性 — 经济机制 (论文 Section: 经济机制)
# ═══════════════════════════════════════════════════════════

FEATURE_LABELS = {
    "time_anomaly": "时间异常度",
    "geo_distance": "地理跳变",
    "action_frequency": "操作频率",
    "amount_deviation": "金额偏离度",
    "sensitive_word_ratio": "敏感词占比",
    "device_repeat": "设备重复度",
    "history_failures": "历史失败次数",
}


def compute_feature_importance(features: dict, risk_score: float) -> dict:
    """
    计算各特征对风险评分的贡献度。

    实现论文中"经济机制"的概念:
      - 每个特征按权重贡献于风险评分
      - 特征贡献可作为内部市场化"按贡献分配"的依据

    简化方法: 特征值 × 归一化权重 → 贡献度
    """
    if not features:
        return {"features": {}, "total_contribution": 0}

    contributions = {}
    total = sum(abs(v) for v in features.values()) or 1

    for name, value in features.items():
        weight = abs(value) / total
        contribution = weight * risk_score
        contributions[name] = {
            "label": FEATURE_LABELS.get(name, name),
            "value": round(value, 4),
            "weight": round(weight, 4),
            "contribution": round(contribution, 6),
            "percentage": f"{weight:.1%}",
        }

    # 排序: 贡献度从高到低
    sorted_features = dict(
        sorted(contributions.items(), key=lambda x: x[1]["contribution"], reverse=True)
    )

    return {
        "features": sorted_features,
        "total_contribution": round(sum(c["contribution"] for c in sorted_features.values()), 6),
        "top_driver": next(iter(sorted_features.keys())) if sorted_features else "N/A",
        "top_driver_label": FEATURE_LABELS.get(
            next(iter(sorted_features.keys())), "N/A"
        ) if sorted_features else "N/A",
    }
