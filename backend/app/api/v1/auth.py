"""Authentication endpoints — cookie-based access/refresh, TOTP MFA."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors, security
from app.core.deps import CurrentUser, auth_db, get_current_user
from app.models import TenantUser
from app.models.platform import PlatformAdmin
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    MfaChallengeRequest,
    MfaEnrollStart,
    MfaEnrollVerify,
    UserInfo,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(auth_db)
):
    principal = await auth_service.authenticate(db, request, body.email, body.password)
    if principal is None:
        await db.commit()
        raise errors.unauthorized("Invalid credentials")

    if principal.mfa_enabled:
        if not body.otp_code:
            challenge = auth_service.create_challenge_token(principal)
            await auth_service._record_login_event(db, request, principal, body.email, "CHALLENGED")
            await db.commit()
            return LoginResponse(status="MFA_REQUIRED", challenge_token=challenge)
        secret = security.decrypt_totp_secret(principal.mfa_secret_enc)
        if not security.verify_totp(secret, body.otp_code):
            await auth_service._record_login_event(
                db, request, principal, body.email, "FAILED", "MFA_FAILED", suspicious=True
            )
            await db.commit()
            raise errors.unauthorized("Invalid MFA code")

    session, csrf = await auth_service.issue_session(db, request, response, principal)
    await db.commit()
    return LoginResponse(
        status="AUTHENTICATED",
        user=UserInfo(
            id=principal.id,
            name=principal.name,
            email=principal.email,
            user_type=principal.user_type,
            role=principal.role,
            tenant_id=principal.tenant_id,
            mfa_enabled=principal.mfa_enabled,
        ),
    )


@router.post("/mfa/challenge", response_model=LoginResponse)
async def mfa_challenge(
    body: MfaChallengeRequest, request: Request, response: Response, db: AsyncSession = Depends(auth_db)
):
    claims = auth_service.decode_challenge_token(body.challenge_token)
    user_id = uuid.UUID(claims["sub"])
    user_type = claims.get("user_type")
    if user_type == "PLATFORM_ADMIN":
        obj = await db.get(PlatformAdmin, user_id)
    else:
        obj = await db.get(TenantUser, user_id)
    if obj is None:
        raise errors.unauthorized("Unknown principal")
    principal = await auth_service.find_principal(db, obj.email)
    if principal is None or not principal.mfa_enabled:
        raise errors.unauthorized("MFA not enabled for account")
    secret = security.decrypt_totp_secret(principal.mfa_secret_enc)
    if not security.verify_totp(secret, body.otp_code):
        raise errors.unauthorized("Invalid MFA code")

    await auth_service.issue_session(db, request, response, principal)
    await db.commit()
    return LoginResponse(
        status="AUTHENTICATED",
        user=UserInfo(
            id=principal.id,
            name=principal.name,
            email=principal.email,
            user_type=principal.user_type,
            role=principal.role,
            tenant_id=principal.tenant_id,
            mfa_enabled=True,
        ),
    )


@router.post("/refresh", response_model=MessageResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(auth_db)):
    await auth_service.refresh_session(db, request, response)
    await db.commit()
    return MessageResponse(message="Session refreshed")


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(auth_db)):
    await auth_service.logout(db, request, response)
    await db.commit()
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserInfo)
async def me(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(auth_db)):
    mfa = False
    if user.user_type == "PLATFORM_ADMIN":
        obj = await db.get(PlatformAdmin, user.user_id)
    else:
        obj = await db.get(TenantUser, user.user_id)
    if obj:
        mfa = bool(obj.mfa_enabled)
    return UserInfo(
        id=user.user_id,
        name=user.name,
        email=user.email,
        user_type=user.user_type,
        role=user.role,
        tenant_id=user.tenant_id,
        mfa_enabled=mfa,
    )


# ------------------------------------------------------------ MFA enrollment


@router.post("/mfa/enroll/start", response_model=MfaEnrollStart)
async def mfa_enroll_start(
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(auth_db)
):
    if user.user_type == "PLATFORM_ADMIN":
        obj = await db.get(PlatformAdmin, user.user_id)
    else:
        obj = await db.get(TenantUser, user.user_id)
    if obj is None:
        raise errors.not_found("User")
    secret = security.generate_totp_secret()
    obj.mfa_secret_enc = security.encrypt_totp_secret(secret)
    await db.commit()
    return MfaEnrollStart(secret=secret, otpauth_uri=security.totp_uri(secret, user.email))


@router.post("/mfa/enroll/verify", response_model=MessageResponse)
async def mfa_enroll_verify(
    body: MfaEnrollVerify,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(auth_db),
):
    if user.user_type == "PLATFORM_ADMIN":
        obj = await db.get(PlatformAdmin, user.user_id)
    else:
        obj = await db.get(TenantUser, user.user_id)
    if obj is None or not obj.mfa_secret_enc:
        raise errors.unauthorized("Start MFA enrollment first")
    secret = security.decrypt_totp_secret(obj.mfa_secret_enc)
    if not security.verify_totp(secret, body.otp_code):
        raise errors.unauthorized("Invalid MFA code")
    obj.mfa_enabled = True
    obj.mfa_configured_at = datetime.now(timezone.utc)
    await db.commit()
    return MessageResponse(message="MFA enabled")
