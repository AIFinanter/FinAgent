# 🛡️ FinAgent — 金融大模型安全审计 Agent

> **基于 Qwen Agent 框架的金融内容安全审计系统**
>
> 架构: Assistant + Tools · Agent 自主调度 · Thompson Sampling MAB

---

## 核心设计

| 组件 | 技术实现 | 参考模式 |
|------|---------|---------|
| 🤖 **审计 Agent** | Qwen Agent Assistant 自主调度 | Qwen Agent + CrewAI |
| 🔧 **工具集** | 4 个 @register_tool 工具 | LangChain BaseTool |
| 📚 **合规知识库** | 关键词+语义混合检索 | Qwen Agent Memory |
| 🎰 **自适应 MAB** | Thompson Sampling 策略选择 | Beta-Bernoulli Bandit |
| 🔍 **可解释性** | Agent 输出自然语言报告 + 结构化 JSON | AutoGen 对话模式 |

## 架构

```
┌──────────────────────────────────────────────────┐
│                 FinAgent v3.0                      │
│            Qwen Agent Assistant + Tools            │
├───────────────────────────────────────────────────┤
│                                                    │
│  User Input → Assistant Agent                      │
│                  ├── data_sanitizer (脱敏)          │
│                  ├── behavior_analyzer (行为检测)   │
│                  ├── compliance_search (合规检索)   │
│                  └── risk_scorer (风险评分)         │
│                                                    │
│  Agent Output → 审计报告 + 结构化 JSON              │
│                  + MAB 策略决策                     │
│                                                    │
├───────────────────────────────────────────────────┤
│  底层: Qwen Agent (Assistant/Memory/Tool/LLM)       │
└───────────────────────────────────────────────────┘
```

## 与旧版对比

| 维度 | v2.0 (FinGuard+FinHarness) | v3.0 (FinAgent) |
|------|---------------------------|-----------------|
| 架构 | 硬编码 DIKW 流水线 | Qwen Agent Assistant 自主调度 |
| LLM 调用 | 两次（评分 + 策略选择） | 一次 Agent 会话 |
| RAG 集成 | 检索后丢弃 | Agent 工具内自动注入 |
| 可扩展性 | 改流水线需改代码 | 新增 @register_tool 即插即用 |
| Prompt | 简化版硬编码 | 完整多段式 prompt（含 few-shot） |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 环境变量
export DEEPSEEK_API_KEY="sk-xxx"

# 或在 Streamlit 侧边栏输入（加密存储）
```

### 3. 启动服务

```bash
# API 服务
uvicorn app:app --reload --port 8000

# Streamlit UI
streamlit run frontend/streamlit_app.py --server.port 8501
```

### 4. 使用 Agent

```python
from finagent.agents import create_audit_agent

agent = create_audit_agent()
messages = [{"role": "user", "content": "审计这段文本: ..."}]
for response in agent.run(messages):
    print(response)
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/evaluate` | Agent 完整审计 |
| POST | `/feedback` | MAB 奖励反馈 |
| GET | `/mab/status` | MAB 状态 |
| POST | `/mab/simulate?rounds=N` | MAB 收敛模拟 |
| POST | `/sanitize?text=...` | 仅脱敏 |
| POST | `/behavior` | 仅行为检测 |
| POST | `/compliance/search?query=...` | 仅合规检索 |

## 项目结构

```
finharness_adaptive/
├── app.py                     # FastAPI 入口
├── config.py                  # 配置中心
├── models.py                  # 数据模型
├── finagent/                  # Agent 核心包
│   ├── agents/
│   │   └── auditor.py         # 审计 Agent (Assistant)
│   ├── tools/                 # Qwen Agent 工具集
│   │   ├── sanitizer.py       # 脱敏工具
│   │   ├── behavior.py        # 行为检测工具
│   │   ├── compliance.py      # 合规检索工具
│   │   └── risk.py            # 风险评分工具
│   └── mab/
│       └── bandit.py          # Thompson Sampling 引擎
├── finguard/                  # [兼容] 旧模块 (crypto_utils)
├── knowledge_base/            # 合规法规库
├── prompts/                   # LLM Prompt 模板
├── frontend/                  # Streamlit UI
├── scripts/                   # 工具脚本
└── tests/                     # 测试
```

## 参考文献

- Qwen Agent: https://github.com/QwenLM/Qwen-Agent
- 徐心 et al. "Information Consumption, Risk Preference, and Portfolio Adjustment"
- 徐心 & 蔡瑶 "数智流：企业数据资产的建设路径", 清华管理评论, 2024

## License

MIT
