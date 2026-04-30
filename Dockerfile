# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the start script executable
RUN chmod +x start.sh

# Railway injects $PORT at runtime (Streamlit binds to it).
# FastAPI always listens on 8000 internally.
EXPOSE 8000

# Launch both services via the start script
CMD ["./start.sh"]
