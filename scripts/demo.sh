#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env

docker compose up -d --build

echo "== Collector: батч (напрямую, через docker compose exec) =="
docker compose exec -T collector python -c \
  "import urllib.request;print(urllib.request.urlopen('http://localhost:8000/batch?size=3').read().decode())"