#!/bin/sh

# FastAPI runs internally on 8001, completely separate from $PORT
uvicorn app:app --host 0.0.0.0 --port 8001 &

# Wait for FastAPI to be ready
sleep 3

# Streamlit binds to Railway's $PORT (Railway sets this to 8080)
export API_BASE_URL="http://127.0.0.1:8001"
exec streamlit run main.py \
    --server.port "${PORT:-8080}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
