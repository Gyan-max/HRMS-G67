#!/bin/bash
# ===========================================================================
# run.sh — Launch the Behavioral Health Risk Monitor (Sentinel)
# ===========================================================================
# Starts both the FastAPI backend (port 8000) and the Streamlit frontend
# (port 8501). Streamlit is launched in headless mode so it doesn't block
# on the interactive email/telemetry prompt the very first time it runs.
#
# Usage: bash run.sh
#
# Once both processes are running, open http://localhost:8501 in a browser.
# Press Ctrl+C to stop everything cleanly.
# ===========================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

echo "=============================================="
echo "  🛡️  Sentinel — Behavioral Health Risk Monitor"
echo "=============================================="
echo ""

# Cleanup background processes on exit
cleanup() {
    echo ""
    [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "${VITE_PID:-}" ] && kill "$VITE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Generate data if missing
if [ ! -f "$PROJECT_DIR/data/synthetic_training_data.csv" ]; then
    echo "📊 Generating synthetic training data..."
    python "$PROJECT_DIR/data/generate_synthetic_data.py"
fi

# 1. Start Backend
echo "🚀 Starting FastAPI backend (port 8000)..."
cd "$PROJECT_DIR/backend"
uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!

# 2. Start Vite
echo "🎨 Starting Vite frontend (port 5173)..."
cd "$PROJECT_DIR/frontend-web"
npm run dev -- --host 0.0.0.0 --port 5173 > /dev/null 2>&1 &
VITE_PID=$!

echo "⏳ Initializing services..."
sleep 5

# 3. Start Streamlit (Foreground)
echo "📊 Starting Streamlit Dashboard (port 8501)..."
echo "   - React UI: http://localhost:5173"
echo "   - Dashboard: http://localhost:8501"
echo ""
cd "$PROJECT_DIR/frontend"
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false

