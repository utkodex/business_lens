# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install dos2unix to fix Windows line endings
RUN apt-get update && apt-get install -y --no-install-recommends dos2unix && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Fix Windows CRLF → Unix LF and make executable
RUN dos2unix start.sh && chmod +x start.sh

# Railway injects $PORT at runtime (Streamlit binds to it).
# FastAPI always listens on 8000 internally.
EXPOSE 8000

# Launch both services via the start script
CMD ["./start.sh"]
