# Start FastAPI backend in background on a fixed internal port (8000).
# We MUST override PORT because Uvicorn automatically binds to $PORT if it exists.
PORT=8000 uvicorn app:app --host 0.0.0.0 --port 8000 &

# Wait a moment for FastAPI to be ready
sleep 2

# Start Streamlit frontend — Railway routes external traffic to $PORT
exec streamlit run main.py \
    --server.port "${PORT:-8501}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
