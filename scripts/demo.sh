#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env

docker compose up -d --build

echo "Ожидание web-master..."
for i in $(seq 1 30); do
  curl -fs localhost:8080/health >/dev/null && break
  sleep 2
done

echo "== Состояние системы =="
curl -s localhost:8080/status; echo

echo "== Collector: батч (напрямую, через docker compose exec) =="
docker compose exec -T collector python -c \
  "import urllib.request;print(urllib.request.urlopen('http://localhost:8000/batch?size=3').read().decode())"