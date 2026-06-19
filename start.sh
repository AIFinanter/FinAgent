#!/usr/bin/env bash
# ═══════════════════════════════════════════════
#  FinGuard + FinHarness Adaptive — 一键启动
#  DIKW 数智流 × Qwen Agent 框架
# ═══════════════════════════════════════════════

set -e
cd "$(dirname "$0")"

API_PORT=8000
UI_PORT=8501

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  🛡️  FinGuard + FinHarness Adaptive   ║"
echo "  ║     v2.0 DIKW 数智流                    ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ── 环境检查 ──────────────────────────────────

echo "[1/4] 检查 Python 环境..."
if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null; then
    echo "  ❌ 未找到 Python，请先安装 Python 3.10+"
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo "  ✅ $($PYTHON --version)"

# ── 依赖检查 ──────────────────────────────────

echo "[2/4] 检查依赖..."
if ! $PYTHON -c "import fastapi" &>/dev/null; then
    echo "  📦 正在安装依赖..."
    $PYTHON -m pip install -r requirements.txt -q
fi
echo "  ✅ 依赖已就绪"

# ── API Key 检查 ──────────────────────────────

echo "[3/4] 检查 API Key..."
if ! $PYTHON -c "from finguard.crypto_utils import has_stored_key; exit(0 if has_stored_key() else 1)" &>/dev/null; then
    echo ""
    echo "  ⚠️  未检测到 DeepSeek API Key"
    echo "  ─────────────────────────────────"
    echo "  系统将运行在 Demo 模式下:"
    echo "  • 脱敏引擎 ✅ 完全可用"
    echo "  • 行为模型 ✅ 完全可用"
    echo "  • MAB 引擎 ✅ 完全可用"
    echo "  • LLM 评分 ⚠️ 需配置 Key"
    echo ""
    echo "  💡 启动后在 Streamlit 侧边栏输入 Key"
    echo "    或: export DEEPSEEK_API_KEY=sk-xxx"
    echo ""
else
    echo "  ✅ API Key 已配置 (加密存储)"
fi

# ── 端口清理 ──────────────────────────────────

cleanup_port() {
    local port=$1
    if command -v lsof &>/dev/null; then
        local pid=$(lsof -ti :$port 2>/dev/null)
        [ -n "$pid" ] && kill "$pid" 2>/dev/null
    elif command -v ss &>/dev/null; then
        local pid=$(ss -ltnp "sport = :$port" 2>/dev/null | grep -oP 'pid=\K\d+')
        [ -n "$pid" ] && kill "$pid" 2>/dev/null
    fi
}

cleanup_port $API_PORT
cleanup_port $UI_PORT

# ── 启动服务 ──────────────────────────────────

echo "[4/4] 启动服务..."
echo ""

# 后台启动 API
$PYTHON -m uvicorn app:app --host 0.0.0.0 --port $API_PORT &
API_PID=$!
echo "  🚀 API 服务:  http://localhost:$API_PORT  (PID: $API_PID)"

sleep 2

# 打开浏览器
if command -v open &>/dev/null; then
    open "http://localhost:$UI_PORT" &
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$UI_PORT" &
fi

echo "  🎨 Streamlit: http://localhost:$UI_PORT"
echo ""
echo "  ═══════════════════════════════════════════"
echo "  按 Ctrl+C 停止全部服务"
echo "  ═══════════════════════════════════════════"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "  👋 正在停止服务..."
    kill $API_PID 2>/dev/null
    wait $API_PID 2>/dev/null
    echo "  ✅ 已停止"
}

trap cleanup EXIT INT TERM

# 前台运行 Streamlit
$PYTHON -m streamlit run frontend/streamlit_app.py --server.port $UI_PORT
