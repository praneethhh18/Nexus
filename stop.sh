#!/usr/bin/env bash
# NexusAgent — Stop all services
for port in 8000 8765 5173 4000 3001; do
  pid=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [ -n "$pid" ]; then
    echo "Stopping port $port (PID $pid)"
    kill -9 "$pid" 2>/dev/null || true
  fi
done
echo "Done."
