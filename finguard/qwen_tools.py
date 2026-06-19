"""
DIKW 自定义 Qwen Agent 工具

将脱敏引擎和行为基础模型封装为 Qwen Agent Tool，
使其可以在 Agent 工作流中被自动调用。
"""

from typing import Dict, Union

from qwen_agent.tools.base import BaseTool, register_tool

from finguard.data_layer import DataSanitizer
from finguard.info_layer import BehavioralFoundationModel


# 全局单例
_sanitizer = DataSanitizer()
_behavior_model = BehavioralFoundationModel()


@register_tool("data_sanitizer")
class DataSanitizerTool(BaseTool):
    """金融数据脱敏工具 — 自动检测并脱敏个人身份信息"""

    description = "对金融文本进行脱敏处理，自动检测并替换姓名、身份证号、银行卡号、手机号、IP地址、邮箱等敏感信息"
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
        sanitized, report = _sanitizer.sanitize(text)
        return {
            "sanitized_text": sanitized,
            "compliance_report": report,
        }


@register_tool("behavior_anomaly")
class BehaviorAnomalyTool(BaseTool):
    """行为异常检测工具 — 基于 IsolationForest 轻量级异常评分"""

    description = "对金融操作元数据进行行为异常检测，输出 0-1 范围的异常评分"
    parameters = {
        "type": "object",
        "properties": {
            "meta": {
                "description": "金融操作元数据 JSON，包含 timestamp/geo_distance_km/action_freq_per_min/amount_deviation/sensitive_word_ratio/device_fingerprint_repeat/history_failures 字段",
                "type": "object",
            },
        },
        "required": ["meta"],
    }

    def call(self, params: Union[str, dict], **kwargs) -> dict:
        params = self._verify_json_format_args(params)
        meta = params.get("meta", {})
        features = _behavior_model.extract_features(meta)
        anomaly_score = float(_behavior_model.predict_anomaly(features))
        return {
            "anomaly_score": anomaly_score,
            "is_anomalous": anomaly_score > 0.5,
            "feature_values": features.tolist()[0],
        }
