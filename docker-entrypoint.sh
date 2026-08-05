#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Extract connection params from DATABASE_URL (strip +asyncpg suffix for asyncpg)
ASYNC_URL="${DATABASE_URL/postgresql+asyncpg/postgresql}"
for i in $(seq 1 30); do
    python -c "
import asyncio, asyncpg
asyncio.run(asyncpg.connect('${ASYNC_URL}', timeout=2))
" 2>/dev/null && echo "Database is ready!" && break
    echo "  Attempt $i: database not ready, retrying in 1s..."
    sleep 1
done

echo "Running alembic migrations..."
alembic upgrade head

echo "Starting GeoContext API..."
# Allow docker-compose CMD to override default uvicorn options
if [ $# -gt 0 ]; then
    exec "$@"
else
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
fi
