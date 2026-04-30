#!/bin/sh

# Save Railway's public port before we override anything
PUBLIC_PORT="${PORT:-8080}"

# FastAPI always runs internally on 8001
FASTAPI_PORT=8001
PORT=$FASTAPI_PORT uvicorn app:app --host 0.0.0.0 --port $FASTAPI_PORT &

# Wait for FastAPI to be ready
sleep 2

# Streamlit binds to Railway's public $PORT
exec streamlit run main.py \
    --server.port "$PUBLIC_PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
