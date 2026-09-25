# Vision Parking Backend

FastAPI backend for the multi-tenant vehicle access & barrier-gate governance platform,
implementing `SYSTEM_ARCHITECTURE_AND_DATABASE_DESIGN.md`.

## Stack

- FastAPI 0.115 + SQLAlchemy 2.0 (async, asyncpg) + Alembic
- PostgreSQL 16 with row-level security tenant isolation (`app.current_tenant_id`)
- Redis (pub/sub WebSocket fan-out + arq worker queue)
- EMQX (MQTT edge ingest: `tenants/{t}/sites/{s}/gates/{g}/{telemetry|incident|ack|command}`)
- RustFS (S3-compatible object storage for plate imagery)
- Mailpit (dev SMTP)

## Quick start (Docker Compose)

```bash
cd backend
cp .env.example .env            # optional; compose defaults work out of the box
docker compose up --build       # postgres + redis + emqx + rustfs + mailpit + api + worker
```

The `api` container runs `alembic upgrade head` and the seed at startup, then serves
`http://localhost:8000` (OpenAPI docs at `/api/v1/docs`).

Seed accounts:

- Platform admin: `anh.nh@kyanon.digital` / `ChangeMe!2026`
- Tenant admin (ABC Logistics): `minh.nguyen@abclogistics.vn` / `TenantDemo!2026`

Useful endpoints: `http://localhost:9001` RustFS console, `http://localhost:8025` Mailpit,
`http://localhost:18083` EMQX dashboard (`admin`/`public`).

## Local development

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
export DATABASE_URL=postgresql+asyncpg://vmp_app:vmp_dev_password@localhost:5432/vision_parking
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --reload
```

Tests + lint:

```bash
.venv/bin/python -m pytest tests -q
.venv/bin/ruff check app alembic tests
```

## Architecture notes

- Two DB roles: `vmp` (superuser, migrations only, via `ALEMBIC_DATABASE_URL`) and
  `vmp_app` (least-privileged, bound by `FORCE ROW LEVEL SECURITY`).
- `tenant_session(tid)` sets `SET LOCAL app.current_tenant_id` inside each request
  transaction; `platform_session()` sets `app.platform_ctx` for platform bypass.
  Auth endpoints use a dedicated `auth_db` (platform context) since pre-auth lookups
  legitimately span tenants.
- Cookie auth: `vmp_access` (15 min), `vmp_refresh` (rotating, reuse detection revokes
  the session family), `vmp_csrf` (double-submit via `x-csrf-token`).
- `access_events` is partitioned quarterly, `gate_telemetry_logs` monthly; the worker
  creates future partitions hourly via SECURITY DEFINER functions.
- WebSocket `ws://.../ws/tenants/{tenantId}/barrier-telemetry` fans out MQTT events via
  Redis pub/sub channel `ws:tenant:{id}`.
