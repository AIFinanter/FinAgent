"""
Data Sanitizer Tool — 金融文本脱敏

Qwen Agent 工具模式: @register_tool 装饰器自动注册，
Agent 根据 description 和 parameters 自主决定何时调用。

参考: Qwen Agent BaseTool + CrewAI 工具自描述模式
"""

import re
from typing import Union

from qwen_agent.tools.base import BaseTool, register_tool


# ── 脱敏规则库 ──────────────────────────────────
# 顺序敏感：长模式优先，避免银行卡被身份证误匹配

SANITIZE_RULES = [
    ("person_name",  r'(?<=姓名[：:])[一-鿿]{2,4}',       "[PERSON]"),
    ("bank_card",    r'62\d{14,17}',                       "[CARD_NUM]"),
    ("id_number",    r'\d{15}(?:\d{2}[\dXx])?',           "[ID_NUM]"),
    ("phone",        r'1[3-9]\d{9}',                       "[PHONE]"),
    ("ip_addr",      r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', "[IP_ADDR]"),
    ("email",        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "[EMAIL]"),
]


@register_tool("data_sanitizer")
class DataSanitizerTool(BaseTool):
    """金融数据脱敏工具 — 自动检测并脱敏个人身份信息"""

    description = (
        "对金融文本进行脱敏处理，自动检测并替换以下敏感信息："
        "姓名、身份证号(18位)、银行卡号(银联62开头)、手机号、IP地址、电子邮箱。"
        "使用此工具处理任何包含用户PII的原始文本后再进行后续分析。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "description": "需要进行脱敏处理的原始金融文本",
                "type": "string",
            },
        },
        "required": ["text"],
    }

    def call(self, params: Union[str, dict], **kwargs) -> dict:
        params = self._verify_json_format_args(params)
        text = params.get("text", "")

        sanitized = text
        report = {"masked": [], "clean": []}

        for field_name, pattern, replacement in SANITIZE_RULES:
            matches = re.findall(pattern, text)
            if matches:
                sanitized = re.sub(pattern, replacement, sanitized)
                report["masked"].append(f"{field_name}({len(matches)}处)")
            else:
                report["clean"].append(field_name)

        return {
            "sanitized_text": sanitized,
            "report": report,
            "masked_count": len(report["masked"]),
        }
