"""
Knowledge Base — RAG 合规知识库引擎 (Qwen Agent 版本)

基于 Qwen Agent Memory 模块:
  - 使用内置 keyword_search + front_page_search 混合检索
  - 自动文档解析与分块
  - 支持多文档管理
"""

from typing import List, Optional

from qwen_agent.memory import Memory
from qwen_agent.llm import BaseChatModel


class ComplianceRAG:
    """
    外挂合规知识库: 基于 Qwen Agent Memory

    核心能力:
    1. 从法规文本文件构建可检索索引
    2. 语义+关键词混合检索
    3. 返回带溯源的条文引用
    """

    def __init__(
        self,
        regulations_file: str,
        llm: Optional[BaseChatModel] = None,
        max_ref_token: int = 4000,
        parser_page_size: int = 500,
        rag_keygen_strategy: str = "SplitQueryThenGenKeyword",
        rag_searchers: list = None,
    ):
        if rag_searchers is None:
            rag_searchers = ["keyword_search", "front_page_search"]

        self.regulations_file = regulations_file

        # 初始化 Qwen Agent Memory (内建 RAG)
        self.memory = Memory(
            llm=llm,
            files=[regulations_file],
            rag_cfg={
                "max_ref_token": max_ref_token,
                "parser_page_size": parser_page_size,
                "rag_keygen_strategy": rag_keygen_strategy,
                "rag_searchers": rag_searchers,
            },
        )

    def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """
        检索最相关的监管条文

        Args:
            query: 查询文本
            top_k: 返回条数

        Returns:
            相关条文列表，每条包含 document/metadata/distance
        """
        # 通过 Memory 的 retrieval 工具检索
        messages = [{"role": "user", "content": query}]

        try:
            response = list(self.memory.run(messages))
            if response:
                last_msg = response[-1]
                # 提取检索到的内容
                evidence = self._parse_retrieval_response(last_msg, top_k)
                return evidence
        except Exception:
            pass

        return []

    def run(self, query: str):
        """原始 Memory run 接口，返回完整的 Agent 响应流"""
        messages = [{"role": "user", "content": query}]
        return self.memory.run(messages)

    def _parse_retrieval_response(self, messages, top_k: int) -> List[dict]:
        """解析 Memory 返回的检索结果"""
        evidence = []
        seen = set()

        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                if isinstance(content, str) and content not in seen:
                    seen.add(content)
                    evidence.append({
                        "document": content[:300],
                        "metadata": {},
                        "distance": 0.0,
                    })
                elif isinstance(content, list):
                    for item in content:
                        if hasattr(item, "text") and item.text not in seen:
                            seen.add(item.text)
                            evidence.append({
                                "document": item.text[:300],
                                "metadata": {},
                                "distance": 0.0,
                            })

        return evidence[:top_k]
