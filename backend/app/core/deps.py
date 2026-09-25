"""Authentication / authorization dependencies shared by the routers."""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, Request, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors
from app.core.database import SessionFactory, platform_session, tenant_session
from app.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    CSRF_HEADER,
    decode_token,
)
from app.models import UserSession


@dataclass
class CurrentUser:
    user_id: uuid.UUID
    user_type: str  # PLATFORM_ADMIN | TENANT_ADMIN | MEMBER | SYSTEM
    session_id: uuid.UUID
    email: str
    name: str
    tenant_id: uuid.UUID | None
    role: str | None

    @property
    def is_platform(self) -> bool:
        return self.user_type == "PLATFORM_ADMIN"

    @property
    def is_tenant_admin(self) -> bool:
        return self.user_type == "TENANT_ADMIN"


async def _session_from_token(request: Request) -> tuple[dict, UserSession]:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise errors.unauthorized("Missing access token")
    try:
        claims = decode_token(token)
    except Exception:
        raise errors.unauthorized("Invalid or expired access token") from None
    if claims.get("type") != "access":
        raise errors.unauthorized("Wrong token type")

    sid = claims.get("sid")
    async with SessionFactory() as db:
        session = (
            await db.execute(select(UserSession).where(UserSession.id == uuid.UUID(sid)))
        ).scalar_one_or_none()
        if session is None or session.revoked_at is not None:
            raise errors.unauthorized("Session revoked")
        if session.expires_at < datetime.now(timezone.utc):
            raise errors.unauthorized("Session expired")
        session.last_active_at = datetime.now(timezone.utc)
        await db.commit()
    return claims, session


async def get_current_user(request: Request) -> CurrentUser:
    claims, session = await _session_from_token(request)
    return CurrentUser(
        user_id=session.user_id,
        user_type=session.user_type,
        session_id=session.id,
        email=session.user_email,
        name=session.user_name,
        tenant_id=session.tenant_id,
        role=claims.get("role"),
    )


async def verify_csrf(request: Request) -> None:
    """Double-submit CSRF check for cookie-authenticated mutating requests."""

    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or cookie != header:
        raise errors.forbidden("CSRF token mismatch")


PLATFORM_ROLES = {"PLATFORM_ADMIN", "PLATFORM_SUPPORT", "PLATFORM_SECURITY"}


async def require_platform_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.user_type != "PLATFORM_ADMIN":
        raise errors.forbidden("Platform administrator access required")
    return user


async def require_platform_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.user_type != "PLATFORM_ADMIN" or user.role != "PLATFORM_ADMIN":
        raise errors.forbidden("PLATFORM_ADMIN role required")
    return user


async def require_tenant_user(
    tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Tenant member/admin whose JWT tenant matches the path tenant.

    Platform admins pass through for support/impersonation views; their audit
    entries still record actor_type=PLATFORM_ADMIN.
    """

    if user.user_type == "PLATFORM_ADMIN":
        return user
    if user.tenant_id != tenant_id:
        raise errors.forbidden("Token tenant does not match requested tenant")
    return user


async def require_tenant_admin(
    tenant_id: uuid.UUID, user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    await require_tenant_user(tenant_id, user)
    if user.user_type == "PLATFORM_ADMIN":
        return user
    if user.user_type != "TENANT_ADMIN":
        raise errors.forbidden("TENANT_ADMIN role required")
    return user


async def auth_db() -> AsyncIterator[AsyncSession]:
    """Pre-auth session for the auth router.

    Login/refresh legitimately look up principals across tenants before a
    tenant context exists, so they run under the platform RLS bypass. The
    bypass is scoped to this router only — nothing here trusts caller input
    for tenant isolation.
    """

    async with platform_session() as db:
        yield db


async def platform_db(
    user: CurrentUser = Depends(require_platform_user),
) -> AsyncIterator[AsyncSession]:
    """RLS-bypassing session for platform endpoints."""

    async with platform_session() as db:
        yield db


async def tenant_db(
    tenant_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
) -> AsyncIterator[AsyncSession]:
    """Tenant-scoped session; verifies tenant match and applies RLS context."""

    if user.user_type == "PLATFORM_ADMIN":
        async with platform_session() as db:
            yield db
        return
    if user.tenant_id != tenant_id:
        raise errors.forbidden("Token tenant does not match requested tenant")
    async with tenant_session(str(tenant_id)) as db:
        yield db


async def ws_current_user(websocket: WebSocket) -> CurrentUser | None:
    """Cookie auth for websockets — returns None instead of raising."""

    class _Req:
        def __init__(self, ws: WebSocket):
            self.cookies = ws.cookies
            self.headers = ws.headers
            self.client = ws.client

    try:
        return await get_current_user(_Req(websocket))  # type: ignore[arg-type]
    except Exception:
        return None
