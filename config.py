"""
FinAgent — 配置中心

Qwen Agent 框架 + DeepSeek LLM + Thompson Sampling MAB
安全存储: Fernet 加密 (cryptography)
"""

import os
from dataclasses import dataclass, field


def _resolve_api_key() -> str:
    """按优先级解析 API Key:
    1. 环境变量 DEEPSEEK_API_KEY (最高优先级)
    2. Fernet 加密存储 (持久化)
    3. 空字符串 (Demo 模式)
    """
    env_key = os.getenv("DEEPSEEK_API_KEY", "")
    if env_key:
        return env_key

    try:
        from finguard.crypto_utils import decrypt_api_key
        stored_key = decrypt_api_key()
        if stored_key:
            return stored_key
    except Exception:
        pass

    return ""


@dataclass
class LLMConfig:
    """LLM 配置 — 通过 Qwen Agent OAI backend 接入 DeepSeek"""
    model: str = "deepseek-v4-pro"
    model_server: str = "https://api.deepseek.com"
    model_type: str = "oai"
    max_tokens: int = 2048
    temperature: float = 0.1

    def __post_init__(self):
        self._api_key: str | None = None

    @property
    def api_key(self) -> str:
        if self._api_key is None:
            self._api_key = _resolve_api_key()
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        self._api_key = value

    def to_qwen_llm_cfg(self) -> dict:
        return {
            "model": self.model,
            "model_server": self.model_server,
            "api_key": self.api_key,
            "model_type": self.model_type,
            "generate_cfg": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }


@dataclass
class MABConfig:
    """MAB 自适应决策配置"""
    arms: tuple = ("strict", "standard", "lenient")
    initial_alpha: float = 1.0
    initial_beta: float = 1.0


@dataclass
class RAGConfig:
    """RAG 合规知识库配置"""
    regulations_file: str = "./knowledge_base/regulations/regulations.txt"
    regulations_json: str = "./knowledge_base/regulations/finance_regulations.json"
    max_ref_token: int = 4000
    parser_page_size: int = 500
    rag_keygen_strategy: str = "SplitQueryThenGenKeyword"
    rag_searchers: list = field(default_factory=lambda: ["keyword_search", "front_page_search"])


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    mab: MABConfig = field(default_factory=MABConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    cache_dir: str = "./cache/llm_cache"


config = AppConfig()
