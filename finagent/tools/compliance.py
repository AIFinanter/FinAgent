"""
Compliance Search Tool — 外挂合规知识库检索

从金融监管法规文件中检索相关条文，为风险判定提供证据。
支持 Qwen Agent Memory RAG（如果可用）和关键词降级搜索。

参考: Qwen Agent Memory 模块 + LlamaIndex 检索模式
"""

import json
import os
import re
from typing import Union

from qwen_agent.tools.base import BaseTool, register_tool


# ── 法规加载 ──────────────────────────────────

_regulations_cache = None


def _load_regulations() -> list:
    """加载法规 JSON 文件（带缓存）"""
    global _regulations_cache
    if _regulations_cache is not None:
        return _regulations_cache

    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "knowledge_base", "regulations", "finance_regulations.json",
    )
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            _regulations_cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _regulations_cache = []
    return _regulations_cache


# ── 关键词搜索 ────────────────────────────────

def _keyword_search(query: str, top_k: int = 5) -> list:
    """对法规条文进行关键词匹配搜索"""
    regs = _load_regulations()
    if not regs:
        return []

    scored = []
    query_terms = set(re.findall(r'[一-鿿]+|[a-zA-Z]+', query.lower()))

    for reg in regs:
        content = reg.get("content", "")
        content_lower = content.lower()

        # 计算命中分数
        hits = sum(1 for term in query_terms if term.lower() in content_lower)
        if hits == 0:
            continue

        # 精确匹配加分
        bonus = 2 if any(term in content for term in query_terms if len(term) >= 3) else 0

        scored.append({
            "id": reg.get("id", ""),
            "source": reg.get("source", ""),
            "article": reg.get("article", ""),
            "category": reg.get("category", ""),
            "content": content,
            "penalty": reg.get("penalty", ""),
            "score": hits + bonus,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ── 工具注册 ──────────────────────────────────

@register_tool("compliance_search")
class ComplianceSearchTool(BaseTool):
    """合规知识库检索工具 — 搜索相关金融监管条文"""

    description = (
        "从金融合规知识库中检索与查询内容相关的监管条文。"
        "知识库覆盖: 数据隐私、数据安全、跨境数据、AI治理、反洗钱、消费者保护等领域。"
        "返回条文 ID、出处、条款内容及违规处罚信息，用于辅助风险合规判定。"
        "当需要判断某内容是否违反金融监管规定时，应优先调用此工具获取条文依据。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "description": "检索查询文本，可以是风险关键词、可疑内容片段或合规问题描述",
                "type": "string",
            },
            "top_k": {
                "description": "返回的条文数量，默认 5",
                "type": "integer",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def call(self, params: Union[str, dict], **kwargs) -> dict:
        params = self._verify_json_format_args(params)
        query = params.get("query", "")
        top_k = params.get("top_k", 5)

        results = _keyword_search(query, top_k)

        return {
            "query": query,
            "total_found": len(results),
            "results": [
                {
                    "id": r["id"],
                    "source": f"{r['source']} {r['article']}",
                    "category": r["category"],
                    "content": r["content"],
                    "penalty": r["penalty"],
                    "relevance_score": r["score"],
                }
                for r in results
            ],
        }
