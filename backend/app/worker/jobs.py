"""arq worker jobs — run outside the request lifecycle."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.database import SessionFactory
from app.models import BarrierGate, EdgeDevice, Tenant
from app.services import email

settings = get_settings()
logger = logging.getLogger(__name__)

OFFLINE_AFTER = timedelta(seconds=90)
PLATFORM_CTX = "SELECT set_config('app.platform_ctx','platform',true)"


async def send_invite(ctx, to_email: str, tenant_id: str, name: str) -> bool:
    async with SessionFactory() as db:
        tenant = await db.get(Tenant, uuid.UUID(tenant_id))
    tenant_name = tenant.name if tenant else "your organization"
    url = f"{settings.public_base_url}/invite/accept?tenant={tenant_id}&email={to_email}"
    return await email.send_invite_email(to_email, tenant_name, url)


async def create_future_partitions(ctx=None) -> str:
    """Ensures monthly telemetry + quarterly access-event partitions exist for
    the current and next partition windows (call nightly)."""

    async with SessionFactory() as db:
        for stmt in (
            "SELECT ensure_telemetry_partition(now())",
            "SELECT ensure_telemetry_partition(now() + interval '1 month')",
            "SELECT ensure_telemetry_partition(now() + interval '2 months')",
            "SELECT ensure_access_event_partition(now())",
            "SELECT ensure_access_event_partition(now() + interval '3 months')",
            "SELECT ensure_access_event_partition(now() + interval '6 months')",
        ):
            await db.execute(text(stmt))
        await db.commit()
    return "partitions ensured"


async def purge_expired_images(ctx=None) -> str:
    """Clears image URLs on access events older than the retention window —
    objects themselves are removed by the MinIO lifecycle policy."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.plate_image_retention_days)
    async with SessionFactory() as db:
        await db.execute(text(PLATFORM_CTX))
        result = await db.execute(
            text(
                "UPDATE access_events SET plate_image_url=NULL, overview_image_url=NULL "
                "WHERE occurred_at < :cutoff AND (plate_image_url IS NOT NULL "
                "OR overview_image_url IS NOT NULL)"
            ),
            {"cutoff": cutoff},
        )
        await db.commit()
        return f"purged {result.rowcount} event image refs"


async def sweep_offline_gateways(ctx=None) -> str:
    cutoff = datetime.now(timezone.utc) - OFFLINE_AFTER
    async with SessionFactory() as db:
        await db.execute(text(PLATFORM_CTX))
        gates = (
            await db.execute(
                select(BarrierGate).where(
                    BarrierGate.status.in_(["ONLINE", "DEGRADED"]),
                    BarrierGate.last_heartbeat_at < cutoff,
                )
            )
        ).scalars()
        edges = (
            await db.execute(
                select(EdgeDevice).where(
                    EdgeDevice.status.in_(["ONLINE", "DEGRADED"]),
                    EdgeDevice.last_heartbeat_at < cutoff,
                )
            )
        ).scalars()
        for g in gates:
            g.status = "OFFLINE"
        for e in edges:
            e.status = "OFFLINE"
        await db.commit()
        return f"swept {len(gates)} gates, {len(edges)} edge devices"
