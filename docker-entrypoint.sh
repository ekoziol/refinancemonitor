#!/bin/bash

# Skip database migrations - schema is already correct
# Migration was failing due to column already existing
# TODO: Re-enable when alembic_version table is synced
echo "Skipping database migrations (schema is already up to date)"

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 120 wsgi:app
