#!/bin/bash
# Hyper-Orchestrator Runner with real-time streaming
# Usage: ./run.sh "your goal here"

GOAL="${1:-Execute daily job search automation}"
WORKERS="${2:-10}"

echo "🚀 Starting Hyper-Orchestrator with real-time streaming..."
echo "Goal: $GOAL"
echo "Workers: $WORKERS"
echo ""

# Run with unbuffered Python (-u) for real-time output
python3 -u scripts/hyper-cli.py \
    --goal "$GOAL" \
    --max-workers "$WORKERS" \
    2>&1

echo ""
echo "✅ Hyper-Orchestrator finished"