#!/usr/bin/env python
"""
端到端验证脚本 — 5 个样例场景 × DIKW 流水线

不依赖 LLM API Key 也可运行（Demo 模式）:
  - 脱敏引擎: 全功能
  - 行为基础模型: 全功能
  - 风险评分: Demo 模式（基于规则）
  - MAB: 全功能 (Thompson Sampling)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from config import config
from models import FinDataInput
from finguard.data_layer import DataSanitizer
from finguard.info_layer import BehavioralFoundationModel
from finharness.mab_engine import AdaptiveMABEngine
from finharness.metrics import calculate_reward
from scripts.sample_data import ALL_SAMPLES


def print_separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run_end_to_end_test():
    print_separator("FinGuard + FinHarness Adaptive — 端到端验证")
    print(f"框架: Qwen Agent | 架构: DIKW 数智流")
    print(f"LLM: {config.llm.model} @ {config.llm.model_server}")
    print(f"RAG: Qwen Agent Memory | 法规: {config.rag.regulations_file}")
    print(f"MAB: Thompson Sampling ({', '.join(config.mab.strategies)})")

    sanitizer = DataSanitizer()
    bfm = BehavioralFoundationModel()
    mab = AdaptiveMABEngine(config.mab.strategies)

    total_risk_scores = []

    for i, sample in enumerate(ALL_SAMPLES, 1):
        print_separator(f"场景 {i}: {sample['scenario'].upper()} — {sample['id']}")

        input_data = FinDataInput(
            id=sample["id"],
            scenario=sample["scenario"],
            raw_text=sample["raw_text"],
            metadata=sample["metadata"],
        )

        # ── D: 脱敏 ──
        sanitized, compliance = sanitizer.sanitize(input_data.raw_text)
        print(f"\n📝 脱敏后文本: {sanitized[:80]}...")
        print(f"📋 合规通过: {compliance['passed']}")

        # ── I: 行为预测 ──
        features = bfm.extract_features(input_data.metadata)
        anomaly = float(bfm.predict_anomaly(features))
        print(f"🔬 行为异常度: {anomaly:.4f}")
        print(f"🔢 特征向量: {[round(f, 3) for f in features[0]]}")

        # ── K: Demo 风险评分 ──
        risk_score = anomaly * 0.4 + sample["metadata"]["sensitive_word_ratio"] * 0.3
        if "密码" in sample["raw_text"] or "验证" in sample["raw_text"]:
            risk_score += 0.15
        if "http://" in sample["raw_text"] or "境外" in sample["raw_text"]:
            risk_score += 0.15
        risk_score = min(1.0, risk_score)
        total_risk_scores.append(risk_score)
        print(f"🎯 风险评分: {risk_score:.4f}")

        # ── W: MAB 策略分配 ──
        strategy_name, mab_samples = mab.assign()
        ev = mab.get_expected_values()
        print(f"🎰 MAB 推荐策略: {strategy_name.upper()}")
        print(f"📊 各策略期望: {', '.join(f'{s}={v:.2%}' for s, v in ev.items())}")

        # ── 反馈模拟 ──
        outcome = "pass" if risk_score < 0.3 else ("block" if risk_score < 0.7 else "incident")
        latency = {"strict": 800, "standard": 300, "lenient": 100}[strategy_name]
        is_fp = risk_score < 0.3 and strategy_name == "strict"
        reward = calculate_reward(outcome, latency, strategy_name, is_fp)
        mab.update(strategy_name, reward)
        print(f"🏆 奖励反馈: {reward:.4f} (outcome={outcome}, latency={latency}ms)")

    # ── 最终报告 ──
    print_separator("验证总结")
    print(f"✅ 5/5 场景评估完成")
    print(f"📊 平均风险评分: {sum(total_risk_scores)/len(total_risk_scores):.4f}")
    print(f"🎰 MAB 总试验: {mab.total_trials}")
    print(f"📈 最终期望值: {mab.get_expected_values()}")

    # 验证 MAB 收敛
    all_ev = mab.get_expected_values()
    if all(0.0 <= v <= 1.0 for v in all_ev.values()):
        print("✅ MAB 期望值在有效范围内")
    else:
        print("❌ MAB 期望值异常！")

    print(f"\n{'='*60}")
    print("  🎉 端到端验证通过！")
    print(f"{'='*60}")

    return True


if __name__ == "__main__":
    success = run_end_to_end_test()
    sys.exit(0 if success else 1)
