"""Schemas for the tenant-facing surface (sites, gates, vehicles, events)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel, StrIp

# ------------------------------------------------------------------ users


class TenantUserOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    role: str
    status: str
    mfa_enabled: bool
    invited_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime


class TenantUserCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = None
    role: Literal["TENANT_ADMIN", "OPERATOR", "VIEWER", "MEMBER"] = "MEMBER"
    password: str | None = Field(default=None, min_length=12, max_length=256)


class TenantUserUpdate(CamelModel):
    name: str | None = None
    phone: str | None = None
    role: Literal["TENANT_ADMIN", "OPERATOR", "VIEWER", "MEMBER"] | None = None
    status: Literal["ACTIVE", "INVITED", "DISABLED"] | None = None


# ------------------------------------------------------------------ sites / lanes / gates


class SiteOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    address: str | None = None
    timezone: str
    status: str
    created_at: datetime


class SiteCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    address: str | None = None
    timezone: str = "Asia/Ho_Chi_Minh"


class SiteUpdate(CamelModel):
    name: str | None = None
    address: str | None = None
    timezone: str | None = None
    status: Literal["ACTIVE", "DISABLED"] | None = None


class LaneOut(CamelModel):
    id: uuid.UUID
    site_id: uuid.UUID
    name: str
    direction: str


class LaneCreate(CamelModel):
    name: str = Field(min_length=1, max_length=128)
    direction: Literal["INBOUND", "OUTBOUND", "BIDIRECTIONAL"] = "INBOUND"


class EdgeDeviceOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    site_id: uuid.UUID | None = None
    device_name: str
    serial: str | None = None
    firmware_version: str | None = None
    status: str
    ip_address: StrIp | None = None
    mac_address: StrIp | None = None
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    connected_cameras: int = 0
    events_per_min: int = 0
    last_heartbeat_at: datetime | None = None


class EdgeDeviceCreate(CamelModel):
    device_name: str = Field(min_length=1, max_length=128)
    site_id: uuid.UUID | None = None
    serial: str | None = None
    firmware_version: str | None = None


class GateOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    site_id: uuid.UUID
    lane_id: uuid.UUID | None = None
    edge_device_id: uuid.UUID | None = None
    name: str
    gate_type: str
    status: str
    state: str
    controller_address: str | None = None
    last_heartbeat_at: datetime | None = None
    created_at: datetime


class GateCreate(CamelModel):
    name: str = Field(min_length=1, max_length=128)
    site_id: uuid.UUID
    lane_id: uuid.UUID | None = None
    edge_device_id: uuid.UUID | None = None
    gate_type: str = "BARRIER"
    controller_address: str | None = None


class GateUpdate(CamelModel):
    name: str | None = None
    lane_id: uuid.UUID | None = None
    edge_device_id: uuid.UUID | None = None
    controller_address: str | None = None


# ------------------------------------------------------------------ vehicles


class VehicleOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    plate_raw: str
    plate_normalized: str
    owner_name: str | None = None
    owner_type: str
    brand_model: str | None = None
    color: str | None = None
    status: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    created_at: datetime


class VehicleCreate(CamelModel):
    plate: str = Field(min_length=1, max_length=32)
    owner_name: str | None = None
    owner_type: str = "STAFF"
    brand_model: str | None = None
    color: str | None = None
    status: Literal["ACTIVE", "SUSPENDED", "BLACKLISTED"] = "ACTIVE"
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class VehicleUpdate(CamelModel):
    owner_name: str | None = None
    owner_type: str | None = None
    brand_model: str | None = None
    color: str | None = None
    status: Literal["ACTIVE", "SUSPENDED", "BLACKLISTED"] | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class ImportJobOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    error_rows: int
    errors: list = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None = None


# ------------------------------------------------------------------ rules


class AccessRuleOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None = None
    rule_type: str
    priority: int
    plate_pattern: str | None = None
    vehicle_id: uuid.UUID | None = None
    gate_id: uuid.UUID | None = None
    schedule: dict | None = None
    enabled: bool


class AccessRuleCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    rule_type: Literal["ALLOW", "DENY", "SCHEDULE"] = "ALLOW"
    priority: int = 100
    plate_pattern: str | None = None
    vehicle_id: uuid.UUID | None = None
    gate_id: uuid.UUID | None = None
    schedule: dict | None = None
    enabled: bool = True


class AccessRuleUpdate(CamelModel):
    name: str | None = None
    description: str | None = None
    rule_type: Literal["ALLOW", "DENY", "SCHEDULE"] | None = None
    priority: int | None = None
    plate_pattern: str | None = None
    gate_id: uuid.UUID | None = None
    schedule: dict | None = None
    enabled: bool | None = None


# ------------------------------------------------------------------ access events / telemetry


class AccessEventOut(CamelModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    site_id: uuid.UUID | None = None
    lane_id: uuid.UUID | None = None
    gate_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    plate_raw: str | None = None
    plate_normalized: str | None = None
    direction: str
    decision: str
    decision_reason: str | None = None
    occurred_at: datetime
    plate_image_url: str | None = None
    overview_image_url: str | None = None
    snapshot: dict | None = None


class TelemetryOut(CamelModel):
    id: uuid.UUID | None = None
    gate_id: uuid.UUID | None = None
    site_id: uuid.UUID | None = None
    recorded_at: datetime
    metrics: dict = Field(default_factory=dict)
    source: str = "EDGE"


# ------------------------------------------------------------------ barrier control


class GateCommandCreate(CamelModel):
    command: Literal["OPEN", "CLOSE", "LOCK", "UNLOCK"]
    idempotency_key: str = Field(min_length=4, max_length=128)


class GateCommandOut(CamelModel):
    id: uuid.UUID
    gate_id: uuid.UUID
    command: str
    status: str
    idempotency_key: str
    issued_at: datetime
    dispatched_at: datetime | None = None
    acked_at: datetime | None = None
    executed_at: datetime | None = None
    response: dict | None = None


# ------------------------------------------------------------------ incidents


class IncidentCreate(CamelModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    site_id: uuid.UUID | None = None
    gate_id: uuid.UUID | None = None
    resource_type: str | None = None
    resource_id: str | None = None


class IncidentUpdate(CamelModel):
    status: Literal["OPEN", "ACKNOWLEDGED", "RESOLVED"] | None = None
    resolution_note: str | None = None
    assigned_to: str | None = None
