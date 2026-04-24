"""
FastAPI routers — one per domain.

`server.py` used to be a 3,700-line monolith with every endpoint inline. We're
splitting it one domain at a time. New endpoint groups should land here rather
than in server.py; old groups get extracted opportunistically as they're
touched.

Every router module exposes a module-level `router = APIRouter(...)` that
server.py includes with `app.include_router(...)`.
"""
