# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend + serve frontend ─────────────────────────────────
# Python 3.12 — pinned to match CI + Ubuntu 24 LTS default. Bumping the
# pinned version is a deliberate change: bump CI, Dockerfile, and docs in
# the same PR so dev / CI / prod never drift.
FROM python:3.12-slim
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ libsndfile1 portaudio19-dev ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy built frontend into static directory
COPY --from=frontend-build /frontend/dist /app/frontend/dist

# Create necessary directories
RUN mkdir -p outputs/reports outputs/email_drafts data/documents chroma_db

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
