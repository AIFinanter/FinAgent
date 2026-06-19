"""Tests for Information Layer — 行为基础模型"""

import numpy as np
import pytest
from datetime import datetime
from finguard.info_layer import BehavioralFoundationModel


@pytest.fixture
def bfm():
    return BehavioralFoundationModel()


def test_feature_dimension(bfm):
    """验证特征向量维度正确"""
    features = bfm.extract_features({})
    assert features.shape == (1, 7)


def test_night_hour_feature(bfm):
    """凌晨2-5点应标记为异常"""
    night_data = {"timestamp": datetime(2025, 1, 1, 3, 0, 0)}
    features = bfm.extract_features(night_data)
    assert features[0, 0] == 1.0


def test_day_hour_feature(bfm):
    """白天应标记为正常"""
    day_data = {"timestamp": datetime(2025, 1, 1, 14, 0, 0)}
    features = bfm.extract_features(day_data)
    assert features[0, 0] == 0.0


def test_anomaly_score_range(bfm):
    """异常评分应在 0.0-1.0 范围内"""
    features = bfm.extract_features({})
    score = bfm.predict_anomaly(features)
    assert 0.0 <= score <= 1.0


def test_multiple_predictions_stable(bfm):
    """多次预测应保持稳定 (相同输入 → 相同输出)"""
    data = {
        "timestamp": datetime(2025, 1, 1, 3, 0, 0),
        "geo_distance_km": 5000,
        "action_freq_per_min": 20,
        "amount_deviation": 50,
        "sensitive_word_ratio": 0.3,
        "device_fingerprint_repeat": 0.5,
        "history_failures": 3,
    }
    features = bfm.extract_features(data)
    scores = [bfm.predict_anomaly(features) for _ in range(10)]
    assert all(a == b for a, b in zip(scores, scores[1:]))


def test_feature_clipping(bfm):
    """特征值应被正确截断到 [0, 1] 范围"""
    extreme_data = {
        "geo_distance_km": 99999,
        "action_freq_per_min": 999,
        "amount_deviation": 999,
        "history_failures": 999,
    }
    features = bfm.extract_features(extreme_data)
    assert all(0.0 <= f <= 1.0 for f in features[0])
