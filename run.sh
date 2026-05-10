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

echo "=============================================="
echo "  🛡️  Sentinel — Behavioral Health Risk Monitor"
echo "=============================================="
echo ""

# Make sure we tear down the backend if anything below fails or the user
# hits Ctrl+C while Streamlit is in the foreground.
cleanup() {
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo ""
        echo "Shutting down backend (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# Check if synthetic data exists; generate if not
if [ ! -f "$PROJECT_DIR/data/synthetic_training_data.csv" ]; then
    echo "📊 Generating synthetic training data..."
    cd "$PROJECT_DIR"
    python data/generate_synthetic_data.py
    echo ""
fi

# Start FastAPI backend in background
echo "🚀 Starting FastAPI backend on port 8000..."
cd "$PROJECT_DIR/backend"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to initialize (model loading + DB setup)
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs above."
    exit 1
fi

echo "✅ Backend running (PID: $BACKEND_PID)"

# Start Streamlit frontend.
#   --server.headless true
#       Skips the first-run interactive email prompt that otherwise blocks
#       on stdin and prevents the dashboard from ever serving.
#   --browser.gatherUsageStats false
#       Suppresses the usage-stats opt-in (also part of the first-run flow).
echo "🎨 Starting Streamlit dashboard on port 8501..."
echo "   Open http://localhost:8501 in your browser once it boots."
cd "$PROJECT_DIR/frontend"
streamlit run dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false

# Cleanup runs via the trap defined above.
echo "Done."
