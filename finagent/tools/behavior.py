"""
Behavior Analyzer Tool — 行为异常检测

基于 IsolationForest 的轻量级异常检测，7 维特征向量。
设计理念：小参数模型、<1ms 推理、只做预判不做最终决策。

参考: Qwen Agent Tool 的 JSON Schema 参数定义
"""

import numpy as np
from typing import Union
from datetime import datetime

from sklearn.ensemble import IsolationForest
from qwen_agent.tools.base import BaseTool, register_tool


# ── 全局模型实例（轻量级，可共享） ──────────────

_model = IsolationForest(
    contamination=0.1,
    random_state=42,
    n_estimators=50,
)

_trained = False


def _ensure_fitted():
    """确保模型已初始化（Demo 模式用随机数据初始化）"""
    global _trained
    if not _trained:
        dummy = np.random.randn(200, 7) * 0.5
        _model.fit(dummy)
        _trained = True


# ── 特征提取 ──────────────────────────────────

FEATURE_NAMES = [
    "time_anomaly",
    "geo_distance",
    "action_frequency",
    "amount_deviation",
    "sensitive_word_ratio",
    "device_repeat",
    "history_failures",
]


def extract_features(meta: dict) -> np.ndarray:
    """从元数据中提取 7 维归一化特征向量"""
    features = np.zeros(7)

    hour = meta.get("timestamp", datetime.now()).hour
    features[0] = 1.0 if 2 <= hour <= 5 else 0.0

    features[1] = min(float(meta.get("geo_distance_km", 0)) / 10000, 1.0)
    features[2] = min(float(meta.get("action_freq_per_min", 0)) / 30, 1.0)
    features[3] = min(float(meta.get("amount_deviation", 0)) / 100, 1.0)
    features[4] = float(meta.get("sensitive_word_ratio", 0))
    features[5] = float(meta.get("device_fingerprint_repeat", 0))
    features[6] = min(float(meta.get("history_failures", 0)) / 10, 1.0)

    return features.reshape(1, -1)


# ── 工具注册 ──────────────────────────────────

@register_tool("behavior_analyzer")
class BehaviorAnalyzerTool(BaseTool):
    """行为异常检测工具 — 基于 IsolationForest 轻量级异常评分"""

    description = (
        "对金融操作元数据进行行为异常检测，输出 0-1 范围的异常评分。"
        "检测维度: 时间异常(凌晨2-5点)、地理跳变(km)、操作频率(次/分)、"
        "金额偏离度、敏感词占比、设备指纹重复度、历史失败次数。"
        "评分 > 0.5 表示存在显著行为异常。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "meta": {
                "description": (
                    "金融操作元数据 JSON 对象，包含以下可选字段: "
                    "timestamp(ISO时间)、geo_distance_km(地理跳变距离)、"
                    "action_freq_per_min(操作频率)、amount_deviation(金额偏离度)、"
                    "sensitive_word_ratio(敏感词占比0-1)、"
                    "device_fingerprint_repeat(设备重复度0-1)、"
                    "history_failures(历史失败次数)"
                ),
                "type": "object",
            },
        },
        "required": ["meta"],
    }

    def call(self, params: Union[str, dict], **kwargs) -> dict:
        params = self._verify_json_format_args(params)
        meta = params.get("meta", {})

        _ensure_fitted()
        features = extract_features(meta)
        raw = _model.decision_function(features)[0]
        anomaly_score = max(0.0, min(1.0, 0.5 - raw))

        return {
            "anomaly_score": round(anomaly_score, 4),
            "is_anomalous": anomaly_score > 0.5,
            "features": {
                name: round(float(features[0][i]), 4)
                for i, name in enumerate(FEATURE_NAMES)
            },
        }
