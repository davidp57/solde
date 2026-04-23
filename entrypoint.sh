#!/bin/sh
set -e

echo "=== Running Alembic migrations ==="
python -m alembic upgrade head
echo "=== Migrations complete ==="

echo "=== Starting Uvicorn ==="
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
