"""Redis pub/sub fan-out — lets multiple API workers share WS delivery."""

import asyncio
import json
import logging
import uuid
from collections import defaultdict

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "ws:tenant:"
CHANNEL_PATTERN = "ws:tenant:*"


class Hub:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis: aioredis.Redis | None = None
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._task = asyncio.create_task(self._listen(), name="ws-hub-listener")

    async def stop(self) -> None:
        self._stopping.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._redis:
            await self._redis.aclose()
        for conns in self.connections.values():
            for ws in conns:
                try:
                    await ws.close(code=1001)
                except Exception:
                    pass
        self.connections.clear()

    def channel(self, tenant_id: uuid.UUID | str) -> str:
        return f"{CHANNEL_PREFIX}{tenant_id}"

    async def publish(self, tenant_id: uuid.UUID | str, event: str, payload: dict) -> None:
        if self._redis is None:
            return
        message = json.dumps({"event": event, "payload": payload}, default=str)
        try:
            await self._redis.publish(self.channel(tenant_id), message)
        except Exception:
            logger.exception("hub publish failed")

    async def broadcast(self, tenant_id: uuid.UUID | str, event: str, payload: dict) -> None:
        """Direct in-process fan-out (used when publisher lives in this worker)."""
        message = json.dumps({"event": event, "payload": payload}, default=str)
        for ws in list(self.connections.get(str(tenant_id), ())):
            try:
                await ws.send_text(message)
            except Exception:
                self.connections[str(tenant_id)].discard(ws)

    def add(self, tenant_id: str, ws: WebSocket) -> None:
        self.connections[tenant_id].add(ws)

    def remove(self, tenant_id: str, ws: WebSocket) -> None:
        self.connections[tenant_id].discard(ws)
        if not self.connections[tenant_id]:
            self.connections.pop(tenant_id, None)

    async def _listen(self) -> None:
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe(CHANNEL_PATTERN)
        try:
            async for message in pubsub.listen():
                if self._stopping.is_set():
                    break
                if message["type"] not in ("pmessage", "message"):
                    continue
                channel: str = message["channel"]
                tenant_id = channel.removeprefix(CHANNEL_PREFIX)
                data = message["data"]
                for ws in list(self.connections.get(tenant_id, ())):
                    try:
                        await ws.send_text(data)
                    except Exception:
                        self.connections[tenant_id].discard(ws)
        except asyncio.CancelledError:
            raise
        finally:
            await pubsub.punsubscribe(CHANNEL_PATTERN)
            await pubsub.aclose()


hub = Hub()
