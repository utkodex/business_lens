# ── Business Lens AI — Render-ready Dockerfile ──────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install dos2unix to fix Windows line endings in shell scripts
RUN apt-get update && apt-get install -y --no-install-recommends dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code + data files
COPY . .

# Fix Windows CRLF → Unix LF and make executable
RUN dos2unix start.sh && chmod +x start.sh

# Render injects $PORT at runtime (default 10000).
# Streamlit binds to $PORT; FastAPI runs internally on 8001.
EXPOSE ${PORT:-10000}

# Launch: rebuild DB → start FastAPI → start Streamlit
CMD ["./start.sh"]
