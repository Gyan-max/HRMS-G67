#!/bin/bash
# ===========================================================================
# run.sh — Launch the Behavioral Health Risk Monitor
# ===========================================================================
# Starts both the FastAPI backend and Streamlit frontend.
# Usage: bash run.sh
# ===========================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================="
echo "  🧠 Behavioral Health Risk Monitor"
echo "=============================================="
echo ""

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

# Wait for backend to initialize
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs above."
    exit 1
fi

echo "✅ Backend running (PID: $BACKEND_PID)"

# Start Streamlit frontend
echo "🎨 Starting Streamlit dashboard on port 8501..."
cd "$PROJECT_DIR/frontend"
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

# Cleanup: kill backend when Streamlit exits
echo "Shutting down backend..."
kill $BACKEND_PID 2>/dev/null
echo "Done."
