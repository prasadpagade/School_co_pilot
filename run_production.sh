#!/bin/bash
# Production startup script

set -e

echo "🚀 Starting Denali School Copilot in production mode..."

# Check for required environment variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY not set"
    exit 1
fi

if [ -z "$FILE_SEARCH_STORE_NAME" ]; then
    echo "❌ Error: FILE_SEARCH_STORE_NAME not set"
    exit 1
fi

# Set production environment
export ENVIRONMENT=production
export PYTHONUNBUFFERED=1

# Determine worker count (default: 2, or from env)
WORKERS=${WORKERS:-2}

echo "✅ Environment configured"
echo "📊 Workers: $WORKERS"
echo "🌐 Starting server on port ${PORT:-8000}..."

# Start uvicorn with production settings
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers $WORKERS \
    --log-level info \
    --access-log \
    --no-use-colors

