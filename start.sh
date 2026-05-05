#!/usr/bin/env bash
# NexusAgent — Production Linux startup script
# Usage: bash start.sh [--build]   pass --build to rebuild frontend first
set -euo pipefail

NEXUS_DIR="$(cd "$(dirname "$0")" && pwd)"
LAB_DIR="${LAB_DIR:-$NEXUS_DIR/../nexuscaller-lab}"
FRONT_DIR="$NEXUS_DIR/frontend"
LAND_DIR="$NEXUS_DIR/landing"
WA_DIR="$NEXUS_DIR/whatsapp_bridge"
LOG_DIR="$NEXUS_DIR/logs"

mkdir -p "$LOG_DIR"

# ── helpers ──────────────────────────────────────────────────────────────────
kill_port() {
  local port=$1
  local pid
  pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo "  - killing PID $pid on port $port"
    kill -9 "$pid" 2>/dev/null || true
  fi
}

# ── 1. Free stale processes ───────────────────────────────────────────────────
echo "[1/8] Freeing ports 8000 8765 5173 4000 3001..."
for p in 8000 8765 5173 4000 3001; do kill_port "$p"; done
sleep 1

# ── 2. Ollama ─────────────────────────────────────────────────────────────────
echo "[2/8] Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "  Ollama not running — starting it..."
  ollama serve >> "$LOG_DIR/ollama.log" 2>&1 &
  sleep 4
else
  echo "  Ollama already running."
fi

# ── 3. NexusAgent API ─────────────────────────────────────────────────────────
echo "[3/8] Starting NexusAgent API (port 8000)..."
cd "$NEXUS_DIR"
source venv/bin/activate

# Run DB migrations first (idempotent — safe to run on every boot)
python -m db.migrate

# Production: no --reload, 2 workers, access log to file
nohup uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  >> "$LOG_DIR/api.log" 2>&1 &
echo "  PID $! → logs/api.log"
sleep 3

# ── 4. Build + serve frontend (production) ────────────────────────────────────
if [[ "${1:-}" == "--build" ]]; then
  echo "[4/8] Building App frontend..."
  cd "$FRONT_DIR" && npm ci && npm run build
  echo "  Build done — served from api.server static mount"
else
  echo "[4/8] Skipping frontend build (pass --build to rebuild)"
fi
# The FastAPI server mounts /frontend/dist as static files when built.
# No separate Vite dev server needed in production.

# ── 5. Landing page ───────────────────────────────────────────────────────────
echo "[5/8] Building + serving Landing page (port 4000)..."
cd "$LAND_DIR"
if [[ "${1:-}" == "--build" ]]; then
  npm ci && npm run build
fi
# Serve the landing dist with a lightweight static file server
nohup npx serve dist -l 4000 --no-clipboard \
  >> "$LOG_DIR/landing.log" 2>&1 &
echo "  PID $! → logs/landing.log"
sleep 2

# ── 6. Vox Agent Worker ───────────────────────────────────────────────────────
echo "[6/8] Starting Vox Agent worker..."
cd "$LAB_DIR"
source venv/bin/activate
nohup python -m voice_agent.agent prod \
  >> "$NEXUS_DIR/$LOG_DIR/vox.log" 2>&1 &
echo "  PID $! → logs/vox.log"
sleep 3

# ── 7. Voice-agent Server ─────────────────────────────────────────────────────
echo "[7/8] Starting Voice-agent server (port 8765)..."
nohup uvicorn voice_agent.server:app \
  --host 0.0.0.0 \
  --port 8765 \
  --workers 1 \
  >> "$NEXUS_DIR/$LOG_DIR/voice.log" 2>&1 &
echo "  PID $! → logs/voice.log"
sleep 2

# ── 8. WhatsApp Bridge ────────────────────────────────────────────────────────
echo "[8/8] Starting WhatsApp bridge (port 3001)..."
cd "$WA_DIR"
nohup node server.js \
  >> "$NEXUS_DIR/$LOG_DIR/whatsapp.log" 2>&1 &
echo "  PID $! → logs/whatsapp.log"
sleep 2

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ============================================================"
echo "   All services launched!"
echo ""
echo "   Landing page    : http://localhost:4000"
echo "   App frontend    : http://localhost:5173  (or via API static)"
echo "   NexusAgent API  : http://localhost:8000/docs"
echo "   Voice server    : http://localhost:8765/health"
echo "   WhatsApp bridge : http://localhost:3001/health"
echo ""
echo "   Logs in: $LOG_DIR/"
echo "  ============================================================"
echo ""
echo "To stop all services: bash stop.sh"
