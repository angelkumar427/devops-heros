#!/usr/bin/env bash
# Generate sustained traffic so request-rate / latency panels and the HPA have something to show.
#   API=http://stockpilot.local DURATION=300 ./scripts/load-test.sh
set -euo pipefail
API="${API:-http://localhost:8000}"; DURATION="${DURATION:-120}"; CONCURRENCY="${CONCURRENCY:-8}"
echo "Load on $API for ${DURATION}s with $CONCURRENCY workers"
worker() {
  local end=$((SECONDS + DURATION))
  while [ $SECONDS -lt $end ]; do
    curl -s -o /dev/null "$API/api/products"
    curl -s -o /dev/null "$API/api/stats"
    curl -s -o /dev/null "$API/api/products?low_stock=true"
    curl -s -o /dev/null "$API/api/movements?limit=20"
  done
}
for _ in $(seq "$CONCURRENCY"); do worker & done
wait
echo "done"
