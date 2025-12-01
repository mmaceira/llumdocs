#!/usr/bin/env bash
set -euo pipefail

BASE="${OLLAMA_API_BASE:-http://ollama:11434}"

echo "Waiting for Ollama at $BASE ..."

for i in {1..60}; do
  if curl -fsS "$BASE/api/tags" >/dev/null 2>&1; then
    echo "Ollama is up."
    exit 0
  fi
  sleep 1
done

echo "Ollama did not come up in time" >&2
exit 1
