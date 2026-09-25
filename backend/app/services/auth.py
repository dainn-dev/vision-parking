"""Login, refresh-rotation, logout and MFA flows shared by the auth router."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors, security
from app.core.audit import write_audit
from app.core.config import get_settings
from app.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    REFRESH_COOKIE,
    client_ip,
    generate_csrf_token,
    parse_user_agent,
)
from app.models import LoginEvent, SecurityAlert, Tenant, TenantUser, UserSession
from app.models.platform import PlatformAdmin

settings = get_settings()


class Principal:
    """Unified view over PlatformAdmin and TenantUser."""

    def __init__(self, obj, user_type: str, tenant_id=None, tenant_name=None):
        self.obj = obj
        self.id: uuid.UUID = obj.id
        self.user_type = user_type
        self.name: str = obj.name
        self.email: str = obj.email
        self.role: str = getattr(obj, "role", None)
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.password_hash = getattr(obj, "password_hash", None)
        self.status = getattr(obj, "status", "ACTIVE")
        self.mfa_enabled = getattr(obj, "mfa_enabled", False)
        self.mfa_secret_enc = getattr(obj, "mfa_secret_enc", None)
        self.failed_login_attempts = getattr(obj, "failed_login_attempts", 0)
        self.locked_until = getattr(obj, "locked_until", None)


async def find_principal(db: AsyncSession, email: str) -> Principal | None:
    admin = (
        await db.execute(select(PlatformAdmin).where(PlatformAdmin.email == email.lower()))
    ).scalar_one_or_none()
    if admin:
        return Principal(admin, "PLATFORM_ADMIN")

    user = (
        await db.execute(select(TenantUser).where(TenantUser.email == email.lower()))
    ).scalar_one_or_none()
    if user:
        tenant = await db.get(Tenant, user.tenant_id)
        user_type = "TENANT_ADMIN" if user.role == "TENANT_ADMIN" else "MEMBER"
        return Principal(
            user, user_type, tenant_id=user.tenant_id, tenant_name=tenant.name if tenant else None
        )
    return None


async def _record_login_event(
    db: AsyncSession,
    request: Request,
    principal: Principal | None,
    email: str,
    result: str,
    failure_reason: str | None = None,
    suspicious: bool = False,
) -> None:
    ua = request.headers.get("user-agent")
    _, _, device = parse_user_agent(ua)
    db.add(
        LoginEvent(
            user_email=email,
            user_type=principal.user_type if principal else "UNKNOWN",
            tenant_id=principal.tenant_id if principal else None,
            tenant_name=principal.tenant_name if principal else None,
            result=result,
            source_ip=client_ip(request),
            client_device=device or (ua[:120] if ua else None),
            failure_reason=failure_reason,
            suspicious=suspicious,
        )
    )


async def _failed_attempt(
    db: AsyncSession, request: Request, principal: Principal | None, email: str
) -> None:
    await _record_login_event(db, request, principal, email, "FAILED", "INVALID_CREDENTIALS")
    if principal is None:
        return
    obj = principal.obj
    obj.failed_login_attempts = (obj.failed_login_attempts or 0) + 1
    if obj.failed_login_attempts >= 5:
        obj.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.add(
            SecurityAlert(
                type="ACCOUNT_LOCKED",
                severity="HIGH",
                subject_email=email,
                subject_user_type=principal.user_type,
                source_ip=client_ip(request),
                client_browser=request.headers.get("user-agent"),
                evidence={"failedAttempts": obj.failed_login_attempts},
            )
        )
        await _record_login_event(db, request, principal, email, "BLOCKED", "ACCOUNT_LOCKED", suspicious=True)


async def authenticate(db: AsyncSession, request: Request, email: str, password: str) -> Principal | None:
    principal = await find_principal(db, email.lower())
    if principal is None or principal.password_hash is None:
        await _record_login_event(db, request, None, email, "FAILED", "INVALID_CREDENTIALS")
        return None

    if principal.status in ("DISABLED", "LOCKED"):
        await _record_login_event(db, request, principal, email, "BLOCKED", "ACCOUNT_DISABLED")
        return None
    if principal.locked_until and principal.locked_until > datetime.now(timezone.utc):
        await _record_login_event(db, request, principal, email, "BLOCKED", "ACCOUNT_LOCKED", suspicious=True)
        return None
    if principal.status == "TRIAL" and principal.user_type == "PLATFORM_ADMIN":
        pass  # platform admins are never TRIAL — defensive only
    if not security.verify_password(password, principal.password_hash):
        await _failed_attempt(db, request, principal, email)
        return None
    return principal


def set_auth_cookies(response: Response, access: str, refresh: str, refresh_expires: datetime) -> str:
    csrf = generate_csrf_token()
    common = {
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "domain": settings.cookie_domain or None,
    }
    response.set_cookie(
        ACCESS_COOKIE, access, httponly=True, max_age=settings.access_token_minutes * 60, path="/", **common
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        httponly=True,
        max_age=int((refresh_expires - datetime.now(timezone.utc)).total_seconds()),
        path="/api/v1/auth",
        **common,
    )
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, path="/", **common)
    return csrf


def clear_auth_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


async def issue_session(
    db: AsyncSession, request: Request, response: Response, principal: Principal
) -> tuple[UserSession, str]:
    ua = request.headers.get("user-agent")
    browser, os_name, device = parse_user_agent(ua)
    refresh, expires = security.create_refresh_token(uuid.uuid4())
    session = UserSession(
        user_id=principal.id,
        user_type=principal.user_type,
        user_name=principal.name,
        user_email=principal.email,
        tenant_id=principal.tenant_id,
        tenant_name=principal.tenant_name,
        refresh_token_hash=security.hash_token(refresh),
        family_id=uuid.uuid4(),
        device=device,
        browser=browser,
        os=os_name,
        ip_address=client_ip(request),
        risk_level="NORMAL",
        expires_at=expires,
    )
    db.add(session)
    await db.flush()

    # Re-mint refresh bound to the real session id.
    refresh, expires = security.create_refresh_token(session.id)
    session.refresh_token_hash = security.hash_token(refresh)
    session.expires_at = expires

    access = security.create_access_token(
        principal.id,
        principal.user_type,
        session.id,
        tenant_id=principal.tenant_id,
        role=principal.role,
    )
    csrf = set_auth_cookies(response, access, refresh, expires)

    obj = principal.obj
    obj.last_login_at = datetime.now(timezone.utc)
    obj.failed_login_attempts = 0
    obj.locked_until = None

    await _record_login_event(db, request, principal, principal.email, "SUCCESS")
    await write_audit(
        db,
        category="AUTHENTICATION",
        action=f"{principal.user_type}_LOGIN",
        actor_type=principal.user_type,
        actor_id=principal.id,
        actor_name=principal.name,
        actor_email=principal.email,
        tenant_id=principal.tenant_id,
        tenant_name=principal.tenant_name,
        resource_type="SESSION",
        resource_id=str(session.id),
        source="WEB",
        ip_address=client_ip(request),
    )
    return session, csrf


async def refresh_session(db: AsyncSession, request: Request, response: Response) -> str:
    """Rotate refresh token; detects reuse of a rotated token family."""

    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise errors.unauthorized("Missing refresh token")
    try:
        claims = security.decode_token(token)
    except Exception:
        clear_auth_cookies(response)
        raise errors.unauthorized("Invalid refresh token") from None
    if claims.get("type") != "refresh":
        raise errors.unauthorized("Wrong token type")

    session = (
        await db.execute(select(UserSession).where(UserSession.id == uuid.UUID(claims["sub"])))
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or session.expires_at < now:
        clear_auth_cookies(response)
        raise errors.unauthorized("Session expired or revoked")

    if session.refresh_token_hash != security.hash_token(token):
        # Reuse of an already-rotated token — kill the whole family.
        family = (
            await db.execute(select(UserSession).where(UserSession.family_id == session.family_id))
        ).scalars()
        for s in family:
            s.revoked_at = now
        db.add(
            SecurityAlert(
                type="SUSPICIOUS_LOGIN",
                severity="CRITICAL",
                subject_email=session.user_email,
                subject_user_type=session.user_type,
                source_ip=client_ip(request),
                evidence={"details": "Refresh token reuse detected; session family revoked"},
            )
        )
        clear_auth_cookies(response)
        raise errors.unauthorized("Refresh token reuse detected")

    principal = await find_principal(db, session.user_email)
    role = principal.role if principal else None
    refresh, expires = security.create_refresh_token(session.id)
    session.refresh_token_hash = security.hash_token(refresh)
    session.expires_at = expires
    session.last_active_at = now
    access = security.create_access_token(
        session.user_id, session.user_type, session.id, tenant_id=session.tenant_id, role=role
    )
    set_auth_cookies(response, access, refresh, expires)
    return session.user_email


async def logout(db: AsyncSession, request: Request, response: Response) -> None:
    token = request.cookies.get(ACCESS_COOKIE)
    sid = None
    if token:
        try:
            sid = security.decode_token(token).get("sid")
        except Exception:
            sid = None
    if sid:
        session = await db.get(UserSession, uuid.UUID(sid))
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            await write_audit(
                db,
                category="AUTHENTICATION",
                action="LOGOUT",
                actor_type=session.user_type,
                actor_id=session.user_id,
                actor_email=session.user_email,
                resource_type="SESSION",
                resource_id=sid,
                source="WEB",
                ip_address=client_ip(request),
            )
    clear_auth_cookies(response)


def create_challenge_token(principal: Principal, kind: str = "mfa_challenge") -> str:
    return security.create_short_token(
        str(principal.id),
        kind,
        minutes=5,
        extra={
            "user_type": principal.user_type,
            "tenant_id": str(principal.tenant_id) if principal.tenant_id else None,
        },
    )


def decode_challenge_token(token: str) -> dict:
    claims = security.decode_token(token)
    if claims.get("type") not in ("mfa_challenge", "mfa_enroll"):
        raise errors.unauthorized("Invalid challenge token")
    return claims
