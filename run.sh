#!/usr/bin/env bash
# run.sh — Launch TELLIN Crypto Quantitative Terminal Server
set -e

cd "$(dirname "$0")"

PORT=${PORT:-3001}
HOST=${HOST:-0.0.0.0}

echo "================================================================================"
echo "  TELLIN // Institutional Crypto Quantitative, Geopolitical & Analytical Terminal"
echo "================================================================================"
echo "  Live Terminal UI:  http://127.0.0.1:$PORT"
echo "  REST API Docs:     http://127.0.0.1:$PORT/docs"
echo "  Health Endpoint:   http://127.0.0.1:$PORT/api/health"
echo "================================================================================"

python3 -m uvicorn main:app --app-dir backend --host "$HOST" --port "$PORT" --reload
