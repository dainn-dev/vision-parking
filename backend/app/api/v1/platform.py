"""Platform governance: tenant lifecycle, platform admins, settings, feature flags."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors, security
from app.core.audit import write_audit
from app.core.deps import CurrentUser, platform_db, require_platform_user, verify_csrf
from app.core.pagination import Page, PageParams
from app.core.security import client_ip
from app.models import (
    AccessEvent,
    BarrierGate,
    EdgeDevice,
    FeatureFlag,
    PlatformSetting,
    RegisteredVehicle,
    Tenant,
    TenantUser,
)
from app.models.platform import PlatformAdmin
from app.schemas.auth import MessageResponse
from app.schemas.platform import (
    FeatureFlagOut,
    FeatureFlagUpsert,
    PlatformAdminCreate,
    PlatformAdminOut,
    PlatformAdminUpdate,
    PlatformSettingsOut,
    SettingsSectionUpdate,
    TenantAdministratorOut,
    TenantCreate,
    TenantOut,
    TenantStatistics,
    TenantStatusUpdate,
    TenantUpdate,
)

router = APIRouter(prefix="/platform", tags=["platform"], dependencies=[Depends(verify_csrf)])


# ------------------------------------------------------------------ helpers


async def _tenant_stats(db: AsyncSession, tenant_id: uuid.UUID) -> TenantStatistics:
    async def count(model) -> int:
        return (
            await db.execute(select(func.count()).select_from(model).where(model.tenant_id == tenant_id))
        ).scalar_one()

    return TenantStatistics(
        users_count=await count(TenantUser),
        vehicles_count=await count(RegisteredVehicle),
        cameras_count=0,  # cameras are edge-side; exposed via edge telemetry
        gates_count=await count(BarrierGate),
        edge_devices_count=await count(EdgeDevice),
        events_count=await count(AccessEvent),
        storage_used_gb=0.0,
    )


async def _tenant_out(db: AsyncSession, tenant: Tenant) -> TenantOut:
    admin = (
        (
            await db.execute(
                select(TenantUser)
                .where(TenantUser.tenant_id == tenant.id, TenantUser.role == "TENANT_ADMIN")
                .order_by(TenantUser.created_at)
            )
        )
        .scalars()
        .first()
    )
    return TenantOut(
        id=tenant.id,
        name=tenant.name,
        code=tenant.code,
        email=tenant.email,
        phone=tenant.phone,
        timezone=tenant.timezone,
        status=tenant.status,
        administrator=TenantAdministratorOut(
            id=admin.id, name=admin.name, email=admin.email, phone=admin.phone
        )
        if admin
        else None,
        statistics=await _tenant_stats(db, tenant.id),
        created_at=tenant.created_at,
        last_activity_at=tenant.last_activity_at,
    )


# ------------------------------------------------------------------ tenants


@router.get("/tenants", response_model=Page[TenantOut])
async def list_tenants(
    page: PageParams = Depends(),
    status: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(Tenant)
    if status:
        q = q.where(Tenant.status == status.upper())
    if search:
        like = f"%{search.lower()}%"
        q = q.where(func.lower(Tenant.name).like(like) | func.lower(Tenant.code).like(like))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(Tenant.created_at.desc()).offset(page.offset).limit(page.page_size))
    ).scalars()
    items = [await _tenant_out(db, t) for t in rows]
    return Page[TenantOut](items=items, total=total, page=page.page, page_size=page.page_size)


@router.post("/tenants", response_model=TenantOut, status_code=201)
async def create_tenant(
    body: TenantCreate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    code = body.code.upper()
    if (await db.execute(select(func.count()).select_from(Tenant).where(Tenant.code == code))).scalar_one():
        raise errors.conflict("TENANT_CODE_EXISTS", "Organization code already registered")

    tenant = Tenant(
        name=body.name,
        code=code,
        email=body.email.lower(),
        phone=body.phone,
        timezone=body.timezone,
        status="ACTIVE",
    )
    db.add(tenant)
    await db.flush()

    admin = TenantUser(
        tenant_id=tenant.id,
        name=body.administrator.name,
        email=body.administrator.email.lower(),
        phone=body.administrator.phone,
        role="TENANT_ADMIN",
        status="ACTIVE" if body.administrator.password else "INVITED",
        password_hash=security.hash_password(body.administrator.password)
        if body.administrator.password
        else None,
        invited_at=datetime.now(timezone.utc),
    )
    db.add(admin)
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="TENANT_CREATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_name=user.name,
        actor_email=user.email,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        resource_type="TENANT",
        resource_id=str(tenant.id),
        resource_name=tenant.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return await _tenant_out(db, tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantOut)
async def get_tenant(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise errors.not_found("Tenant", tenant_id)
    return await _tenant_out(db, tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantOut)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise errors.not_found("Tenant", tenant_id)
    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(tenant, field, value)
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="TENANT_UPDATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        resource_type="TENANT",
        resource_id=str(tenant.id),
        resource_name=tenant.name,
        ip_address=client_ip(request),
        changes=[{"field": k, "after": v} for k, v in updates.items()],
    )
    await db.commit()
    return await _tenant_out(db, tenant)


@router.post("/tenants/{tenant_id}/status", response_model=TenantOut)
async def set_tenant_status(
    tenant_id: uuid.UUID,
    body: TenantStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise errors.not_found("Tenant", tenant_id)
    before = tenant.status
    tenant.status = body.status
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action=f"TENANT_STATUS_{body.status}",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        resource_type="TENANT",
        resource_id=str(tenant.id),
        resource_name=tenant.name,
        ip_address=client_ip(request),
        changes=[{"field": "status", "before": before, "after": body.status}],
        metadata={"reason": body.reason} if body.reason else None,
    )
    await db.commit()
    return await _tenant_out(db, tenant)


# ------------------------------------------------------------------ admins


@router.get("/admins", response_model=Page[PlatformAdminOut])
async def list_admins(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    total = (await db.execute(select(func.count()).select_from(PlatformAdmin))).scalar_one()
    rows = (
        await db.execute(
            select(PlatformAdmin).order_by(PlatformAdmin.created_at).offset(page.offset).limit(page.page_size)
        )
    ).scalars()
    return Page[PlatformAdminOut](
        items=[PlatformAdminOut.model_validate(a) for a in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/admins", response_model=PlatformAdminOut, status_code=201)
async def create_admin(
    body: PlatformAdminCreate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    if (
        await db.execute(
            select(func.count()).select_from(PlatformAdmin).where(PlatformAdmin.email == body.email.lower())
        )
    ).scalar_one():
        raise errors.conflict("EMAIL_EXISTS", "Admin email already registered")
    admin = PlatformAdmin(
        name=body.name,
        email=body.email.lower(),
        role=body.role,
        status="ACTIVE" if body.password else "PENDING",
        password_hash=security.hash_password(body.password or security.generate_csrf_token()),
    )
    db.add(admin)
    await db.flush()
    await write_audit(
        db,
        category="PLATFORM_ADMIN",
        action="ADMIN_ACCOUNT_CREATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="ADMIN",
        resource_id=str(admin.id),
        resource_name=admin.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return PlatformAdminOut.model_validate(admin)


@router.patch("/admins/{admin_id}", response_model=PlatformAdminOut)
async def update_admin(
    admin_id: uuid.UUID,
    body: PlatformAdminUpdate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    admin = await db.get(PlatformAdmin, admin_id)
    if admin is None:
        raise errors.not_found("PlatformAdmin", admin_id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(admin, field, value)
    await write_audit(
        db,
        category="PLATFORM_ADMIN",
        action="ADMIN_ACCOUNT_UPDATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="ADMIN",
        resource_id=str(admin_id),
        resource_name=admin.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return PlatformAdminOut.model_validate(admin)


@router.post("/admins/{admin_id}/disable", response_model=PlatformAdminOut)
async def disable_admin(
    admin_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    admin = await db.get(PlatformAdmin, admin_id)
    if admin is None:
        raise errors.not_found("PlatformAdmin", admin_id)
    active_admins = (
        await db.execute(
            select(func.count())
            .select_from(PlatformAdmin)
            .where(PlatformAdmin.status == "ACTIVE", PlatformAdmin.role == "PLATFORM_ADMIN")
        )
    ).scalar_one()
    if admin.role == "PLATFORM_ADMIN" and admin.status == "ACTIVE" and active_admins <= 1:
        raise errors.conflict("LAST_ADMIN", "Cannot disable the last active PLATFORM_ADMIN")
    admin.status = "DISABLED"

    from app.models import UserSession

    sessions = (
        await db.execute(
            select(UserSession).where(UserSession.user_id == admin_id, UserSession.revoked_at.is_(None))
        )
    ).scalars()
    now = datetime.now(timezone.utc)
    for s in sessions:
        s.revoked_at = now

    await write_audit(
        db,
        category="PLATFORM_ADMIN",
        action="ADMIN_ACCOUNT_DISABLED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="ADMIN",
        resource_id=str(admin_id),
        resource_name=admin.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return PlatformAdminOut.model_validate(admin)


@router.post("/admins/{admin_id}/mfa-reset", response_model=PlatformAdminOut)
async def reset_admin_mfa(
    admin_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    admin = await db.get(PlatformAdmin, admin_id)
    if admin is None:
        raise errors.not_found("PlatformAdmin", admin_id)
    admin.mfa_enabled = False
    admin.mfa_secret_enc = None
    admin.mfa_configured_at = None
    from app.models import SecurityAlert

    db.add(
        SecurityAlert(
            type="MFA_RESET",
            severity="MEDIUM",
            status="OPEN",
            subject_email=admin.email,
            subject_user_type="PLATFORM_ADMIN",
            source_ip=client_ip(request),
            evidence={"details": f"MFA reset performed by {user.email}"},
        )
    )
    await write_audit(
        db,
        category="SECURITY",
        action="MFA_RESET_PERFORMED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="ADMIN",
        resource_id=str(admin_id),
        resource_name=admin.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return PlatformAdminOut.model_validate(admin)


# ------------------------------------------------------------------ feature flags


@router.get("/feature-flags", response_model=list[FeatureFlagOut])
async def list_flags(
    db: AsyncSession = Depends(platform_db), user: CurrentUser = Depends(require_platform_user)
):
    rows = (await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))).scalars()
    return [FeatureFlagOut.model_validate(f) for f in rows]


@router.post("/feature-flags", response_model=FeatureFlagOut, status_code=201)
async def upsert_flag(
    body: FeatureFlagUpsert,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    if not body.key:
        raise errors.ApiError("VALIDATION", "key is required", 422)
    flag = (await db.execute(select(FeatureFlag).where(FeatureFlag.key == body.key))).scalar_one_or_none()
    created = flag is None
    if created:
        flag = FeatureFlag(key=body.key, name=body.name or body.key)
        db.add(flag)
    for field in ("name", "description", "enabled", "environment", "rollout_percentage"):
        value = getattr(body, field)
        if value is not None:
            setattr(flag, field, value)
    if body.rules is not None:
        flag.rules = [r.model_dump(mode="json") for r in body.rules]
    flag.updated_by = user.email
    await write_audit(
        db,
        category="CONFIGURATION",
        action="FEATURE_FLAG_CREATED" if created else "FEATURE_FLAG_UPDATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="FEATURE_FLAG",
        resource_name=flag.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return FeatureFlagOut.model_validate(flag)


@router.post("/feature-flags/{flag_id}/toggle", response_model=FeatureFlagOut)
async def toggle_flag(
    flag_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    flag = await db.get(FeatureFlag, flag_id)
    if flag is None:
        raise errors.not_found("FeatureFlag", flag_id)
    flag.enabled = not flag.enabled
    flag.updated_by = user.email
    await write_audit(
        db,
        category="CONFIGURATION",
        action="FEATURE_FLAG_TOGGLED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="FEATURE_FLAG",
        resource_id=str(flag_id),
        resource_name=flag.name,
        ip_address=client_ip(request),
        changes=[{"field": "enabled", "before": not flag.enabled, "after": flag.enabled}],
    )
    await db.commit()
    return FeatureFlagOut.model_validate(flag)


# ------------------------------------------------------------------ settings


_DEFAULTS = PlatformSettingsOut()


@router.get("/settings", response_model=PlatformSettingsOut)
async def get_settings(
    db: AsyncSession = Depends(platform_db), user: CurrentUser = Depends(require_platform_user)
):
    rows = (await db.execute(select(PlatformSetting))).scalars()
    stored = {r.section: r.data for r in rows}
    merged = _DEFAULTS.model_dump()
    for section, data in stored.items():
        if section in merged and isinstance(data, dict):
            merged[section].update(data)
    return PlatformSettingsOut.model_validate(merged)


@router.put("/settings/{section}", response_model=PlatformSettingsOut)
async def update_settings_section(
    section: str,
    body: SettingsSectionUpdate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    valid = {"general", "authentication", "security", "storage", "notifications"}
    if section not in valid:
        raise errors.not_found("SettingsSection", section)
    row = await db.get(PlatformSetting, section)
    if row is None:
        row = PlatformSetting(section=section, data={})
        db.add(row)
    row.data = {**(row.data or {}), **body.data}
    row.updated_by = user.email
    await write_audit(
        db,
        category="CONFIGURATION",
        action=f"SETTINGS_SECTION_UPDATED_{section.upper()}",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="SETTINGS",
        resource_id=section,
        ip_address=client_ip(request),
    )
    await db.commit()
    return await get_settings(db=db, user=user)


# ------------------------------------------------------------------ tenant user invites


@router.post("/tenants/{tenant_id}/admins/{user_id}/resend-invite", response_model=MessageResponse)
async def resend_invite(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    tenant_user = await db.get(TenantUser, user_id)
    if tenant_user is None or tenant_user.tenant_id != tenant_id:
        raise errors.not_found("TenantUser", user_id)
    from arq.connections import create_pool

    from app.worker.settings import redis_settings

    pool = await create_pool(redis_settings())
    await pool.enqueue_job("send_invite", tenant_user.email, str(tenant_id), tenant_user.name)
    return MessageResponse(message="Invitation email queued")
