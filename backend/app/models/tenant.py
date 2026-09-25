"""Tenant-scoped entities. Every table carries ``tenant_id`` for RLS isolation."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import INET, JSONB, MACADDR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class TenantUser(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tenant_users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_tenant_users_email"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(
        String(32), default="MEMBER", nullable=False
    )  # TENANT_ADMIN|OPERATOR|VIEWER|MEMBER
    status: Mapped[str] = mapped_column(String(16), default="INVITED", nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_enc: Mapped[str | None] = mapped_column(Text)
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")  # noqa: F821


class Site(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tenant_sites"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_sites_code"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Ho_Chi_Minh")
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)

    lanes: Mapped[list["SiteLane"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    gates: Mapped[list["BarrierGate"]] = relationship(back_populates="site", cascade="all, delete-orphan")


class EdgeDevice(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "edge_devices"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_sites.id", ondelete="SET NULL"), index=True
    )
    device_name: Mapped[str] = mapped_column(String(128), nullable=False)
    serial: Mapped[str | None] = mapped_column(String(128))
    firmware_version: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="OFFLINE", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET)
    mac_address: Mapped[str | None] = mapped_column(MACADDR)
    cpu_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    memory_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    disk_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    connected_cameras: Mapped[int] = mapped_column(Integer, default=0)
    events_per_min: Mapped[int] = mapped_column(Integer, default=0)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SiteLane(UUIDPrimaryKey, Base):
    __tablename__ = "site_lanes"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_sites.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), default="INBOUND", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site: Mapped[Site] = relationship(back_populates="lanes")


class BarrierGate(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "barrier_gates"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_sites.id", ondelete="CASCADE"), index=True
    )
    lane_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site_lanes.id", ondelete="SET NULL")
    )
    edge_device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edge_devices.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    gate_type: Mapped[str] = mapped_column(String(32), default="BARRIER")
    status: Mapped[str] = mapped_column(String(16), default="OFFLINE", nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    controller_address: Mapped[str | None] = mapped_column(String(128))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    site: Mapped[Site] = relationship(back_populates="gates")


class GateTelemetryLog(Base):
    """Monthly-partitioned gate telemetry (PK includes partition key)."""

    __tablename__ = "gate_telemetry_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    gate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, server_default=func.now()
    )
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    source: Mapped[str] = mapped_column(String(16), default="EDGE")


class BarrierIncident(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "barrier_incidents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_sites.id", ondelete="SET NULL"), index=True
    )
    gate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("barrier_gates.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="OPEN", nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(32))
    resource_id: Mapped[str | None] = mapped_column(String(128))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[str | None] = mapped_column(String(255))


class RegisteredVehicle(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "registered_vehicles"
    __table_args__ = (UniqueConstraint("tenant_id", "plate_normalized", name="uq_vehicles_plate"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    plate_raw: Mapped[str] = mapped_column(String(32), nullable=False)
    plate_normalized: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(255))
    owner_type: Mapped[str] = mapped_column(String(32), default="STAFF")
    brand_model: Mapped[str | None] = mapped_column(String(128))
    color: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccessRule(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tenant_access_rules"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rule_type: Mapped[str] = mapped_column(String(16), default="ALLOW", nullable=False)  # ALLOW|DENY|SCHEDULE
    priority: Mapped[int] = mapped_column(Integer, default=100)
    plate_pattern: Mapped[str | None] = mapped_column(String(64))
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("registered_vehicles.id", ondelete="CASCADE")
    )
    gate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("barrier_gates.id", ondelete="CASCADE")
    )
    schedule: Mapped[dict | None] = mapped_column(JSONB)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AccessEvent(Base):
    """Quarterly-partitioned access events (PK includes partition key)."""

    __tablename__ = "access_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lane_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    gate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    edge_device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    plate_raw: Mapped[str | None] = mapped_column(String(32))
    plate_normalized: Mapped[str | None] = mapped_column(String(32), index=True)
    direction: Mapped[str] = mapped_column(String(16), default="INBOUND")
    decision: Mapped[str] = mapped_column(String(16), default="ALLOWED")
    decision_reason: Mapped[str | None] = mapped_column(String(255))
    rule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, server_default=func.now()
    )
    plate_image_url: Mapped[str | None] = mapped_column(String(512))
    overview_image_url: Mapped[str | None] = mapped_column(String(512))
    snapshot: Mapped[dict | None] = mapped_column(JSONB)


class GateCommand(UUIDPrimaryKey, Base):
    __tablename__ = "gate_commands"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_gate_cmd_idem"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenant_sites.id", ondelete="SET NULL")
    )
    gate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("barrier_gates.id", ondelete="CASCADE"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    command: Mapped[str] = mapped_column(String(32), nullable=False)  # OPEN|CLOSE|LOCK|UNLOCK
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    issued_by_name: Mapped[str | None] = mapped_column(String(255))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response: Mapped[dict | None] = mapped_column(JSONB)
