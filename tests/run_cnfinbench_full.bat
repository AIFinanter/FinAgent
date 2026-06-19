@echo off
REM ═══════════════════════════════════════════════════════════════
REM  CNFinBench × FinAgent 集成测试 — 完整测试脚本
REM ═══════════════════════════════════════════════════════════════
REM
REM  用法（在 finharness_adaptive 目录下运行）:
REM    tests\run_cnfinbench_full.bat
REM
REM  环境要求:
REM    - DEEPSEEK_API_KEY 环境变量已设置
REM    - 已安装依赖: pip install -r requirements.txt
REM ═══════════════════════════════════════════════════════════════

echo.
echo ================================================================
echo   CNFinBench x FinAgent — 完整测试 (全部数据集)
echo ================================================================
echo.

cd /d "%~dp0\.."

python -m tests.test_cnfinbench ^
    --dataset all ^
    --max-rows 50 ^
    --rounds 4 ^
    --model-name finagent_full_test ^
    --judge ^
    %*

echo.
echo 完整测试完成！结果保存在 test_results\cnfinbench\finagent_full_test\
pause
