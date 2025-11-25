#!/usr/bin/env bash
set -e

# Ensure DB & tables exist on first run
python -m src.db_init

# Start uvicorn. Render provides $PORT env var.
# Use --workers 1 to avoid multiple processes touching sqlite file.
exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
