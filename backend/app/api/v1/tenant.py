"""Tenant-facing API: sites, lanes, gates, users, vehicles, rules, events, barrier control."""

import csv
import io
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import errors
from app.core.audit import write_audit
from app.core.deps import (
    CurrentUser,
    get_current_user,
    require_tenant_admin,
    tenant_db,
    verify_csrf,
)
from app.core.pagination import Page, PageParams
from app.core.security import client_ip, hash_password
from app.models import (
    AccessEvent,
    AccessRule,
    BarrierGate,
    BarrierIncident,
    EdgeDevice,
    GateCommand,
    GateTelemetryLog,
    RegisteredVehicle,
    Site,
    SiteLane,
    TenantUser,
    VehicleImportJob,
)
from app.realtime import mqtt as mqtt_client
from app.schemas.auth import MessageResponse
from app.schemas.platform import IncidentOut as IncidentOutSchema
from app.schemas.tenant import (
    AccessEventOut,
    AccessRuleCreate,
    AccessRuleOut,
    AccessRuleUpdate,
    EdgeDeviceCreate,
    EdgeDeviceOut,
    GateCommandCreate,
    GateCommandOut,
    GateCreate,
    GateOut,
    GateUpdate,
    ImportJobOut,
    IncidentCreate,
    IncidentUpdate,
    LaneCreate,
    LaneOut,
    SiteCreate,
    SiteOut,
    SiteUpdate,
    TelemetryOut,
    TenantUserCreate,
    TenantUserOut,
    TenantUserUpdate,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
)

router = APIRouter(
    prefix="/tenants/{tenant_id}",
    tags=["tenant"],
    dependencies=[Depends(verify_csrf)],
)

PLATE_RE = re.compile(r"[^A-Z0-9]")


def normalize_plate(raw: str) -> str:
    return PLATE_RE.sub("", raw.upper())


def _audit_actor(user: CurrentUser) -> dict:
    return {
        "actor_type": user.user_type,
        "actor_id": user.user_id,
        "actor_name": user.name,
        "actor_email": user.email,
    }


# ================================================================== SITES / LANES / GATES


@router.get("/sites", response_model=Page[SiteOut])
async def list_sites(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    db: AsyncSession = Depends(tenant_db),
):
    q = select(Site).where(Site.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(page.offset).limit(page.page_size))).scalars()
    return Page[SiteOut](
        items=[SiteOut.model_validate(s) for s in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/sites", response_model=SiteOut, status_code=201)
async def create_site(
    tenant_id: uuid.UUID,
    body: SiteCreate,
    request: Request,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(get_current_user),
):
    site = Site(
        tenant_id=tenant_id,
        name=body.name,
        code=body.code.upper(),
        address=body.address,
        timezone=body.timezone,
    )
    db.add(site)
    await db.flush()
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="SITE_CREATED",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="SITE",
        resource_id=str(site.id),
        resource_name=site.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return SiteOut.model_validate(site)


@router.get("/sites/{site_id}", response_model=SiteOut)
async def get_site(tenant_id: uuid.UUID, site_id: uuid.UUID, db: AsyncSession = Depends(tenant_db)):
    site = await db.get(Site, site_id)
    if site is None or site.tenant_id != tenant_id:
        raise errors.not_found("Site", site_id)
    return SiteOut.model_validate(site)


@router.patch("/sites/{site_id}", response_model=SiteOut)
async def update_site(
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    body: SiteUpdate,
    db: AsyncSession = Depends(tenant_db),
):
    site = await db.get(Site, site_id)
    if site is None or site.tenant_id != tenant_id:
        raise errors.not_found("Site", site_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(site, k, v)
    await db.commit()
    return SiteOut.model_validate(site)


@router.get("/sites/{site_id}/lanes", response_model=list[LaneOut])
async def list_lanes(tenant_id: uuid.UUID, site_id: uuid.UUID, db: AsyncSession = Depends(tenant_db)):
    rows = (
        await db.execute(select(SiteLane).where(SiteLane.site_id == site_id, SiteLane.tenant_id == tenant_id))
    ).scalars()
    return [LaneOut.model_validate(lane) for lane in rows]


@router.post("/sites/{site_id}/lanes", response_model=LaneOut, status_code=201)
async def create_lane(
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    body: LaneCreate,
    db: AsyncSession = Depends(tenant_db),
):
    if await db.get(Site, site_id) is None:
        raise errors.not_found("Site", site_id)
    lane = SiteLane(tenant_id=tenant_id, site_id=site_id, name=body.name, direction=body.direction)
    db.add(lane)
    await db.commit()
    return LaneOut.model_validate(lane)


@router.get("/gates", response_model=Page[GateOut])
async def list_gates(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    site_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(tenant_db),
):
    q = select(BarrierGate).where(BarrierGate.tenant_id == tenant_id)
    if site_id:
        q = q.where(BarrierGate.site_id == site_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(page.offset).limit(page.page_size))).scalars()
    return Page[GateOut](
        items=[GateOut.model_validate(g) for g in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/gates", response_model=GateOut, status_code=201)
async def create_gate(
    tenant_id: uuid.UUID,
    body: GateCreate,
    request: Request,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(get_current_user),
):
    site = await db.get(Site, body.site_id)
    if site is None or site.tenant_id != tenant_id:
        raise errors.not_found("Site", body.site_id)
    gate = BarrierGate(
        tenant_id=tenant_id,
        site_id=body.site_id,
        lane_id=body.lane_id,
        edge_device_id=body.edge_device_id,
        name=body.name,
        gate_type=body.gate_type,
        controller_address=body.controller_address,
    )
    db.add(gate)
    await db.flush()
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="GATE_CREATED",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="GATE",
        resource_id=str(gate.id),
        resource_name=gate.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return GateOut.model_validate(gate)


@router.patch("/gates/{gate_id}", response_model=GateOut)
async def update_gate(
    tenant_id: uuid.UUID,
    gate_id: uuid.UUID,
    body: GateUpdate,
    db: AsyncSession = Depends(tenant_db),
):
    gate = await db.get(BarrierGate, gate_id)
    if gate is None or gate.tenant_id != tenant_id:
        raise errors.not_found("Gate", gate_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(gate, k, v)
    await db.commit()
    return GateOut.model_validate(gate)


@router.get("/edge-devices", response_model=Page[EdgeDeviceOut])
async def list_edge_devices(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    db: AsyncSession = Depends(tenant_db),
):
    q = select(EdgeDevice).where(EdgeDevice.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(page.offset).limit(page.page_size))).scalars()
    return Page[EdgeDeviceOut](
        items=[EdgeDeviceOut.model_validate(e) for e in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/edge-devices", response_model=EdgeDeviceOut, status_code=201)
async def register_edge_device(
    tenant_id: uuid.UUID,
    body: EdgeDeviceCreate,
    db: AsyncSession = Depends(tenant_db),
):
    device = EdgeDevice(
        tenant_id=tenant_id,
        site_id=body.site_id,
        device_name=body.device_name,
        serial=body.serial,
        firmware_version=body.firmware_version,
        status="OFFLINE",
    )
    db.add(device)
    await db.commit()
    return EdgeDeviceOut.model_validate(device)


# ================================================================== USERS


@router.get("/users", response_model=Page[TenantUserOut])
async def list_users(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    db: AsyncSession = Depends(tenant_db),
):
    q = select(TenantUser).where(TenantUser.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(TenantUser.created_at).offset(page.offset).limit(page.page_size))
    ).scalars()
    return Page[TenantUserOut](
        items=[TenantUserOut.model_validate(u) for u in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/users", response_model=TenantUserOut, status_code=201)
async def create_user(
    tenant_id: uuid.UUID,
    body: TenantUserCreate,
    request: Request,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(require_tenant_admin),
):
    if (
        await db.execute(
            select(func.count())
            .select_from(TenantUser)
            .where(TenantUser.tenant_id == tenant_id, TenantUser.email == body.email.lower())
        )
    ).scalar_one():
        raise errors.conflict("EMAIL_EXISTS", "A user with this email already exists in the tenant")
    obj = TenantUser(
        tenant_id=tenant_id,
        name=body.name,
        email=body.email.lower(),
        phone=body.phone,
        role=body.role,
        status="ACTIVE" if body.password else "INVITED",
        password_hash=hash_password(body.password) if body.password else None,
        invited_at=datetime.now(timezone.utc),
    )
    db.add(obj)
    await db.flush()
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="TENANT_USER_CREATED",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="USER",
        resource_id=str(obj.id),
        resource_name=obj.name,
        ip_address=client_ip(request),
    )
    await db.commit()
    return TenantUserOut.model_validate(obj)


@router.patch("/users/{user_id}", response_model=TenantUserOut)
async def update_user(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    body: TenantUserUpdate,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(require_tenant_admin),
):
    obj = await db.get(TenantUser, user_id)
    if obj is None or obj.tenant_id != tenant_id:
        raise errors.not_found("TenantUser", user_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    await db.commit()
    return TenantUserOut.model_validate(obj)


# ================================================================== VEHICLES


@router.get("/vehicles", response_model=Page[VehicleOut])
async def list_vehicles(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    plate: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(tenant_db),
):
    q = select(RegisteredVehicle).where(RegisteredVehicle.tenant_id == tenant_id)
    if plate:
        q = q.where(RegisteredVehicle.plate_normalized.contains(normalize_plate(plate)))
    if status:
        q = q.where(RegisteredVehicle.status == status.upper())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(
            q.order_by(RegisteredVehicle.created_at.desc()).offset(page.offset).limit(page.page_size)
        )
    ).scalars()
    return Page[VehicleOut](
        items=[VehicleOut.model_validate(v) for v in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
async def create_vehicle(
    tenant_id: uuid.UUID,
    body: VehicleCreate,
    request: Request,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(get_current_user),
):
    norm = normalize_plate(body.plate)
    if not norm:
        raise errors.ApiError("VALIDATION", "License plate is empty after normalization", 422)
    exists = (
        await db.execute(
            select(func.count())
            .select_from(RegisteredVehicle)
            .where(
                RegisteredVehicle.tenant_id == tenant_id,
                RegisteredVehicle.plate_normalized == norm,
            )
        )
    ).scalar_one()
    if exists:
        raise errors.conflict("PLATE_EXISTS", f"Vehicle {norm} already registered")
    vehicle = RegisteredVehicle(
        tenant_id=tenant_id,
        plate_raw=body.plate,
        plate_normalized=norm,
        owner_name=body.owner_name,
        owner_type=body.owner_type,
        brand_model=body.brand_model,
        color=body.color,
        status=body.status,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
    )
    db.add(vehicle)
    await db.flush()
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="VEHICLE_REGISTERED",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="VEHICLE",
        resource_id=str(vehicle.id),
        resource_name=norm,
        ip_address=client_ip(request),
    )
    await db.commit()
    return VehicleOut.model_validate(vehicle)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(tenant_id: uuid.UUID, vehicle_id: uuid.UUID, db: AsyncSession = Depends(tenant_db)):
    v = await db.get(RegisteredVehicle, vehicle_id)
    if v is None or v.tenant_id != tenant_id:
        raise errors.not_found("Vehicle", vehicle_id)
    return VehicleOut.model_validate(v)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    tenant_id: uuid.UUID, vehicle_id: uuid.UUID, body: VehicleUpdate, db: AsyncSession = Depends(tenant_db)
):
    v = await db.get(RegisteredVehicle, vehicle_id)
    if v is None or v.tenant_id != tenant_id:
        raise errors.not_found("Vehicle", vehicle_id)
    for k, val in body.model_dump(exclude_none=True).items():
        setattr(v, k, val)
    await db.commit()
    return VehicleOut.model_validate(v)


@router.delete("/vehicles/{vehicle_id}", response_model=MessageResponse)
async def delete_vehicle(tenant_id: uuid.UUID, vehicle_id: uuid.UUID, db: AsyncSession = Depends(tenant_db)):
    v = await db.get(RegisteredVehicle, vehicle_id)
    if v is None or v.tenant_id != tenant_id:
        raise errors.not_found("Vehicle", vehicle_id)
    await db.delete(v)
    await db.commit()
    return MessageResponse(message="Vehicle removed")


@router.post("/vehicles:import", response_model=ImportJobOut, status_code=202)
async def import_vehicles(
    tenant_id: uuid.UUID,
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(require_tenant_admin),
):
    """CSV bulk import — parsed inline for small files, queued for larger ones.

    CSV columns: plate, owner_name, owner_type, brand_model, color, status,
    valid_from, valid_until
    """

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise errors.ApiError("PAYLOAD_TOO_LARGE", "CSV exceeds 10MB", 413)
    job = VehicleImportJob(
        tenant_id=tenant_id, filename=file.filename or "upload.csv", status="RUNNING", created_by=user.user_id
    )
    db.add(job)
    await db.flush()

    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    job.total_rows = 0
    errs: list[dict] = []
    for idx, row in enumerate(reader, start=1):
        job.total_rows += 1
        plate = (row.get("plate") or "").strip()
        if not plate:
            errs.append({"row": idx, "error": "missing plate"})
            continue
        norm = normalize_plate(plate)
        exists = (
            await db.execute(
                select(func.count())
                .select_from(RegisteredVehicle)
                .where(
                    RegisteredVehicle.tenant_id == tenant_id,
                    RegisteredVehicle.plate_normalized == norm,
                )
            )
        ).scalar_one()
        if exists:
            job.error_rows += 1
            errs.append({"row": idx, "error": f"duplicate plate {norm}"})
            continue
        db.add(
            RegisteredVehicle(
                tenant_id=tenant_id,
                plate_raw=plate,
                plate_normalized=norm,
                owner_name=row.get("owner_name") or None,
                owner_type=(row.get("owner_type") or "STAFF").upper(),
                brand_model=row.get("brand_model") or None,
                color=row.get("color") or None,
                status=(row.get("status") or "ACTIVE").upper(),
            )
        )
        job.processed_rows += 1
    job.errors = errs[:500]
    job.status = "COMPLETED" if not errs else ("FAILED" if job.processed_rows == 0 else "COMPLETED")
    job.completed_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        category="TENANT_MANAGEMENT",
        action="VEHICLE_BULK_IMPORT",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="IMPORT",
        resource_id=str(job.id),
        resource_name=job.filename,
        ip_address=client_ip(request),
        metadata={"processed": job.processed_rows, "errors": job.error_rows},
    )
    await db.commit()
    return ImportJobOut.model_validate(job)


@router.get("/vehicles:imports/{job_id}", response_model=ImportJobOut)
async def get_import_job(tenant_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(tenant_db)):
    job = await db.get(VehicleImportJob, job_id)
    if job is None or job.tenant_id != tenant_id:
        raise errors.not_found("ImportJob", job_id)
    return ImportJobOut.model_validate(job)


# ================================================================== ACCESS RULES


@router.get("/access-rules", response_model=Page[AccessRuleOut])
async def list_rules(
    tenant_id: uuid.UUID, page: PageParams = Depends(), db: AsyncSession = Depends(tenant_db)
):
    q = select(AccessRule).where(AccessRule.tenant_id == tenant_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(AccessRule.priority).offset(page.offset).limit(page.page_size))
    ).scalars()
    return Page[AccessRuleOut](
        items=[AccessRuleOut.model_validate(r) for r in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/access-rules", response_model=AccessRuleOut, status_code=201)
async def create_rule(tenant_id: uuid.UUID, body: AccessRuleCreate, db: AsyncSession = Depends(tenant_db)):
    rule = AccessRule(tenant_id=tenant_id, **body.model_dump())
    db.add(rule)
    await db.commit()
    return AccessRuleOut.model_validate(rule)


@router.patch("/access-rules/{rule_id}", response_model=AccessRuleOut)
async def update_rule(
    tenant_id: uuid.UUID, rule_id: uuid.UUID, body: AccessRuleUpdate, db: AsyncSession = Depends(tenant_db)
):
    rule = await db.get(AccessRule, rule_id)
    if rule is None or rule.tenant_id != tenant_id:
        raise errors.not_found("AccessRule", rule_id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(rule, k, v)
    await db.commit()
    return AccessRuleOut.model_validate(rule)


@router.delete("/access-rules/{rule_id}", response_model=MessageResponse)
async def delete_rule(tenant_id: uuid.UUID, rule_id: uuid.UUID, db: AsyncSession = Depends(tenant_db)):
    rule = await db.get(AccessRule, rule_id)
    if rule is None or rule.tenant_id != tenant_id:
        raise errors.not_found("AccessRule", rule_id)
    await db.delete(rule)
    await db.commit()
    return MessageResponse(message="Rule deleted")


# ================================================================== ACCESS EVENTS & TELEMETRY


@router.get("/access-events", response_model=Page[AccessEventOut])
async def list_access_events(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    gate_id: uuid.UUID | None = None,
    plate: str | None = None,
    decision: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    db: AsyncSession = Depends(tenant_db),
):
    q = select(AccessEvent).where(AccessEvent.tenant_id == tenant_id)
    if gate_id:
        q = q.where(AccessEvent.gate_id == gate_id)
    if plate:
        q = q.where(AccessEvent.plate_normalized == normalize_plate(plate))
    if decision:
        q = q.where(AccessEvent.decision == decision.upper())
    if since:
        q = q.where(AccessEvent.occurred_at >= since)
    if until:
        q = q.where(AccessEvent.occurred_at <= until)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(AccessEvent.occurred_at.desc()).offset(page.offset).limit(page.page_size))
    ).scalars()
    return Page[AccessEventOut](
        items=[AccessEventOut.model_validate(e) for e in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/gates/{gate_id}/telemetry", response_model=Page[TelemetryOut])
async def gate_telemetry(
    tenant_id: uuid.UUID,
    gate_id: uuid.UUID,
    page: PageParams = Depends(),
    since: datetime | None = None,
    db: AsyncSession = Depends(tenant_db),
):
    q = select(GateTelemetryLog).where(
        GateTelemetryLog.tenant_id == tenant_id, GateTelemetryLog.gate_id == gate_id
    )
    if since:
        q = q.where(GateTelemetryLog.recorded_at >= since)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(
            q.order_by(GateTelemetryLog.recorded_at.desc()).offset(page.offset).limit(page.page_size)
        )
    ).scalars()
    return Page[TelemetryOut](
        items=[TelemetryOut.model_validate(t) for t in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


# ================================================================== BARRIER CONTROL


@router.post("/gates/{gate_id}/commands", response_model=GateCommandOut, status_code=202)
async def issue_gate_command(
    tenant_id: uuid.UUID,
    gate_id: uuid.UUID,
    body: GateCommandCreate,
    request: Request,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(require_tenant_admin),
):
    gate = await db.get(BarrierGate, gate_id)
    if gate is None or gate.tenant_id != tenant_id:
        raise errors.not_found("Gate", gate_id)

    existing = (
        await db.execute(
            select(GateCommand).where(
                GateCommand.tenant_id == tenant_id, GateCommand.idempotency_key == body.idempotency_key
            )
        )
    ).scalar_one_or_none()
    if existing:
        return GateCommandOut.model_validate(existing)

    cmd = GateCommand(
        tenant_id=tenant_id,
        site_id=gate.site_id,
        gate_id=gate_id,
        idempotency_key=body.idempotency_key,
        command=body.command,
        status="PENDING",
        issued_by_id=user.user_id,
        issued_by_name=user.name,
    )
    db.add(cmd)
    await db.flush()
    try:
        await mqtt_client.publish_command(
            str(tenant_id),
            str(gate.site_id),
            str(gate_id),
            {
                "commandId": str(cmd.id),
                "command": body.command,
                "issuedAt": cmd.issued_at.isoformat() if cmd.issued_at else None,
            },
        )
        cmd.status = "DISPATCHED"
        cmd.dispatched_at = datetime.now(timezone.utc)
    except Exception:
        cmd.status = "FAILED"
        cmd.response = {"error": "MQTT publish failed"}
    await write_audit(
        db,
        category="MONITORING",
        action=f"GATE_COMMAND_{body.command}",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="GATE",
        resource_id=str(gate_id),
        resource_name=gate.name,
        ip_address=client_ip(request),
        metadata={"commandId": str(cmd.id), "status": cmd.status},
    )
    await db.commit()
    return GateCommandOut.model_validate(cmd)


@router.get("/gates/{gate_id}/commands", response_model=Page[GateCommandOut])
async def list_gate_commands(
    tenant_id: uuid.UUID,
    gate_id: uuid.UUID,
    page: PageParams = Depends(),
    db: AsyncSession = Depends(tenant_db),
):
    q = select(GateCommand).where(GateCommand.tenant_id == tenant_id, GateCommand.gate_id == gate_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(q.order_by(GateCommand.issued_at.desc()).offset(page.offset).limit(page.page_size))
    ).scalars()
    return Page[GateCommandOut](
        items=[GateCommandOut.model_validate(c) for c in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


# ================================================================== INCIDENTS


@router.get("/incidents", response_model=Page[IncidentOutSchema])
async def list_tenant_incidents(
    tenant_id: uuid.UUID,
    page: PageParams = Depends(),
    status: str | None = None,
    db: AsyncSession = Depends(tenant_db),
):
    q = select(BarrierIncident).where(BarrierIncident.tenant_id == tenant_id)
    if status:
        q = q.where(BarrierIncident.status == status.upper())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (
        await db.execute(
            q.order_by(BarrierIncident.started_at.desc()).offset(page.offset).limit(page.page_size)
        )
    ).scalars()
    return Page[IncidentOutSchema](
        items=[IncidentOutSchema.model_validate(i) for i in rows],
        total=total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/incidents", response_model=IncidentOutSchema, status_code=201)
async def create_tenant_incident(
    tenant_id: uuid.UUID,
    body: IncidentCreate,
    request: Request,
    db: AsyncSession = Depends(tenant_db),
    user: CurrentUser = Depends(get_current_user),
):
    inc = BarrierIncident(
        tenant_id=tenant_id,
        site_id=body.site_id,
        gate_id=body.gate_id,
        title=body.title,
        description=body.description,
        severity=body.severity,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        status="OPEN",
    )
    db.add(inc)
    await db.flush()
    await write_audit(
        db,
        category="MONITORING",
        action="INCIDENT_REPORTED",
        **_audit_actor(user),
        tenant_id=tenant_id,
        resource_type="INCIDENT",
        resource_id=str(inc.id),
        resource_name=inc.title,
        ip_address=client_ip(request),
    )
    await db.commit()
    return IncidentOutSchema.model_validate(inc)


@router.patch("/incidents/{incident_id}", response_model=IncidentOutSchema)
async def update_tenant_incident(
    tenant_id: uuid.UUID,
    incident_id: uuid.UUID,
    body: IncidentUpdate,
    db: AsyncSession = Depends(tenant_db),
):
    inc = await db.get(BarrierIncident, incident_id)
    if inc is None or inc.tenant_id != tenant_id:
        raise errors.not_found("Incident", incident_id)
    if body.status:
        inc.status = body.status
        if body.status == "RESOLVED":
            inc.resolved_at = datetime.now(timezone.utc)
    if body.resolution_note is not None:
        inc.resolution_note = body.resolution_note
    if body.assigned_to is not None:
        inc.assigned_to = body.assigned_to
    inc.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return IncidentOutSchema.model_validate(inc)
