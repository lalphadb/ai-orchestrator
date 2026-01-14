#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Checking env file presence..."
test -f backend/.env || { echo "backend/.env missing"; exit 1; }

echo "[2/4] Checking sandbox posture..."
grep -q "^EXECUTE_MODE=sandbox" backend/.env || { echo "EXECUTE_MODE not sandbox"; exit 1; }
if grep -q "^ALLOW_DIRECT_FALLBACK=" backend/.env; then
  grep -q "^ALLOW_DIRECT_FALLBACK=false" backend/.env || { echo "ALLOW_DIRECT_FALLBACK must be false in prod"; exit 1; }
fi

echo "[3/4] Checking Docker availability..."
docker info >/dev/null 2>&1 || { echo "Docker not available"; exit 1; }

echo "[4/4] Running minimal sandbox test..."
docker run --rm --network=none alpine:latest echo "OK" >/dev/null

echo "SECURITY POSTURE: OK"
