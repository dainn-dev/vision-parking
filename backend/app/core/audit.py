import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    category: str,
    action: str,
    actor_type: str = "SYSTEM",
    actor_id: uuid.UUID | None = None,
    actor_name: str | None = None,
    actor_email: str | None = None,
    tenant_id: uuid.UUID | None = None,
    tenant_name: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    resource_name: str | None = None,
    result: str = "SUCCESS",
    source: str = "WEB",
    ip_address: str | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
    changes: list[dict] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        category=category,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_email=actor_email,
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        result=result,
        source=source,
        ip_address=ip_address,
        request_id=request_id,
        trace_id=trace_id,
        changes=changes,
        log_metadata=metadata,
    )
    db.add(entry)
    return entry
