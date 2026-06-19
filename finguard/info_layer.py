"""
Information Layer — 行为基础模型

DIKW 层级: Information (脱敏数据 → 异常预测)

设计理念:
- 用 IsolationForest 替代全量神经网络, 推理 <1ms
- 只做异常预判, 不做最终决策
- 特征维度控制在 10 以内, 避免过拟合
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime


class BehavioralFoundationModel:
    """
    小参数行为基础模型: 轻量级异常检测

    7 维特征:
    0: 时间异常度 (凌晨2-5点=1, 其他=0)
    1: 地理位置跳变距离 (km, 归一化)
    2: 操作频率 (次/分钟)
    3: 金额偏离度 (|当前-均值|/标准差)
    4: 关键词敏感度 (敏感词数/总词数)
    5: 设备指纹重复度
    6: 历史失败次数
    """

    FEATURE_DIM = 7

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,     # 预期 10% 异常率
            random_state=42,
            n_estimators=50        # 轻量: 仅 50 棵树
        )
        self._fitted = False

    def extract_features(self, data: dict) -> np.ndarray:
        """从元数据中提取 7 维特征向量"""
        features = np.zeros(self.FEATURE_DIM)

        hour = data.get("timestamp", datetime.now()).hour
        features[0] = 1.0 if 2 <= hour <= 5 else 0.0

        features[1] = min(data.get("geo_distance_km", 0) / 10000, 1.0)
        features[2] = min(data.get("action_freq_per_min", 0) / 30, 1.0)
        features[3] = min(data.get("amount_deviation", 0) / 100, 1.0)
        features[4] = data.get("sensitive_word_ratio", 0)
        features[5] = data.get("device_fingerprint_repeat", 0)
        features[6] = min(data.get("history_failures", 0) / 10, 1.0)

        return features.reshape(1, -1)

    def predict_anomaly(self, features: np.ndarray) -> float:
        """
        返回异常评分 0.0(正常) ~ 1.0(异常)
        IsolationForest 返回 -1(异常) 或 1(正常)
        """
        if not self._fitted:
            # Demo 模式: 用随机数据初始化
            dummy = np.random.randn(100, self.FEATURE_DIM) * 0.5
            self.model.fit(dummy)
            self._fitted = True

        raw = self.model.decision_function(features)[0]
        # 决策函数值域映射到 0-1
        return max(0.0, min(1.0, (0.5 - raw)))
