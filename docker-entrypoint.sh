#!/bin/bash

# Run database migrations (may fail if already applied, that's ok)
echo "Running database migrations..."
if flask db upgrade; then
    echo "Migrations completed successfully"
else
    echo "Migration skipped (may be already applied)"
fi

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 120 wsgi:app
