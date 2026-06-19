"""FinAgent Tools — Qwen Agent 自定义工具集

所有工具使用 @register_tool 装饰器注册，会被 Agent 自动发现。
导入此模块即触发所有工具注册。

参考模式:
  - Qwen Agent: @register_tool + BaseTool
  - CrewAI: 每个工具独立职责、自描述
  - LangChain: JSON Schema 参数定义
"""

from finagent.tools.sanitizer import DataSanitizerTool
from finagent.tools.behavior import BehaviorAnalyzerTool
from finagent.tools.compliance import ComplianceSearchTool
from finagent.tools.risk import RiskScorerTool, configure_llm

__all__ = [
    "DataSanitizerTool",
    "BehaviorAnalyzerTool",
    "ComplianceSearchTool",
    "RiskScorerTool",
    "configure_llm",
]
