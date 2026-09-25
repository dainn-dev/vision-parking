"""MQTT ingestion: edge telemetry / incidents / command acks from EMQX.

Topic hierarchy (per SYSTEM_ARCHITECTURE_AND_DATABASE_DESIGN):
    tenants/{tenantId}/sites/{siteId}/gates/{gateId}/{telemetry|incident|command|ack}
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

import aiomqtt
import redis.asyncio as aioredis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import SessionFactory, tenant_session
from app.models import BarrierGate, BarrierIncident, EdgeDevice, GateCommand, GateTelemetryLog
from app.realtime.hub import hub

settings = get_settings()
logger = logging.getLogger(__name__)

TOPIC_FILTER = "tenants/+/sites/+/gates/+/+"
HEARTBEAT_TTL_SECONDS = 45


def parse_parts(topic: str) -> dict | None:
    # tenants/{tenantId}/sites/{siteId}/gates/{gateId}/{suffix}
    parts = topic.split("/")
    if len(parts) != 7 or parts[0] != "tenants" or parts[2] != "sites" or parts[4] != "gates":
        return None
    return {"tenant": parts[1], "site": parts[3], "gate": parts[5], "suffix": parts[6]}


async def _handle_telemetry(db: AsyncSession, ids: dict, payload: dict) -> None:
    gate_id = uuid.UUID(ids["gate"])
    metrics = {
        "cpuPercent": payload.get("cpuPercent"),
        "memoryPercent": payload.get("memoryPercent"),
        "diskPercent": payload.get("diskPercent"),
        "gateState": payload.get("gateState"),
        "latencyMs": payload.get("latencyMs"),
        "eventsPerMin": payload.get("eventsPerMin"),
        "fps": payload.get("fps"),
    }
    metrics = {k: v for k, v in metrics.items() if v is not None}
    db.add(
        GateTelemetryLog(
            tenant_id=uuid.UUID(ids["tenant"]),
            site_id=uuid.UUID(ids["site"]),
            gate_id=gate_id,
            metrics=metrics,
            source="EDGE",
        )
    )
    gate = await db.get(BarrierGate, gate_id)
    if gate:
        gate.status = "ONLINE"
        gate.last_heartbeat_at = datetime.now(timezone.utc)
        if metrics.get("gateState"):
            gate.state = str(metrics["gateState"]).upper()
        if gate.edge_device_id:
            edge = await db.get(EdgeDevice, gate.edge_device_id)
            if edge:
                edge.status = "ONLINE"
                edge.last_heartbeat_at = datetime.now(timezone.utc)
                for mkey, attr in (
                    ("cpuPercent", "cpu_percent"),
                    ("memoryPercent", "memory_percent"),
                    ("diskPercent", "disk_percent"),
                    ("eventsPerMin", "events_per_min"),
                ):
                    if metrics.get(mkey) is not None:
                        setattr(edge, attr, metrics[mkey])
    await db.commit()
    await hub.publish(
        ids["tenant"],
        "gate.telemetry",
        {
            "gateId": ids["gate"],
            "siteId": ids["site"],
            "metrics": metrics,
            "recordedAt": datetime.now(timezone.utc).isoformat(),
        },
    )


async def _handle_incident(db: AsyncSession, ids: dict, payload: dict) -> None:
    incident = BarrierIncident(
        tenant_id=uuid.UUID(ids["tenant"]),
        site_id=uuid.UUID(ids["site"]),
        gate_id=uuid.UUID(ids["gate"]),
        title=payload.get("title", "Edge-reported incident"),
        description=payload.get("description"),
        severity=payload.get("severity", "MEDIUM"),
        status="OPEN",
        resource_type="GATE",
        resource_id=ids["gate"],
        started_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    gate = await db.get(BarrierGate, uuid.UUID(ids["gate"]))
    if gate:
        gate.status = "DEGRADED"
    await db.commit()
    await hub.publish(
        ids["tenant"],
        "gate.incident",
        {
            "incidentId": str(incident.id),
            "gateId": ids["gate"],
            "severity": incident.severity,
            "title": incident.title,
        },
    )


async def _handle_ack(db: AsyncSession, ids: dict, payload: dict) -> None:
    cmd_id = payload.get("commandId")
    if not cmd_id:
        return
    cmd = (
        await db.execute(select(GateCommand).where(GateCommand.id == uuid.UUID(cmd_id)))
    ).scalar_one_or_none()
    if cmd is None:
        return
    now = datetime.now(timezone.utc)
    cmd.acked_at = now
    result = payload.get("result")
    if result == "EXECUTED":
        cmd.status = "EXECUTED"
        cmd.executed_at = now
    elif result == "FAILED":
        cmd.status = "FAILED"
    else:
        cmd.status = "ACKED"
    cmd.response = payload
    await db.commit()
    await hub.publish(
        ids["tenant"],
        "gate.command",
        {"commandId": cmd_id, "gateId": ids["gate"], "status": cmd.status, "result": result},
    )


async def handle_message(topic: str, raw: bytes) -> None:
    ids = parse_parts(topic)
    if ids is None:
        return
    try:
        payload = json.loads(raw.decode()) if raw else {}
    except json.JSONDecodeError:
        logger.warning("non-json payload on %s", topic)
        return
    async with tenant_session(ids["tenant"]) as db:
        suffix = ids["suffix"]
        if suffix == "telemetry":
            await _handle_telemetry(db, ids, payload)
        elif suffix == "incident":
            await _handle_incident(db, ids, payload)
        elif suffix == "ack":
            await _handle_ack(db, ids, payload)
        # "command" topics are outbound — backend publishes, never consumes.


async def mqtt_loop(stop: asyncio.Event) -> None:
    """Reconnecting MQTT consumer; exits when ``stop`` is set."""

    while not stop.is_set():
        try:
            async with aiomqtt.Client(
                hostname=settings.mqtt_host,
                port=settings.mqtt_port,
                username=settings.mqtt_username,
                password=settings.mqtt_password,
                identifier=f"{settings.mqtt_client_prefix}-{uuid.uuid4().hex[:8]}",
            ) as client:
                await client.subscribe(TOPIC_FILTER, qos=1)
                logger.info("MQTT subscribed to %s", TOPIC_FILTER)
                async for message in client.messages:
                    if stop.is_set():
                        break
                    try:
                        await handle_message(str(message.topic), message.payload)
                    except Exception:
                        logger.exception("mqtt message handling failed: %s", message.topic)
        except aiomqtt.MqttError as exc:
            if stop.is_set():
                break
            logger.warning("MQTT connection error: %s — retrying in 5s", exc)
            await asyncio.sleep(5)


async def publish_command(tenant_id: str, site_id: str, gate_id: str, command: dict) -> None:
    topic = f"tenants/{tenant_id}/sites/{site_id}/gates/{gate_id}/command"
    async with aiomqtt.Client(
        hostname=settings.mqtt_host,
        port=settings.mqtt_port,
        username=settings.mqtt_username,
        password=settings.mqtt_password,
        identifier=f"{settings.mqtt_client_prefix}-pub-{uuid.uuid4().hex[:8]}",
    ) as client:
        await client.publish(topic, json.dumps(command, default=str), qos=1)


async def heartbeat_sweeper(stop: asyncio.Event) -> None:
    """Marks gates/edges OFFLINE when their Redis heartbeat expires."""

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        while not stop.is_set():
            await asyncio.sleep(30)
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_TTL_SECONDS)
                async with SessionFactory() as db:
                    await db.execute(text("SELECT set_config('app.platform_ctx','platform',true)"))
                    stale = await db.execute(
                        select(BarrierGate).where(
                            BarrierGate.status == "ONLINE",
                            BarrierGate.last_heartbeat_at < cutoff,
                        )
                    )
                    for gate in stale.scalars():
                        gate.status = "OFFLINE"
                    await db.commit()
            except Exception:
                logger.exception("heartbeat sweep failed")
    finally:
        await redis.aclose()
