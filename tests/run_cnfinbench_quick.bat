@echo off
REM ═══════════════════════════════════════════════════════════════
REM  CNFinBench × FinAgent 集成测试 — 快速测试脚本
REM ═══════════════════════════════════════════════════════════════
REM
REM  用法（在 finharness_adaptive 目录下运行）:
REM    tests\run_cnfinbench_quick.bat
REM
REM  环境要求:
REM    - DEEPSEEK_API_KEY 环境变量已设置
REM    - 已安装依赖: pip install -r requirements.txt
REM ═══════════════════════════════════════════════════════════════

echo.
echo ================================================================
echo   CNFinBench x FinAgent — 快速测试 (MT_Inter, 前3条, 简化模式)
echo ================================================================
echo.

cd /d "%~dp0\.."

python -m tests.test_cnfinbench ^
    --dataset MT_Inter ^
    --max-rows 3 ^
    --rounds 4 ^
    --simple ^
    --model-name finagent_quick_test ^
    %*

echo.
echo 测试完成！结果保存在 test_results\cnfinbench\finagent_quick_test\
pause
