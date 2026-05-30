#!/bin/bash
set -e

echo "============================================"
echo "  BrandPulse API -- Starting up..."
echo "============================================"

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database (if empty)..."
python seed.py

echo "Starting BrandPulse API server..."
exec gunicorn run:app \
    --worker-class eventlet \
    --workers 1 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
