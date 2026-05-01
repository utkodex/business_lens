#!/bin/sh

# ── Step 1: Rebuild DuckDB from CSV data ────────────────────────────────────
# The .duckdb file is gitignored, so we rebuild it every time the container
# starts.  This takes ~5-10 seconds and guarantees a fresh database.
echo "[start.sh] Building DuckDB database from CSV data..."
python build_db.py
echo "[start.sh] Database ready."

# ── Step 2: Start FastAPI backend (internal, not exposed to the internet) ───
# Runs on port 8001 inside the container; only Streamlit talks to it.
uvicorn app:app --host 0.0.0.0 --port 8001 &

# Give FastAPI a moment to bind
sleep 3

# ── Step 3: Start Streamlit frontend (exposed to the internet) ──────────────
# Render injects $PORT at runtime.  Streamlit binds to it so Render's
# reverse proxy can route traffic to the container.
export API_BASE_URL="http://127.0.0.1:8001"
exec streamlit run main.py \
    --server.port "${PORT:-8080}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
