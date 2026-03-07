#!/bin/bash
# Script to run migrations and start the application

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
