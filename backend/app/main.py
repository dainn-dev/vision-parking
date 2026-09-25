import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import ApiError, api_error_handler, error_body
from app.realtime.hub import hub
from app.realtime.mqtt import heartbeat_sweeper, mqtt_loop
from app.realtime.ws import ws_router
from app.services import storage

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mqtt_stop = asyncio.Event()
    hub_task = asyncio.create_task(hub.start(), name="ws-hub")
    mqtt_task = asyncio.create_task(mqtt_loop(app.state.mqtt_stop), name="mqtt-ingest")
    sweep_task = asyncio.create_task(heartbeat_sweeper(app.state.mqtt_stop), name="hb-sweeper")
    loop = asyncio.get_running_loop()
    bucket_task = loop.run_in_executor(None, storage.ensure_bucket)
    try:
        yield
    finally:
        app.state.mqtt_stop.set()
        for t in (mqtt_task, sweep_task):
            t.cancel()
        await asyncio.gather(mqtt_task, sweep_task, hub_task, bucket_task, return_exceptions=True)
        await hub.stop()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-csrf-token"],
    expose_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_body("VALIDATION", "Request validation failed", exc.errors()),
    )


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body("DATABASE_ERROR", "Internal database error"),
    )


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # lightweight request id for trace correlation
    import uuid as _uuid

    request.state.request_id = f"req-{_uuid.uuid4().hex[:12]}"
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.get(f"{settings.api_v1_prefix}/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(ws_router)


# ------------------------------------------------------------------ healthcheck helper


@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True}
