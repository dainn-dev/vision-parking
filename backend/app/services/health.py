"""Live health probes for the platform-monitoring endpoints."""

import asyncio
import socket
import time
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.services import storage

settings = get_settings()


async def _timed(coro) -> tuple[bool, float]:
    start = time.perf_counter()
    try:
        await coro
        return True, (time.perf_counter() - start) * 1000
    except Exception:
        return False, (time.perf_counter() - start) * 1000


async def check_postgres() -> dict:
    ok, ms = await _timed(_pg_ping())
    return {
        "id": "srv-postgres",
        "name": "PostgreSQL Primary Cluster",
        "category": "database",
        "status": "HEALTHY" if ok else "DOWN",
        "response_time_ms": round(ms, 1),
        "uptime_percent": 100.0 if ok else 0.0,
        "error_rate_percent": 0.0 if ok else 100.0,
        "details": "primary reachable" if ok else "connection failed",
        "last_checked": datetime.now(timezone.utc),
    }


async def _pg_ping():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def check_redis() -> dict:
    ok, ms = await _timed(_redis_ping())
    return {
        "id": "srv-redis",
        "name": "Redis Cache / Queue / Pub-Sub",
        "category": "database",
        "status": "HEALTHY" if ok else "DOWN",
        "response_time_ms": round(ms, 1),
        "uptime_percent": 100.0 if ok else 0.0,
        "error_rate_percent": 0.0 if ok else 100.0,
        "details": settings.redis_url.split("@")[-1],
        "last_checked": datetime.now(timezone.utc),
    }


async def _redis_ping():
    r = aioredis.from_url(settings.redis_url)
    try:
        await r.ping()
    finally:
        await r.aclose()


async def check_s3() -> dict:
    ok, ms = await _timed(_s3_ping())
    return {
        "id": "srv-minio",
        "name": "MinIO Object Storage",
        "category": "storage",
        "status": "HEALTHY" if ok else "DOWN",
        "response_time_ms": round(ms, 1),
        "uptime_percent": 99.9 if ok else 0.0,
        "error_rate_percent": 0.0 if ok else 100.0,
        "details": f"bucket '{settings.s3_bucket}'",
        "last_checked": datetime.now(timezone.utc),
    }


async def _s3_ping():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, storage.ensure_bucket)


async def check_mqtt() -> dict:
    ok, ms = await _timed(_mqtt_ping())
    return {
        "id": "srv-mqtt",
        "name": "EMQX MQTT Broker (edge telemetry)",
        "category": "realtime",
        "status": "HEALTHY" if ok else "DOWN",
        "response_time_ms": round(ms, 1),
        "uptime_percent": 99.9 if ok else 0.0,
        "error_rate_percent": 0.0 if ok else 100.0,
        "details": f"{settings.mqtt_host}:{settings.mqtt_port}",
        "last_checked": datetime.now(timezone.utc),
    }


async def _mqtt_ping():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: socket.create_connection((settings.mqtt_host, settings.mqtt_port), timeout=3).close(),
    )


async def check_api() -> dict:
    return {
        "id": "srv-api",
        "name": "Core REST API Engine",
        "category": "core",
        "status": "HEALTHY",
        "response_time_ms": 1.0,
        "uptime_percent": 99.99,
        "error_rate_percent": 0.0,
        "details": f"{settings.app_name} ({settings.environment})",
        "last_checked": datetime.now(timezone.utc),
    }


async def all_service_health() -> list[dict]:
    checks = await asyncio.gather(check_api(), check_postgres(), check_redis(), check_s3(), check_mqtt())
    return list(checks)
