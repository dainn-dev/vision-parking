"""Platform operations: monitoring, security alerts, sessions, credentials, audit."""

import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors, security
from app.core.audit import write_audit
from app.core.deps import CurrentUser, platform_db, require_platform_user, verify_csrf
from app.core.pagination import Page, PageParams
from app.core.security import client_ip
from app.models import (
    ApiCredential,
    AuditLog,
    BarrierGate,
    BarrierIncident,
    EdgeDevice,
    LoginEvent,
    SecurityAlert,
    Tenant,
    UserSession,
)
from app.schemas.auth import MessageResponse
from app.schemas.platform import (
    ApiCredentialCreate,
    ApiCredentialCreated,
    ApiCredentialOut,
    AuditLogOut,
    EdgeDeviceHealthOut,
    GateHealthOut,
    IncidentAction,
    IncidentOut,
    LoginEventOut,
    SecurityAlertOut,
    ServiceHealthOut,
    SessionOut,
)
from app.services import health

router = APIRouter(prefix="/platform", tags=["platform-ops"], dependencies=[Depends(verify_csrf)])


# ------------------------------------------------------------------ monitoring


@router.get("/monitoring/services", response_model=list[ServiceHealthOut])
async def service_health(user: CurrentUser = Depends(require_platform_user)):
    return await health.all_service_health()


@router.get("/monitoring/edge-devices", response_model=Page[EdgeDeviceHealthOut])
async def edge_devices(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(EdgeDevice, Tenant.name.label("tenant_name")).join(Tenant, Tenant.id == EdgeDevice.tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(EdgeDevice.device_name).offset(page.offset).limit(page.page_size))
    ).all()
    items = [
        EdgeDeviceHealthOut(
            id=e.id,
            device_name=e.device_name,
            tenant_id=e.tenant_id,
            tenant_name=tname,
            status=e.status,
            cpu_percent=e.cpu_percent or 0,
            memory_percent=e.memory_percent or 0,
            disk_percent=e.disk_percent or 0,
            version=e.firmware_version,
            connected_cameras=e.connected_cameras,
            events_per_min=e.events_per_min,
            last_heartbeat=e.last_heartbeat_at,
        )
        for e, tname in rows
    ]
    return Page[EdgeDeviceHealthOut](items=items, total=total, page=page.page, page_size=page.page_size)


@router.get("/monitoring/gates", response_model=Page[GateHealthOut])
async def gates_health(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(BarrierGate, Tenant.name.label("tenant_name")).join(Tenant, Tenant.id == BarrierGate.tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(BarrierGate.name).offset(page.offset).limit(page.page_size))).all()
    items = [
        GateHealthOut(
            id=g.id,
            gate_name=g.name,
            tenant_id=g.tenant_id,
            tenant_name=tname,
            status=g.status,
            last_heartbeat=g.last_heartbeat_at,
        )
        for g, tname in rows
    ]
    return Page[GateHealthOut](items=items, total=total, page=page.page, page_size=page.page_size)


@router.get("/monitoring/incidents", response_model=Page[IncidentOut])
async def list_incidents(
    page: PageParams = Depends(),
    status: str | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(BarrierIncident, Tenant.name.label("tenant_name")).join(
        Tenant, Tenant.id == BarrierIncident.tenant_id
    )
    if status:
        q = q.where(BarrierIncident.status == status.upper())
    if severity:
        q = q.where(BarrierIncident.severity == severity.upper())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(
            q.order_by(BarrierIncident.started_at.desc()).offset(page.offset).limit(page.page_size)
        )
    ).all()
    items = [
        IncidentOut(
            id=i.id,
            title=i.title,
            severity=i.severity,
            status=i.status,
            resource_id=i.resource_id,
            resource_type=i.resource_type,
            tenant_id=i.tenant_id,
            tenant_name=tname,
            description=i.description,
            started_at=i.started_at,
            updated_at=i.updated_at,
            resolution_note=i.resolution_note,
            assigned_to=i.assigned_to,
        )
        for i, tname in rows
    ]
    return Page[IncidentOut](items=items, total=total, page=page.page, page_size=page.page_size)


@router.post("/monitoring/incidents/{incident_id}/acknowledge", response_model=IncidentOut)
async def acknowledge_incident(
    incident_id: uuid.UUID,
    body: IncidentAction,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    inc = await db.get(BarrierIncident, incident_id)
    if inc is None:
        raise errors.not_found("Incident", incident_id)
    inc.status = "ACKNOWLEDGED"
    inc.assigned_to = body.assigned_to or user.email
    inc.updated_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        category="MONITORING",
        action="OPERATIONAL_INCIDENT_ACKNOWLEDGED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="INCIDENT",
        resource_id=str(incident_id),
        resource_name=inc.title,
        ip_address=client_ip(request),
    )
    await db.commit()
    tenant_name = (await db.get(Tenant, inc.tenant_id)).name if inc.tenant_id else None
    return IncidentOut(
        id=inc.id,
        title=inc.title,
        severity=inc.severity,
        status=inc.status,
        resource_id=inc.resource_id,
        resource_type=inc.resource_type,
        tenant_id=inc.tenant_id,
        tenant_name=tenant_name,
        description=inc.description,
        started_at=inc.started_at,
        updated_at=inc.updated_at,
        resolution_note=inc.resolution_note,
        assigned_to=inc.assigned_to,
    )


@router.post("/monitoring/incidents/{incident_id}/resolve", response_model=IncidentOut)
async def resolve_incident(
    incident_id: uuid.UUID,
    body: IncidentAction,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    inc = await db.get(BarrierIncident, incident_id)
    if inc is None:
        raise errors.not_found("Incident", incident_id)
    inc.status = "RESOLVED"
    inc.resolution_note = body.note or "Resolved by Platform Administrator"
    inc.resolved_at = datetime.now(timezone.utc)
    inc.updated_at = inc.resolved_at
    await write_audit(
        db,
        category="MONITORING",
        action="OPERATIONAL_INCIDENT_RESOLVED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="INCIDENT",
        resource_id=str(incident_id),
        resource_name=inc.title,
        ip_address=client_ip(request),
    )
    await db.commit()
    tenant_name = (await db.get(Tenant, inc.tenant_id)).name if inc.tenant_id else None
    return IncidentOut(
        id=inc.id,
        title=inc.title,
        severity=inc.severity,
        status=inc.status,
        resource_id=inc.resource_id,
        resource_type=inc.resource_type,
        tenant_id=inc.tenant_id,
        tenant_name=tenant_name,
        description=inc.description,
        started_at=inc.started_at,
        updated_at=inc.updated_at,
        resolution_note=inc.resolution_note,
        assigned_to=inc.assigned_to,
    )


# ------------------------------------------------------------------ security


@router.get("/security/alerts", response_model=Page[SecurityAlertOut])
async def list_security_alerts(
    page: PageParams = Depends(),
    status: str | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(SecurityAlert)
    if status:
        q = q.where(SecurityAlert.status == status.upper())
    if severity:
        q = q.where(SecurityAlert.severity == severity.upper())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(
            q.order_by(SecurityAlert.detected_at.desc()).offset(page.offset).limit(page.page_size)
        )
    ).scalars()
    return Page[SecurityAlertOut](
        items=[SecurityAlertOut.model_validate(a) for a in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/security/alerts/{alert_id}/acknowledge", response_model=SecurityAlertOut)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    alert = await db.get(SecurityAlert, alert_id)
    if alert is None:
        raise errors.not_found("SecurityAlert", alert_id)
    alert.status = "ACKNOWLEDGED"
    await write_audit(
        db,
        category="SECURITY",
        action="SECURITY_ALERT_ACKNOWLEDGED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="SECURITY_ALERT",
        resource_id=str(alert_id),
        ip_address=client_ip(request),
    )
    await db.commit()
    return SecurityAlertOut.model_validate(alert)


@router.post("/security/alerts/{alert_id}/resolve", response_model=SecurityAlertOut)
async def resolve_alert(
    alert_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    alert = await db.get(SecurityAlert, alert_id)
    if alert is None:
        raise errors.not_found("SecurityAlert", alert_id)
    alert.status = "RESOLVED"
    await write_audit(
        db,
        category="SECURITY",
        action="SECURITY_ALERT_RESOLVED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="SECURITY_ALERT",
        resource_id=str(alert_id),
        ip_address=client_ip(request),
    )
    await db.commit()
    return SecurityAlertOut.model_validate(alert)


@router.get("/security/login-events", response_model=Page[LoginEventOut])
async def list_login_events(
    page: PageParams = Depends(),
    result: str | None = None,
    email: str | None = None,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(LoginEvent)
    if result:
        q = q.where(LoginEvent.result == result.upper())
    if email:
        q = q.where(LoginEvent.user_email == email.lower())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(LoginEvent.timestamp.desc()).offset(page.offset).limit(page.page_size))
    ).scalars()
    return Page[LoginEventOut](
        items=[LoginEventOut.model_validate(e) for e in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/security/sessions", response_model=Page[SessionOut])
async def list_sessions(
    page: PageParams = Depends(),
    user_id: uuid.UUID | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(UserSession)
    if user_id:
        q = q.where(UserSession.user_id == user_id)
    if active_only:
        q = q.where(UserSession.revoked_at.is_(None), UserSession.expires_at > datetime.now(timezone.utc))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(
            q.order_by(UserSession.last_active_at.desc()).offset(page.offset).limit(page.page_size)
        )
    ).scalars()
    return Page[SessionOut](
        items=[SessionOut.model_validate(s) for s in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/security/sessions/{session_id}/revoke", response_model=MessageResponse)
async def revoke_session(
    session_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    session = await db.get(UserSession, session_id)
    if session is None:
        raise errors.not_found("Session", session_id)
    session.revoked_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        category="SECURITY",
        action="SESSION_REVOKED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="SESSION",
        resource_id=str(session_id),
        resource_name=session.user_name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return MessageResponse(message="Session revoked")


@router.post("/security/users/{target_user_id}/revoke-sessions", response_model=MessageResponse)
async def revoke_user_sessions(
    target_user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    rows = (
        await db.execute(
            select(UserSession).where(UserSession.user_id == target_user_id, UserSession.revoked_at.is_(None))
        )
    ).scalars()
    now = datetime.now(timezone.utc)
    for s in rows:
        s.revoked_at = now
    await write_audit(
        db,
        category="SECURITY",
        action="ALL_USER_SESSIONS_REVOKED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="USER",
        resource_id=str(target_user_id),
        ip_address=client_ip(request),
    )
    await db.commit()
    return MessageResponse(message=f"Revoked {len(rows)} session(s)")


# ------------------------------------------------------------------ credentials


@router.get("/security/credentials", response_model=Page[ApiCredentialOut])
async def list_credentials(
    page: PageParams = Depends(),
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    total = (await db.execute(select(func.count()).select_from(ApiCredential))).scalar_one()
    rows = (
        await db.execute(
            select(ApiCredential)
            .order_by(ApiCredential.created_at.desc())
            .offset(page.offset)
            .limit(page.page_size)
        )
    ).scalars()
    return Page[ApiCredentialOut](
        items=[ApiCredentialOut.model_validate(c) for c in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/security/credentials", response_model=ApiCredentialCreated, status_code=201)
async def create_credential(
    body: ApiCredentialCreate,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    raw, prefix, digest = security.generate_api_key(
        {"PLATFORM_KEY": "plt", "EDGE_KEY": "edge", "INTEGRATION_SECRET": "sec", "SERVICE_ACCOUNT": "svc"}[
            body.type
        ]
    )
    cred = ApiCredential(
        name=body.name,
        type=body.type,
        owner_name=body.owner_name,
        key_prefix=prefix,
        key_hash=digest,
        expires_at=body.expires_at,
    )
    db.add(cred)
    await db.flush()
    await write_audit(
        db,
        category="CREDENTIAL",
        action="API_CREDENTIAL_CREATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="CREDENTIAL",
        resource_id=str(cred.id),
        resource_name=cred.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return ApiCredentialCreated(credential=ApiCredentialOut.model_validate(cred), plaintext_key=raw)


@router.post("/security/credentials/{cred_id}/rotate", response_model=ApiCredentialCreated)
async def rotate_credential(
    cred_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    cred = await db.get(ApiCredential, cred_id)
    if cred is None:
        raise errors.not_found("ApiCredential", cred_id)
    raw, prefix, digest = security.generate_api_key(cred.key_prefix.split("_")[0] or "vmp")
    cred.key_prefix = prefix
    cred.key_hash = digest
    cred.status = "ACTIVE"
    cred.created_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        category="CREDENTIAL",
        action="API_CREDENTIAL_ROTATED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="CREDENTIAL",
        resource_id=str(cred_id),
        resource_name=cred.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return ApiCredentialCreated(credential=ApiCredentialOut.model_validate(cred), plaintext_key=raw)


@router.post("/security/credentials/{cred_id}/revoke", response_model=ApiCredentialOut)
async def revoke_credential(
    cred_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    cred = await db.get(ApiCredential, cred_id)
    if cred is None:
        raise errors.not_found("ApiCredential", cred_id)
    cred.status = "REVOKED"
    await write_audit(
        db,
        category="CREDENTIAL",
        action="API_CREDENTIAL_REVOKED",
        actor_type="PLATFORM_ADMIN",
        actor_id=user.user_id,
        actor_email=user.email,
        resource_type="CREDENTIAL",
        resource_id=str(cred_id),
        resource_name=cred.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return ApiCredentialOut.model_validate(cred)


# ------------------------------------------------------------------ audit


@router.get("/audit/logs", response_model=Page[AuditLogOut])
async def list_audit_logs(
    page: PageParams = Depends(),
    category: str | None = None,
    action: str | None = None,
    actor_email: str | None = None,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(AuditLog)
    if category:
        q = q.where(AuditLog.category == category.upper())
    if action:
        q = q.where(AuditLog.action == action.upper())
    if actor_email:
        q = q.where(AuditLog.actor_email == actor_email.lower())
    if tenant_id:
        q = q.where(AuditLog.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(AuditLog.timestamp.desc()).offset(page.offset).limit(page.page_size))
    ).scalars()
    return Page[AuditLogOut](
        items=[AuditLogOut.model_validate(a) for a in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/audit/export")
async def export_audit_logs(
    category: str | None = None,
    db: AsyncSession = Depends(platform_db),
    user: CurrentUser = Depends(require_platform_user),
):
    q = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50_000)
    if category:
        q = q.where(AuditLog.category == category.upper())
    rows = (await db.execute(q)).scalars()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "timestamp",
            "category",
            "action",
            "actorEmail",
            "actorType",
            "tenantName",
            "resourceType",
            "resourceId",
            "result",
            "source",
            "ipAddress",
        ]
    )
    for a in rows:
        writer.writerow(
            [
                a.id,
                a.timestamp.isoformat(),
                a.category,
                a.action,
                a.actor_email,
                a.actor_type,
                a.tenant_name,
                a.resource_type,
                a.resource_id,
                a.result,
                a.source,
                a.ip_address,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-log-export.csv"'},
    )
