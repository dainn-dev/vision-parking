"""Schemas for the platform-governance surface (admin console contract)."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel, StrIp

# ------------------------------------------------------------------ tenants


class TenantAdministratorIn(CamelModel):
    name: str
    email: EmailStr
    phone: str | None = None
    password: str | None = Field(default=None, min_length=12, max_length=256)


class TenantAdministratorOut(CamelModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None = None


class TenantStatistics(CamelModel):
    users_count: int = 0
    vehicles_count: int = 0
    cameras_count: int = 0
    gates_count: int = 0
    edge_devices_count: int = 0
    events_count: int = 0
    storage_used_gb: float = 0.0


class TenantOut(CamelModel):
    id: uuid.UUID
    name: str
    code: str
    email: str
    phone: str | None = None
    timezone: str
    status: str
    administrator: TenantAdministratorOut | None = None
    statistics: TenantStatistics = Field(default_factory=TenantStatistics)
    created_at: datetime
    last_activity_at: datetime | None = None


class TenantCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    email: EmailStr
    phone: str | None = None
    timezone: str = "Asia/Ho_Chi_Minh"
    administrator: TenantAdministratorIn


class TenantUpdate(CamelModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    timezone: str | None = None


class TenantStatusUpdate(CamelModel):
    status: Literal["ACTIVE", "TRIAL", "SUSPENDED", "DISABLED"]
    reason: str | None = None


# ------------------------------------------------------------------ admins


class PlatformAdminOut(CamelModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    status: str
    mfa_enabled: bool
    mfa_configured_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    failed_login_attempts: int = 0


class PlatformAdminCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role: Literal["PLATFORM_ADMIN", "PLATFORM_SUPPORT", "PLATFORM_SECURITY"] = "PLATFORM_ADMIN"
    password: str | None = Field(default=None, min_length=12, max_length=256)


class PlatformAdminUpdate(CamelModel):
    name: str | None = None
    role: Literal["PLATFORM_ADMIN", "PLATFORM_SUPPORT", "PLATFORM_SECURITY"] | None = None


# ------------------------------------------------------------------ feature flags


class FeatureFlagRule(CamelModel):
    id: str | None = None
    tenant_ids: list[uuid.UUID] | None = None
    user_percentage: int | None = Field(default=None, ge=0, le=100)


class FeatureFlagOut(CamelModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    enabled: bool
    environment: str
    rollout_percentage: int
    rules: list[FeatureFlagRule] = Field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: str | None = None


class FeatureFlagUpsert(CamelModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    environment: Literal["production", "staging", "development"] | None = None
    rollout_percentage: int | None = Field(default=None, ge=0, le=100)
    rules: list[FeatureFlagRule] | None = None


# ------------------------------------------------------------------ settings


class GeneralSettings(CamelModel):
    platform_name: str = "Vehicle Governance Platform"
    platform_url: str = ""
    default_timezone: str = "Asia/Ho_Chi_Minh"
    default_language: str = "English (US)"
    support_email: str = ""
    support_url: str = ""


class AuthenticationSettings(CamelModel):
    access_token_lifetime_minutes: int = 15
    refresh_token_lifetime_days: int = 7
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 5
    revoke_sessions_on_password_change: bool = True
    revoke_sessions_on_password_reset: bool = True


class SecuritySettings(CamelModel):
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 15
    mfa_enforcement: Literal["MANDATORY_ALL", "MANDATORY_ADMINS", "OPTIONAL"] = "MANDATORY_ADMINS"


class StorageSettings(CamelModel):
    provider: str = "MinIO"
    default_image_retention_days: int = 90
    attachment_retention_days: int = 180
    max_upload_size_bytes: int = 20_971_520
    auto_cleanup_enabled: bool = True
    warning_threshold_percent: int = 80


class NotificationSettings(CamelModel):
    email_notifications_enabled: bool = True
    sender_name: str = "Platform Governance Control Center"
    sender_email: str = "no-reply@vehicle.platform.internal"
    notify_security_alerts: bool = True
    notify_system_health_alerts: bool = True
    notify_tenant_lifecycle_alerts: bool = True


class PlatformSettingsOut(CamelModel):
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    authentication: AuthenticationSettings = Field(default_factory=AuthenticationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)


class SettingsSectionUpdate(CamelModel):
    data: dict[str, Any]


# ------------------------------------------------------------------ monitoring


class ServiceHealthOut(CamelModel):
    id: str
    name: str
    category: str
    status: str
    response_time_ms: float = 0
    uptime_percent: float = 100.0
    error_rate_percent: float = 0.0
    details: str | None = None
    last_checked: datetime | None = None


class EdgeDeviceHealthOut(CamelModel):
    id: uuid.UUID
    device_name: str
    tenant_id: uuid.UUID
    tenant_name: str
    status: str
    cpu_percent: float = 0
    memory_percent: float = 0
    disk_percent: float = 0
    version: str | None = None
    connected_cameras: int = 0
    events_per_min: int = 0
    last_heartbeat: datetime | None = None


class GateHealthOut(CamelModel):
    id: uuid.UUID
    gate_name: str
    tenant_id: uuid.UUID
    tenant_name: str
    status: str
    events_per_min: int = 0
    average_latency_ms: float = 0
    success_rate_percent: float = 0
    last_heartbeat: datetime | None = None


class IncidentOut(CamelModel):
    id: uuid.UUID
    title: str
    severity: str
    status: str
    resource_id: str | None = None
    resource_type: str | None = None
    tenant_id: uuid.UUID | None = None
    tenant_name: str | None = None
    description: str | None = None
    started_at: datetime
    updated_at: datetime
    resolution_note: str | None = None
    assigned_to: str | None = None


class IncidentAction(CamelModel):
    note: str | None = None
    assigned_to: str | None = None


# ------------------------------------------------------------------ security


class SecurityAlertOut(CamelModel):
    id: uuid.UUID
    type: str
    severity: str
    status: str
    subject_email: str | None = None
    subject_user_type: str | None = None
    detected_at: datetime
    source_ip: StrIp | None = None
    client_browser: str | None = None
    evidence: dict = Field(default_factory=dict)


class LoginEventOut(CamelModel):
    id: uuid.UUID
    timestamp: datetime
    user_email: str
    user_type: str
    tenant_name: str | None = None
    result: str
    source_ip: StrIp | None = None
    client_device: str | None = None
    failure_reason: str | None = None
    suspicious: bool = False


class SessionOut(CamelModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    user_email: str
    user_type: str
    tenant_id: uuid.UUID | None = None
    tenant_name: str | None = None
    device: str | None = None
    browser: str | None = None
    os: str | None = None
    ip_address: StrIp | None = None
    location: str | None = None
    risk_level: str
    created_at: datetime
    last_active_at: datetime


class ApiCredentialOut(CamelModel):
    id: uuid.UUID
    name: str
    type: str
    owner_name: str | None = None
    key_prefix: str
    status: str
    last_used_at: datetime | None = None
    created_at: datetime
    expires_at: datetime | None = None


class ApiCredentialCreate(CamelModel):
    name: str = Field(min_length=1, max_length=255)
    type: Literal["PLATFORM_KEY", "EDGE_KEY", "INTEGRATION_SECRET", "SERVICE_ACCOUNT"]
    owner_name: str | None = None
    expires_at: datetime | None = None


class ApiCredentialCreated(CamelModel):
    credential: ApiCredentialOut
    plaintext_key: str


# ------------------------------------------------------------------ audit


class AuditLogOut(CamelModel):
    id: uuid.UUID
    timestamp: datetime
    category: str
    action: str
    actor_name: str | None = None
    actor_email: str | None = None
    actor_type: str
    tenant_name: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None
    result: str
    source: str
    ip_address: StrIp | None = None
    request_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    changes: list[dict] | None = None
    log_metadata: dict | None = Field(default=None, serialization_alias="metadata")


# ------------------------------------------------------------------ public


class PlanOut(CamelModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    price_cents: int
    currency: str
    interval: str
    features: dict = Field(default_factory=dict)


class LegalDocOut(CamelModel):
    id: uuid.UUID
    doc_type: str
    version: str
    title: str
    content: str
    published_at: datetime


class TenantRegistration(CamelModel):
    organization_name: str = Field(min_length=1, max_length=255)
    organization_code: str = Field(min_length=1, max_length=64)
    email: EmailStr
    phone: str | None = None
    timezone: str = "Asia/Ho_Chi_Minh"
    administrator: TenantAdministratorIn
    plan_code: str | None = None
    accepted_legal_version: str | None = None
