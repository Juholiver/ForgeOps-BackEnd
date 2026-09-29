#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "waiting for postgres at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
  until python -c "import os,socket; socket.create_connection((os.environ.get('POSTGRES_HOST','postgres'), int(os.environ.get('POSTGRES_PORT','5432'))), timeout=2).close()" 2>/dev/null; do
    sleep 2
  done
  echo "running database migrations..."
  alembic upgrade head
fi

exec "$@"
