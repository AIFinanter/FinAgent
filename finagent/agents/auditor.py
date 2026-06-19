"""
Audit Agent — 金融大模型安全审计 Agent

基于 Qwen Agent Assistant 模式，集成全部自定义工具。
Agent 自主调度工具完成: 脱敏 → 行为分析 → 合规检索 → 风险评分 → 策略决策。

参考实现:
  - Qwen Agent Assistant: 工具调用 + 系统消息
  - CrewAI Agent: 角色定义 + 任务描述 + 工具集
  - AutoGen Assistant: 对话式工具编排
"""

from qwen_agent.agents import Assistant
from qwen_agent.llm import get_chat_model

from config import config
from finagent.tools.risk import configure_llm

# ── Agent 系统消息 ─────────────────────────────
# 参考 CrewAI 的角色定义模式 + Qwen Agent 的工具使用指令

SYSTEM_PROMPT = """# 角色
你是金融大模型安全审计专家。你的任务是对金融 LLM 输出内容进行完整的安全审计。

# 可用工具
你可以使用以下工具完成审计任务，按需自主调度：

1. **data_sanitizer** — 脱敏处理：检测并替换文本中的姓名、身份证号、银行卡号、手机号、IP地址、邮箱等 PII
2. **behavior_analyzer** — 行为异常检测：分析操作元数据，输出 0-1 异常评分（7维特征）
3. **compliance_search** — 合规知识库检索：搜索相关金融监管条文，为合规判定提供依据
4. **risk_scorer** — 风险评分：基于 DeepSeek LLM 进行深度语义分析，输出风险分数和类型

# 审计流程
请按以下逻辑进行审计（可根据实际情况调整工具调用顺序）：

1. **脱敏** — 调用 data_sanitizer 处理原始文本，保护用户隐私
2. **行为分析** — 如有元数据，调用 behavior_analyzer 检测行为异常
3. **合规检索** — 调用 compliance_search 搜索相关监管条文作为判定依据
4. **风险评分** — 调用 risk_scorer 进行最终的综合风险评分

# 输出要求
审计完成后，请输出以下两部分：

## 审计报告（自然语言）
用中文总结审计发现，包括：
- 内容概要
- 各维度风险分析
- 引用的合规条文
- 行为模型交叉验证结果
- 综合判定结论

## 结构化结果（JSON）
```json
{
  "risk_score": 0.0-1.0,
  "primary_risk_type": "compliance|data_leak|misleading|hallucination|safe",
  "secondary_risk_types": [],
  "confidence": 0.0-1.0,
  "recommended_strategy": "strict|standard|lenient",
  "block_triggers": [],
  "key_findings": [],
  "rag_citations": [],
  "intervention_layer": "Data|Information|Knowledge|Wisdom"
}
```

# 注意事项
- 始终先脱敏再分析——永远不要在未脱敏的文本上进行风险评分
- 合规判定必须引用具体条文 ID，不可凭空判断
- 行为异常度 > 0.5 时，应在报告中注明
- 如遇证据冲突，以合规知识库条文为准
"""

# ── 工具列表（Qwen Agent 通过函数名匹配注册的工具） ──

AGENT_TOOLS = [
    "data_sanitizer",
    "behavior_analyzer",
    "compliance_search",
    "risk_scorer",
]


# ── Agent 工厂函数 ─────────────────────────────
# 参考 CrewAI 的 Agent 构造函数模式

def create_audit_agent() -> Assistant:
    """
    创建金融审计 Agent 实例。

    配置 LLM 连接并初始化 Assistant，注入全部自定义工具。

    Returns:
        Qwen Agent Assistant 实例，可直接调用 run() 执行审计
    """
    # 配置 LLM
    llm_cfg = config.llm.to_qwen_llm_cfg()
    if config.llm.api_key:
        configure_llm(
            model=config.llm.model,
            base_url=config.llm.model_server,
            api_key=config.llm.api_key,
        )

    # 创建 Assistant Agent
    agent = Assistant(
        llm=llm_cfg,
        function_list=AGENT_TOOLS,
        system_message=SYSTEM_PROMPT,
        name="FinAgent",
        description="金融大模型安全审计专用 Agent",
    )

    return agent


# ── 便捷函数 ──────────────────────────────────
# 参考 AutoGen 的简化的用户接口

def audit(
    raw_text: str,
    scenario: str = "自定义",
    metadata: dict = None,
    context_level: float = 0.5,
    history_summary: str = "无历史事故记录",
    stream: bool = False,
):
    """
    执行一次完整的金融安全审计。

    Args:
        raw_text: 待审计的金融 LLM 输出内容
        scenario: 金融场景描述
        metadata: 行为元数据（可选）
        context_level: 上下文敏感度
        history_summary: 历史事故摘要
        stream: 是否流式返回

    Yields/Returns:
        审计结果消息
    """
    agent = create_audit_agent()

    # 构造初始消息——引导 Agent 按流程执行
    user_message = f"""请对以下金融 LLM 输出内容进行完整的安全审计。

金融场景: {scenario}
上下文敏感度: {context_level}
历史事故摘要: {history_summary}

{"行为元数据: " + str(metadata) if metadata else "行为元数据: 未提供（可跳过行为分析步骤）"}

待审计内容:
---
{raw_text}
---

请开始审计流程。先调用 data_sanitizer 脱敏，然后按需调用其他工具，最后输出完整的审计报告和结构化 JSON 结果。"""

    messages = [{"role": "user", "content": user_message}]

    if stream:
        return agent.run(messages)  # 返回生成器
    else:
        results = list(agent.run(messages))
        return results
