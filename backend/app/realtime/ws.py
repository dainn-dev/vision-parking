import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.deps import ws_current_user
from app.realtime.hub import hub

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws/tenants/{tenant_id}/barrier-telemetry")
async def barrier_telemetry_ws(websocket: WebSocket, tenant_id: uuid.UUID) -> None:
    user = await ws_current_user(websocket)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if user.user_type != "PLATFORM_ADMIN" and user.tenant_id != tenant_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    hub.add(str(tenant_id), websocket)
    await websocket.send_json({"event": "connected", "payload": {"tenantId": str(tenant_id)}})
    try:
        while True:
            # Keep-alive: inbound payloads are ignored; clients may send pings.
            await asyncio.wait_for(websocket.receive_text(), timeout=60)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception:
        logger.exception("ws error")
    finally:
        hub.remove(str(tenant_id), websocket)
        try:
            await websocket.close()
        except Exception:
            pass
