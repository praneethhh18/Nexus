"""
Google Calendar OAuth + read-only event access.

Per-user connection: each user authorizes their own Google account.
Tokens are stored locally; only the meeting-prep agent reads them via
`api.calendar`. The OAuth callback is hit by Google's browser redirect,
not the SPA — so it returns an HTML close-window page rather than JSON.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from api.auth import get_current_user
from api import calendar as _cal

router = APIRouter(tags=["calendar"])


@router.get("/api/calendar/status")
def calendar_status(user: dict = Depends(get_current_user)):
    conn = _cal.get_connection(user["id"])
    configured = bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
    return {
        "configured": configured,
        "connected": bool(conn),
        "connection": conn,
    }


@router.post("/api/calendar/oauth/start")
def calendar_oauth_start(user: dict = Depends(get_current_user)):
    url = _cal.build_authorize_url(user["id"])
    return {"authorize_url": url}


@router.get("/api/calendar/oauth/callback")
def calendar_oauth_callback(code: str = "", state: str = "", error: str = ""):
    """
    This endpoint is hit by Google (browser redirect). We verify the signed
    state to recover the user_id, swap the code for tokens, and render a
    small HTML page that tells the user they can close the window.
    """
    if error:
        return HTMLResponse(f"<h3>Google sign-in failed</h3><p>{error}</p>", status_code=400)
    if not code or not state:
        return HTMLResponse("<h3>Missing code or state.</h3>", status_code=400)
    try:
        user_id = _cal._verify_state(state)
    except HTTPException as e:
        return HTMLResponse(f"<h3>Invalid state.</h3><p>{e.detail}</p>", status_code=400)

    redirect_uri = os.getenv(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:8000/api/calendar/oauth/callback",
    ).strip()
    tokens = _cal.exchange_code_for_tokens(code, redirect_uri)
    info = _cal.save_connection(user_id, tokens)

    return HTMLResponse(
        f"""
        <html><head><title>Calendar connected</title>
        <style>body{{font-family:Segoe UI,system-ui,sans-serif;background:#0c1222;color:#e2e8f0;
        display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
        .card{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:32px;max-width:420px;text-align:center}}
        h2{{color:#22c55e;margin-top:0}}</style></head><body>
        <div class="card">
          <h2>Calendar connected</h2>
          <p>Connected account: <strong>{info.get('account_email') or 'unknown'}</strong></p>
          <p style="color:#94a3b8;font-size:13px">You can close this window and return to NexusAgent.</p>
          <script>setTimeout(()=>window.close(), 1500)</script>
        </div></body></html>
        """,
    )


@router.get("/api/calendar/events")
def calendar_events(days: int = 14, limit: int = 20,
                    user: dict = Depends(get_current_user)):
    return _cal.list_upcoming_events(user["id"], days_ahead=days, max_results=limit)


@router.delete("/api/calendar/disconnect")
def calendar_disconnect(user: dict = Depends(get_current_user)):
    _cal.disconnect(user["id"])
    return {"ok": True}
