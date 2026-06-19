"""
FinAgent — FastAPI Entry Point

基于 Qwen Agent 框架的金融大模型安全审计系统。
Agent 自主调度工具完成: 脱敏 → 行为分析 → 合规检索 → 风险评分 → 策略决策。

对比旧版:
  - 旧: 硬编码 DIKW 流水线 (pipeline.py)
  - 新: Qwen Agent Assistant 自主调度工具
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import config
from models import AuditInput, RiskAssessment, StrategyDecision, AuditReport, RiskType, StrategyLevel

# ── 延迟导入 Agent（避免启动时加载 LLM） ──────

_agent = None


def _get_agent():
    """延迟初始化 Agent 单例"""
    global _agent
    if _agent is None:
        # 导入工具（触发注册）
        import finagent.tools  # noqa: F401
        from finagent.agents import create_audit_agent
        _agent = create_audit_agent()
    return _agent


# ── FastAPI App ─────────────────────────────────

app = FastAPI(
    title="FinAgent · 金融安全审计",
    description="基于 Qwen Agent 框架的金融大模型安全审计系统 — Assistant + Tools 架构",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════
#  Request Models
# ═══════════════════════════════════════════════════════════

class EvaluateRequest(BaseModel):
    id: str = "default"
    scenario: str = Field(default="phishing", description="金融场景: phishing / login / transaction / aml")
    raw_text: str = Field(default="", description="待审计的金融 LLM 输出内容")
    metadata: dict = Field(default_factory=dict, description="行为元数据")
    context_level: float = Field(default=0.5, ge=0.0, le=1.0)
    history_summary: str = Field(default="无历史事故记录")


class FeedbackRequest(BaseModel):
    strategy: str = Field(default="standard", description="采用的策略")
    outcome: str = Field(default="pass", description="治理结果: pass / block / incident")
    latency_ms: int = Field(default=300)
    is_false_positive: bool = False


class KeyConfigRequest(BaseModel):
    api_key: str


# ═══════════════════════════════════════════════════════════
#  API Routes
# ═══════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "FinAgent · 金融安全审计",
        "version": "3.0.0",
        "framework": "Qwen Agent",
        "architecture": "Assistant + Tools (Agent 自主调度)",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "llm_model": config.llm.model,
        "llm_server": config.llm.model_server,
        "mab_arms": list(config.mab.arms),
        "api_key_configured": bool(config.llm.api_key),
    }


@app.post("/evaluate")
async def evaluate(req: EvaluateRequest):
    """
    金融安全审计 — Agent 自主调度完整流程。

    Agent 会自动:
    1. data_sanitizer → 脱敏
    2. behavior_analyzer → 行为异常检测
    3. compliance_search → 合规知识库检索
    4. risk_scorer → 深度语义风险评分
    5. 综合输出审计报告 + 结构化 JSON
    """
    try:
        agent = _get_agent()

        # 构造审计请求
        metadata_str = "未提供"
        if req.metadata:
            metadata_str = str(req.metadata)

        user_message = f"""请对以下金融 LLM 输出内容进行完整的安全审计。

金融场景: {req.scenario}
上下文敏感度: {req.context_level}
历史事故摘要: {req.history_summary}

行为元数据: {metadata_str}

待审计内容:
---
{req.raw_text}
---

请按审计流程执行：先脱敏 → 行为分析 → 合规检索 → 风险评分 → 输出报告。"""

        messages = [{"role": "user", "content": user_message}]
        results = list(agent.run(messages))

        # 提取最后一条完整响应
        final_response = ""
        for msg in results:
            if hasattr(msg, "content") and msg.content:
                final_response += str(msg.content) + "\n"
            elif isinstance(msg, dict) and msg.get("content"):
                final_response += str(msg["content"]) + "\n"

        return {
            "id": req.id,
            "scenario": req.scenario,
            "raw_response": final_response.strip(),
            "message_count": len(results),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    """
    MAB 奖励反馈闭环 — 根据实际治理结果更新 Thompson Sampling 参数。
    """
    from finagent.mab import compute_reward
    from finagent.mab import ThompsonBandit

    reward = compute_reward(
        outcome=req.outcome,
        latency_ms=req.latency_ms,
        strategy=req.strategy,
        is_false_positive=req.is_false_positive,
    )

    return {
        "reward": reward,
        "outcome": req.outcome,
        "strategy": req.strategy,
    }


@app.get("/mab/status")
async def mab_status():
    """获取 MAB 引擎当前状态（从 session 获取或新建）"""
    from finagent.mab import ThompsonBandit

    bandit = ThompsonBandit(config.mab.arms)
    return {
        "arms": bandit.arms,
        "expected_values": bandit.expected_values(),
        "total_trials": bandit.total_trials,
    }


@app.post("/mab/simulate")
async def mab_simulate(rounds: int = 100):
    """模拟 MAB 收敛 — 验证 Thompson Sampling 行为"""
    import random
    from finagent.mab import ThompsonBandit, compute_reward

    bandit = ThompsonBandit(config.mab.arms)
    true_rates = {"strict": 0.8, "standard": 0.5, "lenient": 0.3}

    for _ in range(rounds):
        chosen, _ = bandit.pull()
        success = random.random() < true_rates[chosen]
        reward = 0.9 if success else 0.3
        bandit.update(chosen, reward)

    return {
        "rounds": rounds,
        "final_expected_values": bandit.expected_values(),
        "convergence_data": bandit.convergence_data(),
        "summary": f"strict={bandit.expected_values()['strict']:.2%}, "
                   f"standard={bandit.expected_values()['standard']:.2%}, "
                   f"lenient={bandit.expected_values()['lenient']:.2%}",
    }


@app.post("/sanitize")
async def sanitize_text(text: str):
    """仅执行脱敏"""
    from finagent.tools.sanitizer import DataSanitizerTool
    tool = DataSanitizerTool()
    return tool.call({"text": text})


@app.post("/behavior")
async def behavior_check(meta: dict):
    """仅执行行为异常检测"""
    from finagent.tools.behavior import BehaviorAnalyzerTool
    tool = BehaviorAnalyzerTool()
    return tool.call({"meta": meta})


@app.post("/compliance/search")
async def compliance_search(query: str, top_k: int = 5):
    """仅执行合规知识库检索"""
    from finagent.tools.compliance import ComplianceSearchTool
    tool = ComplianceSearchTool()
    return tool.call({"query": query, "top_k": top_k})


# ═══════════════════════════════════════════════════════════
#  论文增强: DIKW 血缘 + A/B实验 + 特征重要性 + 场景模板
# ═══════════════════════════════════════════════════════════

@app.get("/lineage")
async def get_lineage_list():
    """获取所有 DIKW 数据血缘记录 (双螺旋结构)"""
    from finagent.lineage import get_all_lineages, lineage_summary
    lineages = get_all_lineages()
    return {
        "total": len(lineages),
        "summary": lineage_summary(),
        "records": [l.to_dict() for l in lineages],
    }


@app.get("/lineage/{audit_id}")
async def get_lineage_detail(audit_id: str):
    """获取单条审计的完整 DIKW 数据血缘"""
    from finagent.lineage import get_lineage
    lineage = get_lineage(audit_id)
    if not lineage:
        raise HTTPException(status_code=404, detail=f"未找到审计记录: {audit_id}")
    return lineage.to_dict()


@app.get("/experiments")
async def list_experiments():
    """获取所有 A/B 实验"""
    from finagent.experiment import get_all_experiments
    return get_all_experiments()


@app.post("/experiments/create")
async def create_experiment_endpoint(name: str, description: str = "", strategies: str = None):
    """创建新的 A/B 对照实验"""
    from finagent.experiment import create_experiment
    strategies_list = strategies.split(",") if strategies else None
    exp = create_experiment(name, description, strategies_list)
    return exp.to_dict()


@app.post("/vrio")
async def vrio_analysis_endpoint(audit_features: dict):
    """VRIO 竞争力分析"""
    from finagent.experiment import vrio_analysis
    return vrio_analysis(audit_features)


@app.post("/feature-importance")
async def feature_importance_endpoint(features: dict, risk_score: float):
    """计算特征重要性归因 (经济机制)"""
    from finagent.experiment import compute_feature_importance
    return compute_feature_importance(features, risk_score)


@app.get("/scenarios")
async def list_scenario_templates():
    """获取所有业务场景模板 (论文案例)"""
    from finagent.scenarios import get_all_templates
    return get_all_templates()


@app.get("/scenarios/{template_id}")
async def apply_scenario_template(template_id: str):
    """应用场景模板 — 返回预设输入和元数据"""
    from finagent.scenarios import apply_template
    result = apply_template(template_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"未找到场景模板: {template_id}")
    return result


# ═══════════════════════════════════════════════════════════
#  API Key 管理
# ═══════════════════════════════════════════════════════════

@app.get("/api-key/status")
async def api_key_status():
    """检查 API Key 是否已配置"""
    from finguard.crypto_utils import has_stored_key

    has_env = bool(os.environ.get("DEEPSEEK_API_KEY", ""))
    has_stored = has_stored_key()
    key_source = "env" if has_env else ("stored" if has_stored else "none")

    return {
        "configured": has_env or has_stored,
        "source": key_source,
        "masked_key": mask_key(config.llm.api_key),
    }


@app.post("/api-key/set")
async def set_api_key(req: KeyConfigRequest):
    """设置并加密存储 API Key"""
    from finguard.crypto_utils import encrypt_api_key

    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API Key 不能为空")

    key = req.api_key.strip()
    if not key.startswith("sk-"):
        raise HTTPException(status_code=400, detail="API Key 格式不正确，应以 sk- 开头")

    encrypt_api_key(key, persist=True)
    config.llm.api_key = key

    return {"success": True, "masked_key": mask_key(key), "message": "API Key 已加密存储并生效"}


@app.post("/api-key/clear")
async def clear_api_key():
    """清除加密存储的 API Key"""
    from finguard.crypto_utils import clear_api_key

    cleared = clear_api_key()
    config.llm.api_key = ""
    return {"success": cleared, "message": "API Key 已清除" if cleared else "无存储的 API Key"}


def mask_key(key: str, visible: int = 7) -> str:
    if not key:
        return "未配置"
    if len(key) <= visible + 4:
        return key[:3] + "***"
    return f"{key[:visible]}...{key[-4:]}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
