"""Platform-governance entities (cross-tenant; not RLS-scoped)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Tenant(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Ho_Chi_Minh", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="TRIAL", nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["TenantUser"]] = relationship(  # noqa: F821
        "TenantUser", back_populates="tenant", cascade="all, delete-orphan"
    )


class PlatformAdmin(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "platform_admins"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="PLATFORM_ADMIN", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret_enc: Mapped[str | None] = mapped_column(Text)
    mfa_configured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(UUIDPrimaryKey, Base):
    """Refresh-session row shared by platform admins and tenant users.

    ``user_id`` is polymorphic by design (two separate account tables) and is
    validated in the service layer rather than by a foreign key.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # PLATFORM_ADMIN | TENANT_ADMIN | MEMBER
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    tenant_name: Mapped[str | None] = mapped_column(String(255))
    refresh_token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    device: Mapped[str | None] = mapped_column(String(255))
    browser: Mapped[str | None] = mapped_column(String(255))
    os: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(INET)
    location: Mapped[str | None] = mapped_column(String(255))
    risk_level: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FeatureFlag(UUIDPrimaryKey, Base):
    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    environment: Mapped[str] = mapped_column(String(16), default="production", nullable=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rules: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[str | None] = mapped_column(String(255))


class PlatformSetting(Base):
    """One row per settings section (general/authentication/security/storage/notifications)."""

    __tablename__ = "platform_settings"

    section: Mapped[str] = mapped_column(String(32), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[str | None] = mapped_column(String(255))


class SecurityAlert(UUIDPrimaryKey, Base):
    __tablename__ = "security_alerts"

    type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="OPEN", nullable=False)
    subject_email: Mapped[str | None] = mapped_column(String(255), index=True)
    subject_user_type: Mapped[str | None] = mapped_column(String(32))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_ip: Mapped[str | None] = mapped_column(INET)
    client_browser: Mapped[str | None] = mapped_column(String(255))
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")


class LoginEvent(UUIDPrimaryKey, Base):
    __tablename__ = "login_events"

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    user_type: Mapped[str] = mapped_column(String(32))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    tenant_name: Mapped[str | None] = mapped_column(String(255))
    result: Mapped[str] = mapped_column(String(16))  # SUCCESS | FAILED | BLOCKED | CHALLENGED
    source_ip: Mapped[str | None] = mapped_column(INET)
    client_device: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(String(128))
    suspicious: Mapped[bool] = mapped_column(Boolean, default=False)


class ApiCredential(UUIDPrimaryKey, Base):
    __tablename__ = "api_credentials"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # PLATFORM_KEY | EDGE_KEY | INTEGRATION_SECRET | SERVICE_ACCOUNT
    owner_name: Mapped[str | None] = mapped_column(String(255))
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(UUIDPrimaryKey, Base):
    __tablename__ = "audit_logs"

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    category: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )  # polymorphic, enforced in service layer
    actor_name: Mapped[str | None] = mapped_column(String(255))
    actor_email: Mapped[str | None] = mapped_column(String(255), index=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    tenant_name: Mapped[str | None] = mapped_column(String(255))
    resource_type: Mapped[str | None] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(128))
    resource_name: Mapped[str | None] = mapped_column(String(255))
    result: Mapped[str] = mapped_column(String(16), default="SUCCESS")
    source: Mapped[str] = mapped_column(String(16), default="WEB")
    ip_address: Mapped[str | None] = mapped_column(INET)
    request_id: Mapped[str | None] = mapped_column(String(64))
    trace_id: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(64))
    changes: Mapped[list | None] = mapped_column(JSONB)
    log_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)


class SubscriptionPlan(UUIDPrimaryKey, Base):
    __tablename__ = "subscription_plans"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(BigInteger, default=0)  # cents in VND can exceed int32
    currency: Mapped[str] = mapped_column(String(8), default="VND")
    interval: Mapped[str] = mapped_column(String(16), default="MONTHLY")
    features: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LegalDocument(UUIDPrimaryKey, Base):
    __tablename__ = "legal_documents"

    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)  # TERMS | PRIVACY | DPA
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VehicleImportJob(UUIDPrimaryKey, Base):
    __tablename__ = "vehicle_import_jobs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    s3_key: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="PENDING")  # PENDING|RUNNING|COMPLETED|FAILED
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
