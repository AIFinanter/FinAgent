#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  CNFinBench × FinAgent 集成测试 — 快速测试脚本 (Linux/Mac)
# ═══════════════════════════════════════════════════════════════

echo ""
echo "================================================================"
echo "  CNFinBench x FinAgent — 快速测试 (MT_Inter, 前3条, 简化模式)"
echo "================================================================"
echo ""

cd "$(dirname "$0")/.."

python -m tests.test_cnfinbench \
    --dataset MT_Inter \
    --max-rows 3 \
    --rounds 4 \
    --simple \
    --model-name finagent_quick_test \
    "$@"

echo ""
echo "测试完成！结果保存在 test_results/cnfinbench/finagent_quick_test/"
