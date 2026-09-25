"""Idempotent dev seed mirroring the frontend console's mock dataset.

Run: ``python -m app.seed`` (inside the api container after migrations).
Tenant-scoped writes run under the ``app.platform_ctx='platform'`` bypass.
"""

import asyncio
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import platform_session
from app.core.security import hash_password
from app.models import (
    BarrierGate,
    EdgeDevice,
    FeatureFlag,
    LegalDocument,
    PlatformAdmin,
    PlatformSetting,
    Site,
    SiteLane,
    SubscriptionPlan,
    Tenant,
    TenantUser,
)

settings = get_settings()
logger = logging.getLogger("seed")

TENANTS = [
    dict(
        name="ABC Logistics & Parking",
        code="ABC-LOGISTICS",
        email="contact@abclogistics.vn",
        phone="+84 28 3822 9900",
        status="ACTIVE",
        admin=dict(name="Nguyen Van Minh", email="minh.nguyen@abclogistics.vn", phone="+84 90 312 3456"),
    ),
    dict(
        name="Saigon Metro Plaza Mall",
        code="SG-METRO-PLAZA",
        email="operations@sgmetro.com.vn",
        phone="+84 28 7300 1122",
        status="ACTIVE",
        admin=dict(name="Tran Thi Hong", email="hong.tran@sgmetro.com.vn", phone="+84 91 822 3344"),
    ),
    dict(
        name="Vinhomes Central Park Gate Systems",
        code="VINHOMES-CP",
        email="security@vinhomescp.vn",
        phone="+84 28 3910 8888",
        status="ACTIVE",
        admin=dict(name="Le Hoang Nam", email="nam.le@vinhomescp.vn", phone="+84 98 900 1122"),
    ),
    dict(
        name="Tan Son Nhat Air Cargo Terminal",
        code="TSN-CARGO-TERM",
        email="access@tsncargo.com.vn",
        phone="+84 28 3844 5566",
        status="ACTIVE",
        admin=dict(name="Pham Quoc Bao", email="bao.pham@tsncargo.com.vn", phone=None),
    ),
    dict(
        name="TechPark Tan Thuan Enterprise",
        code="TECHPARK-TT",
        email="admin@techpark.vn",
        phone="+84 28 3770 0011",
        status="TRIAL",
        admin=dict(name="Doan Viet Dung", email="dung.doan@techpark.vn", phone=None),
    ),
    dict(
        name="Old Port Warehousing Services",
        code="OLD-PORT-WAREHOUSE",
        email="info@oldport.com.vn",
        phone="+84 28 3829 1122",
        status="SUSPENDED",
        admin=dict(name="Vo Thi Lan", email="lan.vo@oldport.com.vn", phone=None),
    ),
]

PLATFORM_ADMINS = [
    dict(name="Anthony Nguyen", email="anh.nh@kyanon.digital", role="PLATFORM_ADMIN", status="ACTIVE"),
    dict(
        name="Johnathan Vance",
        email="johnathan.vance@platform.internal",
        role="PLATFORM_ADMIN",
        status="ACTIVE",
    ),
    dict(
        name="Platform Support Lead",
        email="support.lead@platform.internal",
        role="PLATFORM_SUPPORT",
        status="ACTIVE",
    ),
    dict(
        name="Security Officer Alex",
        email="security.alex@platform.internal",
        role="PLATFORM_SECURITY",
        status="ACTIVE",
    ),
    dict(
        name="Inactive Admin Account",
        email="legacy.admin@platform.internal",
        role="PLATFORM_ADMIN",
        status="DISABLED",
    ),
]

MOCK_TENANT_ID_TO_CODE = {
    "t-001": "ABC-LOGISTICS",
    "t-002": "SG-METRO-PLAZA",
    "t-003": "VINHOMES-CP",
    "t-004": "TSN-CARGO-TERM",
    "t-005": "TECHPARK-TT",
    "t-006": "OLD-PORT-WAREHOUSE",
}

FEATURE_FLAGS = [
    dict(
        key="ANPR_AI_V2_CORE",
        name="Automatic Number Plate Recognition V2 (YOLOv11 Edge)",
        description="Enables real-time 99.8% precision license plate optical character "
        "recognition with blur & night IR restoration.",
        enabled=True,
        environment="production",
        rollout_percentage=100,
        rules=[{"tenantIds": ["t-001", "t-002", "t-003"]}],
        updated_by="anh.nh@kyanon.digital",
    ),
    dict(
        key="BIOMETRIC_DRIVER_VERIFY",
        name="Driver Facial Verification at Gate Barrier",
        description="Cross-checks camera driver snapshot against resident/staff registered "
        "biometric templates.",
        enabled=True,
        environment="production",
        rollout_percentage=50,
        rules=[{"tenantIds": ["t-003"]}],
        updated_by="johnathan.vance@platform.internal",
    ),
    dict(
        key="EDGE_STREAM_HQ_60FPS",
        name="60 FPS Ultra-HD RTSP Edge Camera Ingestion",
        description="Allows high-throughput 4K stream decoding on hardware-accelerated NPU Edge devices.",
        enabled=True,
        environment="production",
        rollout_percentage=25,
        rules=[{"tenantIds": ["t-004"]}],
        updated_by="security.alex@platform.internal",
    ),
    dict(
        key="GEO_IP_LOCKOUT_STRICT",
        name="Strict Geo-IP Authentication Lockout",
        description="Blocks login sessions originating outside designated country IP CIDR blocks.",
        enabled=True,
        environment="production",
        rollout_percentage=100,
        rules=[],
        updated_by="anh.nh@kyanon.digital",
    ),
    dict(
        key="KAFKA_STREAMING_CDC",
        name="Kafka Change Data Capture Event Hub",
        description="Streams entry/exit audit payloads to external compliance data lakes "
        "in sub-50ms latency.",
        enabled=False,
        environment="staging",
        rollout_percentage=0,
        rules=[],
        updated_by="anh.nh@kyanon.digital",
    ),
]

SETTINGS = {
    "general": dict(
        platformName="Vehicle Governance Platform Admin Console",
        platformUrl="https://vehicle.platform.internal",
        defaultTimezone="Asia/Ho_Chi_Minh",
        defaultLanguage="English (US)",
        supportEmail="platform-support@kyanon.digital",
        supportUrl="https://support.vehicle.platform.internal",
    ),
    "authentication": dict(
        accessTokenLifetimeMinutes=15,
        refreshTokenLifetimeDays=7,
        sessionTimeoutMinutes=30,
        maxConcurrentSessions=5,
        revokeSessionsOnPasswordChange=True,
        revokeSessionsOnPasswordReset=True,
    ),
    "security": dict(
        minPasswordLength=12,
        requireUppercase=True,
        requireLowercase=True,
        requireNumbers=True,
        requireSpecialChars=True,
        maxFailedLoginAttempts=5,
        accountLockoutMinutes=15,
        mfaEnforcement="MANDATORY_ADMINS",
    ),
    "storage": dict(
        provider="MinIO",
        defaultImageRetentionDays=90,
        attachmentRetentionDays=180,
        maxUploadSizeBytes=20971520,
        autoCleanupEnabled=True,
        warningThresholdPercent=80,
    ),
    "notifications": dict(
        emailNotificationsEnabled=True,
        senderName="Platform Governance Control Center",
        senderEmail="no-reply@vehicle.platform.internal",
        notifySecurityAlerts=True,
        notifySystemHealthAlerts=True,
        notifyTenantLifecycleAlerts=True,
    ),
}

PLANS = [
    dict(
        code="STARTER",
        name="Starter Gate",
        description="1 site / 2 gates / up to 500 vehicles",
        price_cents=1_500_000_00,
        currency="VND",
        interval="MONTHLY",
        features={"maxSites": 1, "maxGates": 2, "maxVehicles": 500, "anpr": True, "support": "EMAIL"},
    ),
    dict(
        code="PROFESSIONAL",
        name="Professional",
        description="5 sites / 20 gates / 10k vehicles + telemetry",
        price_cents=7_500_000_00,
        currency="VND",
        interval="MONTHLY",
        features={
            "maxSites": 5,
            "maxGates": 20,
            "maxVehicles": 10000,
            "anpr": True,
            "telemetry": True,
            "support": "PRIORITY",
        },
    ),
    dict(
        code="ENTERPRISE",
        name="Enterprise",
        description="Unlimited sites, SLA 99.9%, dedicated CSM",
        price_cents=25_000_000_00,
        currency="VND",
        interval="MONTHLY",
        features={"maxSites": -1, "maxGates": -1, "maxVehicles": -1, "sla": "99.9", "support": "DEDICATED"},
    ),
]

LEGAL_DOCS = [
    dict(
        doc_type="TERMS",
        version="1.2.0",
        title="Terms of Service — Vehicle Governance Platform",
        content="These Terms govern access to the multi-tenant vehicle access & barrier-gate "
        "governance platform. Tenants are responsible for their registered vehicles, access rules, "
        "and gate hardware operators.",
    ),
    dict(
        doc_type="PRIVACY",
        version="1.1.0",
        title="Privacy Policy",
        content="The platform processes license-plate images, access events, and account "
        "identifiers for the sole purpose of gate access governance. Plate imagery is retained "
        "per the tenant's configured retention window.",
    ),
]

DEMO_HARDWARE = {
    "ABC-LOGISTICS": dict(
        site=("ABC-NORTH", "ABC North Warehouse Campus"),
        edge=("EDGE-GATE-ABC-NORTH", "ONLINE", "v2.4.1-arm64"),
        gate="GATE-MAIN-INBOUND-01",
    ),
    "SG-METRO-PLAZA": dict(
        site=("SGM-B1", "SG Metro Plaza Basement 1"),
        edge=("EDGE-GATE-SGMETRO-L1", "ONLINE", "v2.4.1-arm64"),
        gate="GATE-SG-MALL-SOUTH",
    ),
    "VINHOMES-CP": dict(
        site=("VH-ZONE-A", "Vinhomes Central Park Zone A"),
        edge=("EDGE-VINHOMES-ZONE-A", "ONLINE", "v2.4.1-arm64"),
        gate="GATE-VINHOMES-TOWER-1",
    ),
    "TSN-CARGO-TERM": dict(
        site=("TSN-MAIN", "TSN Cargo Terminal Main"),
        edge=("EDGE-TSN-CARGO-MAIN", "DEGRADED", "v2.3.8-legacy"),
        gate="GATE-TSN-CARGO-RESTRICTED",
    ),
    "OLD-PORT-WAREHOUSE": dict(
        site=("OP-BAY01", "Old Port Bay 01"),
        edge=("EDGE-OLDPORT-BAY01", "OFFLINE", "v2.2.0-legacy"),
        gate="GATE-OLDPORT-BAY01",
    ),
}


async def _exists(db: AsyncSession, model, **where) -> bool:
    q = select(func.count()).select_from(model)
    for k, v in where.items():
        q = q.where(getattr(model, k) == v)
    return (await db.execute(q)).scalar_one() > 0


async def seed() -> None:
    async with platform_session() as db:
        tenant_ids: dict[str, uuid.UUID] = {}

        for p in PLANS:
            if not await _exists(db, SubscriptionPlan, code=p["code"]):
                db.add(SubscriptionPlan(**p))
        for d in LEGAL_DOCS:
            if not await _exists(db, LegalDocument, doc_type=d["doc_type"], version=d["version"]):
                db.add(LegalDocument(**d))

        for a in PLATFORM_ADMINS:
            if not await _exists(db, PlatformAdmin, email=a["email"]):
                db.add(PlatformAdmin(**a, password_hash=hash_password(settings.seed_admin_password)))

        for t in TENANTS:
            t = dict(t)
            admin = t.pop("admin")
            tenant = (await db.execute(select(Tenant).where(Tenant.code == t["code"]))).scalar_one_or_none()
            if tenant is None:
                tenant = Tenant(timezone="Asia/Ho_Chi_Minh", **t)
                db.add(tenant)
                await db.flush()
            tenant_ids[t["code"]] = tenant.id
            if not await _exists(db, TenantUser, tenant_id=tenant.id, email=admin["email"]):
                db.add(
                    TenantUser(
                        tenant_id=tenant.id,
                        role="TENANT_ADMIN",
                        status="ACTIVE",
                        password_hash=hash_password(settings.seed_tenant_password),
                        **admin,
                    )
                )

        for code, hw in DEMO_HARDWARE.items():
            tid = tenant_ids[code]
            site_code, site_name = hw["site"]
            site = (
                await db.execute(select(Site).where(Site.tenant_id == tid, Site.code == site_code))
            ).scalar_one_or_none()
            if site is None:
                site = Site(tenant_id=tid, code=site_code, name=site_name, status="ACTIVE")
                db.add(site)
                await db.flush()

            edge_name, edge_status, fw = hw["edge"]
            edge = (
                await db.execute(
                    select(EdgeDevice).where(EdgeDevice.tenant_id == tid, EdgeDevice.device_name == edge_name)
                )
            ).scalar_one_or_none()
            if edge is None:
                edge = EdgeDevice(
                    tenant_id=tid,
                    site_id=site.id,
                    device_name=edge_name,
                    status=edge_status,
                    firmware_version=fw,
                )
                db.add(edge)
                await db.flush()

            lane = (
                await db.execute(
                    select(SiteLane).where(SiteLane.tenant_id == tid, SiteLane.site_id == site.id)
                )
            ).scalar_one_or_none()
            if lane is None:
                lane = SiteLane(tenant_id=tid, site_id=site.id, name="Lane 1", direction="INBOUND")
                db.add(lane)
                await db.flush()

            if not await _exists(db, BarrierGate, tenant_id=tid, name=hw["gate"]):
                db.add(
                    BarrierGate(
                        tenant_id=tid,
                        site_id=site.id,
                        lane_id=lane.id,
                        edge_device_id=edge.id,
                        name=hw["gate"],
                        status=edge_status,
                        state="CLOSED",
                    )
                )

        for f in FEATURE_FLAGS:
            f = dict(f)
            if not await _exists(db, FeatureFlag, key=f["key"]):
                rules = []
                for r in f.pop("rules"):
                    rules.append(
                        {
                            **r,
                            "tenantIds": [
                                str(tenant_ids.get(MOCK_TENANT_ID_TO_CODE.get(i, "")) or i)
                                for i in r.get("tenantIds", [])
                            ],
                        }
                    )
                db.add(FeatureFlag(rules=rules, **f))

        for section, data in SETTINGS.items():
            if not await _exists(db, PlatformSetting, section=section):
                db.add(PlatformSetting(section=section, data=data, updated_by="seed"))

        await db.commit()
        logger.info("seed complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
