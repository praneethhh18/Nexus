"""
Auth + 2FA + sessions + password-reset endpoints.

Public surface:
    /api/auth/signup, /login, /refresh, /forgot-password, /reset-password
Authed surface:
    /api/auth/me, /users, /change-password
    /api/auth/2fa/{status,enroll,verify,disable,regenerate-codes}
    /api/auth/sessions, /sessions/{jti}, /sessions/revoke-all-other
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

from api.auth import (
    create_user, authenticate_user,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, get_user_by_id, list_users,
    create_email_verification_token, consume_email_verification_token,
    require_email_verification, is_email_verified,
)
from api.businesses import (
    ensure_business_for_user, list_user_businesses,
)
from api import security as _sec
from utils.timez import now_utc_naive

router = APIRouter(tags=["auth"])


# ── Request schemas ─────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None  # required if 2FA is enabled


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TotpCode(BaseModel):
    code: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ── Public auth ─────────────────────────────────────────────────────────────
@router.post("/api/auth/signup")
def signup(req: SignupRequest):
    """Create the account. If REQUIRE_EMAIL_VERIFICATION is on (default in prod),
    no tokens are returned and no trial is activated yet — the frontend shows
    a "check your inbox" screen until the user clicks the verify link.

    In dev (REQUIRE_EMAIL_VERIFICATION=0), the legacy auto-login + auto-trial
    behaviour is preserved so the E2E checklist doesn't break.
    """
    user = create_user(req.email, req.name, req.password)
    biz_id = ensure_business_for_user(user["id"], user["name"])

    # Dev / opt-out path: same as the old flow — auto-login, trial already
    # started by ensure_business_for_user above.
    if not require_email_verification():
        access = create_access_token(user["id"], user["email"], user["role"])
        refresh = create_refresh_token(user["id"])
        return {
            "user": user,
            "access_token": access,
            "refresh_token": refresh,
            "businesses": list_user_businesses(user["id"]),
            "current_business_id": biz_id,
            "verification_required": False,
        }

    # Production path: send the verify link, hold tokens until verified.
    # Email failures don't block — the user can resend from the inbox screen.
    token = create_email_verification_token(user["id"], user["email"])
    try:
        from api.verification_emails import send_verification_email
        send_verification_email(to_email=user["email"], name=user["name"], token=token)
    except Exception as e:
        logger.warning(f"[Auth] verification email failed for {user['email']}: {e}")

    return {
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        "verification_required": True,
        "message": f"We sent a verification link to {user['email']}. "
                   f"Click it to activate your 14-day Pro trial.",
    }


class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/api/auth/verify-email")
def verify_email(req: VerifyEmailRequest):
    """Consume the verification token. On success: marks the user verified,
    activates their 14-day Pro trial (idempotently), and returns auth tokens
    so the frontend can drop the user straight into the dashboard with the
    confetti welcome modal."""
    user = consume_email_verification_token(req.token)
    if not user:
        raise HTTPException(400, "This verification link is invalid or has expired. "
                                 "Sign in and click 'Resend verification email'.")

    # Activate the trial now that email is verified. ensure_business_for_user
    # is idempotent — if a business already exists for this user, it just
    # returns the id. The trial-start inside it will now succeed because
    # is_email_verified() returns True.
    biz_id = ensure_business_for_user(user["id"], user["name"])

    # Fire the celebratory "trial is live" email. Wrapped in try/except because
    # SMTP transient failures must NOT block the verify response — the trial
    # row is already committed and the user is waiting on the tokens to land
    # in the dashboard. The email is a bonus, not a critical-path step.
    try:
        from api.businesses import get_business
        from api.verification_emails import send_trial_welcome_email
        biz = get_business(biz_id) or {}
        send_trial_welcome_email(
            to_email=user["email"],
            name=user["name"],
            business_name=biz.get("name"),
        )
    except Exception as e:
        logger.warning(f"[Auth] trial-welcome email failed (non-fatal) for {user['email']}: {e}")

    access = create_access_token(user["id"], user["email"], user["role"])
    refresh = create_refresh_token(user["id"])
    return {
        "user": user,
        "access_token": access,
        "refresh_token": refresh,
        "businesses": list_user_businesses(user["id"]),
        "current_business_id": biz_id,
        "trial_activated": True,
    }


class ResendVerificationRequest(BaseModel):
    email: str


@router.post("/api/auth/resend-verification")
def resend_verification(req: ResendVerificationRequest):
    """Send a fresh verification link. Throttled per-email indirectly via the
    token TTL (a new token invalidates the old one in create_email_verification_token).

    Privacy-preserving: returns the same response whether the email exists
    or not, so this can't be used to enumerate accounts.
    """
    from api.auth import get_user_by_email
    user = get_user_by_email(req.email)
    generic = {"ok": True, "message": "If that email is registered and unverified, "
                                       "a new link is on its way."}
    if not user:
        return generic
    if is_email_verified(user["id"]):
        return generic  # don't reveal verified state either
    token = create_email_verification_token(user["id"], user["email"])
    try:
        from api.verification_emails import send_verification_email
        send_verification_email(to_email=user["email"], name=user["name"], token=token)
    except Exception as e:
        logger.warning(f"[Auth] resend-verification failed for {user['email']}: {e}")
    return generic


@router.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    user = authenticate_user(req.email, req.password, request=request)
    if not user:
        raise HTTPException(401, "Invalid email or password")
    if require_email_verification() and not user.get("email_verified", True):
        try:
            token = create_email_verification_token(user["id"], user["email"])
            from api.verification_emails import send_verification_email
            send_verification_email(to_email=user["email"], name=user["name"], token=token)
        except Exception as e:
            logger.warning(f"[Auth] login blocked for unverified user; resend failed for {user['email']}: {e}")
        raise HTTPException(
            403,
            "Please verify your email before signing in. We sent a fresh verification link.",
        )

    if _sec.is_2fa_required(user["id"]):
        if not req.totp_code:
            return {
                "requires_2fa": True,
                "email": user["email"],
                "message": "Enter the 6-digit code from your authenticator app.",
            }
        if not _sec.verify_login_factor(user["id"], req.totp_code):
            raise HTTPException(401, "Invalid 2FA code")

    biz_id = ensure_business_for_user(user["id"], user["name"])
    access = create_access_token(user["id"], user["email"], user["role"])
    refresh = create_refresh_token(user["id"])

    # Record this session for visibility + revocation
    try:
        payload = decode_token(access)
        jti = payload.get("jti", "")
        if jti:
            _sec.record_session(
                jti=jti, user_id=user["id"],
                user_agent=(request.headers.get("user-agent") or "")[:300],
                ip=(request.client.host if request.client else "") or "",
                expires_at=datetime.utcfromtimestamp(payload["exp"])
                if isinstance(payload.get("exp"), (int, float))
                else now_utc_naive() + timedelta(hours=24),
            )
    except Exception as e:
        logger.debug(f"[Auth] session recording skipped: {e}")

    return {
        "user": user,
        "access_token": access,
        "refresh_token": refresh,
        "businesses": list_user_businesses(user["id"]),
        "current_business_id": biz_id,
    }


@router.post("/api/auth/refresh")
def refresh_token(body: dict):
    token = body.get("refresh_token", "")
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    access = create_access_token(user["id"], user["email"], user["role"])
    return {"access_token": access, "user": user}


# ── Authed identity ─────────────────────────────────────────────────────────
@router.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "user": user,
        "businesses": list_user_businesses(user["id"]),
    }


@router.get("/api/auth/users")
def get_users(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return list_users()


@router.post("/api/auth/change-password")
def change_password_api(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    from api.auth import change_password
    change_password(user["id"], req.current_password, req.new_password)
    return {"ok": True}


# ── 2FA ─────────────────────────────────────────────────────────────────────
@router.get("/api/auth/2fa/status")
def twofa_status(user: dict = Depends(get_current_user)):
    return _sec.get_2fa_state(user["id"])


@router.post("/api/auth/2fa/enroll")
def twofa_enroll(user: dict = Depends(get_current_user)):
    """Start enrollment. Returns the secret + QR code. 2FA is NOT active yet."""
    return _sec.start_2fa_enrollment(user["id"], user["email"])


@router.post("/api/auth/2fa/verify")
def twofa_verify(req: TotpCode, user: dict = Depends(get_current_user)):
    """Verify the first code to finalize enrollment. Returns recovery codes ONCE."""
    recovery = _sec.verify_and_enable_2fa(user["id"], req.code)
    return {
        "enabled": True,
        "recovery_codes": recovery,
        "message": "2FA is now active. Save these recovery codes somewhere safe — they won't be shown again.",
    }


@router.post("/api/auth/2fa/disable")
def twofa_disable(req: TotpCode, user: dict = Depends(get_current_user)):
    _sec.disable_2fa(user["id"], req.code)
    return {"ok": True}


@router.post("/api/auth/2fa/regenerate-codes")
def twofa_regenerate_codes(req: TotpCode, user: dict = Depends(get_current_user)):
    codes = _sec.regenerate_recovery_codes(user["id"], req.code)
    return {"recovery_codes": codes}


# ── Sessions ────────────────────────────────────────────────────────────────
@router.get("/api/auth/sessions")
def sessions_list(user: dict = Depends(get_current_user)):
    sessions = _sec.list_sessions(user["id"])
    current_jti = user.get("_jti")
    for s in sessions:
        s["is_current"] = (s["jti"] == current_jti)
    return sessions


@router.delete("/api/auth/sessions/{jti}")
def revoke_session(jti: str, user: dict = Depends(get_current_user)):
    if jti == user.get("_jti"):
        raise HTTPException(400, "Use /logout to end your current session")
    _sec.revoke_session(user["id"], jti)
    return {"ok": True}


@router.post("/api/auth/sessions/revoke-all-other")
def revoke_all_other(user: dict = Depends(get_current_user)):
    current = user.get("_jti", "")
    count = _sec.revoke_all_other_sessions(user["id"], current)
    return {"ok": True, "revoked": count}


# ── Password reset (public) ─────────────────────────────────────────────────
def _send_reset_email(to_email: str, to_name: str, token: str) -> bool:
    """Send the reset email. Returns True on success, False if email is disabled."""
    import os
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    base_url = os.getenv("APP_BASE_URL", "http://localhost:5173").rstrip("/")
    reset_link = f"{base_url}/reset-password?token={token}"

    if not EMAIL_ENABLED:
        logger.warning(f"[Auth] EMAIL not configured — reset link for {to_email}: {reset_link}")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        subject = "NexusAgent — Reset your password"
        body = (
            f"Hi {to_name or 'there'},\n\n"
            f"Someone (hopefully you) asked to reset your NexusAgent password. "
            f"Click the link below to set a new one. This link is valid for 1 hour.\n\n"
            f"{reset_link}\n\n"
            f"If you didn't request this, you can safely ignore this email — "
            f"your password will not be changed.\n\n"
            f"— NexusAgent"
        )
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"[Auth] Reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"[Auth] Reset email failed: {e}")
        return False


@router.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """
    Always returns the same response regardless of whether the email exists,
    to avoid email enumeration.
    """
    from api.auth import request_password_reset
    result = request_password_reset(req.email)
    if result:
        token, user = result
        _send_reset_email(user["email"], user.get("name", ""), token)
    return {
        "ok": True,
        "message": "If that email is registered, a reset link has been sent.",
    }


@router.post("/api/auth/reset-password")
def reset_password_api(req: ResetPasswordRequest):
    from api.auth import consume_password_reset
    consume_password_reset(req.token, req.new_password)
    return {"ok": True, "message": "Password updated. You can now sign in."}
