"""
FinAgent — 金融大模型安全审计 Agent 框架

基于 Qwen Agent 框架构建的金融内容安全审计系统。
使用 Assistant + Tools 模式，Agent 自主调度工具完成 DIKW 审计流水线。

参考:
  - Qwen Agent (QwenLM/Qwen-Agent): Assistant + BaseTool 框架
  - CrewAI: 角色定义 + 任务描述 + 工具集模式
  - 徐心 & 蔡瑶 (2024): "数智流：企业数据资产的建设路径", 清华管理评论
    DIKW 双螺旋结构、STEP 框架、VRIO 模型、实物期权理论

Quickstart:
    >>> from finagent.agents import create_audit_agent
    >>> agent = create_audit_agent()
"""

from finagent.tools import (
    DataSanitizerTool,
    BehaviorAnalyzerTool,
    ComplianceSearchTool,
    RiskScorerTool,
    configure_llm,
)
from finagent.agents import create_audit_agent, audit
from finagent.mab import ThompsonBandit, compute_reward
from finagent.lineage import (
    DataLineage,
    create_lineage,
    get_lineage,
    get_all_lineages,
    lineage_summary,
    DIKWLayer,
    SpiralType,
)
from finagent.experiment import (
    ABExperiment,
    ExperimentGroup,
    create_experiment,
    get_experiment,
    get_all_experiments,
    vrio_analysis,
    compute_feature_importance,
)
from finagent.scenarios import (
    SCENARIO_TEMPLATES,
    get_all_templates,
    get_template,
    apply_template,
)

__all__ = [
    # Agent
    "create_audit_agent",
    "audit",
    # Tools
    "DataSanitizerTool",
    "BehaviorAnalyzerTool",
    "ComplianceSearchTool",
    "RiskScorerTool",
    "configure_llm",
    # MAB
    "ThompsonBandit",
    "compute_reward",
    # Lineage (数智流双螺旋)
    "DataLineage",
    "create_lineage",
    "get_lineage",
    "get_all_lineages",
    "lineage_summary",
    "DIKWLayer",
    "SpiralType",
    # Experiment (A/B + VRIO + 特征重要性)
    "ABExperiment",
    "ExperimentGroup",
    "create_experiment",
    "get_experiment",
    "get_all_experiments",
    "vrio_analysis",
    "compute_feature_importance",
    # Scenarios (业务场景模板)
    "SCENARIO_TEMPLATES",
    "get_all_templates",
    "get_template",
    "apply_template",
]
