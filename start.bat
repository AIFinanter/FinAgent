@echo off
chcp 65001 >nul
title FinGuard + FinHarness Adaptive

:: ═══════════════════════════════════════════════
::  FinGuard + FinHarness Adaptive — 一键启动
::  DIKW 数智流 × Qwen Agent 框架
:: ═══════════════════════════════════════════════

cd /d "%~dp0"

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║  🛡️  FinGuard + FinHarness Adaptive   ║
echo   ║     v2.0 DIKW 数智流                    ║
echo   ╚══════════════════════════════════════════╝
echo.

:: ── 环境检查 ──────────────────────────────────

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ❌ 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   ✅ Python %%v

:: ── 依赖检查 ──────────────────────────────────

echo [2/4] 检查依赖...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo   📦 正在安装依赖...
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo   ❌ 依赖安装失败
        pause
        exit /b 1
    )
)
echo   ✅ 依赖已就绪

:: ── API Key 检查 ──────────────────────────────

echo [3/4] 检查 API Key...
python -c "from finguard.crypto_utils import has_stored_key; exit(0 if has_stored_key() else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   ⚠️  未检测到 DeepSeek API Key
    echo   ─────────────────────────────────
    echo   系统将运行在 Demo 模式下:
    echo   • 脱敏引擎 ✅ 完全可用
    echo   • 行为模型 ✅ 完全可用
    echo   • MAB 引擎 ✅ 完全可用
    echo   • LLM 评分 ⚠️ 需配置 Key
    echo.
    echo   💡 启动后在 Streamlit 侧边栏输入 Key
    echo     或设置环境变量: set DEEPSEEK_API_KEY=sk-xxx
    echo.
) else (
    echo   ✅ API Key 已配置 (加密存储)
)

:: ── 端口检查 ──────────────────────────────────

set API_PORT=8000
set UI_PORT=8501

netstat -ano 2>nul | findstr ":%API_PORT% " >nul
if %errorlevel% equ 0 (
    echo   ⚠️  端口 %API_PORT% 已被占用，尝试终止...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%API_PORT% "') do taskkill //PID %%a //F >nul 2>&1
)

netstat -ano 2>nul | findstr ":%UI_PORT% " >nul
if %errorlevel% equ 0 (
    echo   ⚠️  端口 %UI_PORT% 已被占用，尝试终止...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%UI_PORT% "') do taskkill //PID %%a //F >nul 2>&1
)

:: ── 启动服务 ──────────────────────────────────

echo [4/4] 启动服务...
echo.

:: 启动 API (后台)
start "FinGuard API" /min cmd /c "cd /d %cd% && python -m uvicorn app:app --host 0.0.0.0 --port %API_PORT%"
echo   🚀 API 服务:  http://localhost:%API_PORT%

:: 等待 API 就绪
echo   ⏳ 等待 API 服务就绪...
timeout /t 3 /nobreak >nul

:: 启动 Streamlit
echo   🎨 Streamlit: http://localhost:%UI_PORT%
echo.
echo   ═══════════════════════════════════════════
echo   按 Ctrl+C 停止 | 关闭窗口停止全部服务
echo   ═══════════════════════════════════════════
echo.

:: 打开浏览器
start "" http://localhost:%UI_PORT%

:: 前台运行 Streamlit
streamlit run frontend/streamlit_app.py --server.port %UI_PORT% --server.headless false

:: 清理
taskkill //FI "WINDOWTITLE eq FinGuard API" //F >nul 2>&1
echo.
echo   👋 服务已停止
