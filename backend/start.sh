#!/bin/bash
# Development startup script
echo "Starting ShotSaaS Backend..."
echo "Make sure PostgreSQL and Redis are running."

# Create database if not exists
createdb shotsaas 2>/dev/null || echo "Database already exists"

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
