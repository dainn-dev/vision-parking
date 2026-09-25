"""initial schema — all tables, partitions, RLS, app role

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-25

Creates every ORM table except the two range-partitioned tables
(``gate_telemetry_logs`` monthly, ``access_events`` quarterly), which are
emitted as hand-written PARTITION BY RANGE DDL with ensure_*_partition()
SECURITY DEFINER functions. Tenant-scoped tables get ENABLE + FORCE ROW
LEVEL SECURITY keyed on ``app.current_tenant_id`` with an
``app.platform_ctx='platform'`` bypass for platform/worker operations.

A least-privileged login role ``vmp_app`` is provisioned for the API and
worker: it is not the table owner and is not a superuser, so FORCE RLS
fully binds it.
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

APP_ROLE = "vmp_app"
APP_ROLE_PASSWORD = "vmp_app_dev_password"

PARTITIONED = ("gate_telemetry_logs", "access_events")

TENANT_TABLES = (
    "tenant_users",
    "tenant_sites",
    "edge_devices",
    "site_lanes",
    "barrier_gates",
    "barrier_incidents",
    "registered_vehicles",
    "tenant_access_rules",
    "gate_commands",
    "vehicle_import_jobs",
    "gate_telemetry_logs",
    "access_events",
)

TELEMETRY_DDL = [
    """CREATE TABLE gate_telemetry_logs (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    site_id UUID,
    gate_id UUID,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    source VARCHAR(16) NOT NULL DEFAULT 'EDGE',
    PRIMARY KEY (recorded_at)
) PARTITION BY RANGE (recorded_at)""",
    "CREATE INDEX ix_gate_telemetry_logs_tenant_id ON gate_telemetry_logs (tenant_id)",
    "CREATE INDEX ix_gate_telemetry_logs_gate_id ON gate_telemetry_logs (gate_id)",
]

ACCESS_EVENTS_DDL = [
    """CREATE TABLE access_events (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    site_id UUID,
    lane_id UUID,
    gate_id UUID,
    vehicle_id UUID,
    edge_device_id UUID,
    plate_raw VARCHAR(32),
    plate_normalized VARCHAR(32),
    direction VARCHAR(16) NOT NULL DEFAULT 'INBOUND',
    decision VARCHAR(16) NOT NULL DEFAULT 'ALLOWED',
    decision_reason VARCHAR(255),
    rule_id UUID,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    plate_image_url VARCHAR(512),
    overview_image_url VARCHAR(512),
    snapshot JSONB,
    PRIMARY KEY (occurred_at)
) PARTITION BY RANGE (occurred_at)""",
    "CREATE INDEX ix_access_events_tenant_id ON access_events (tenant_id)",
    "CREATE INDEX ix_access_events_gate_id ON access_events (gate_id)",
    "CREATE INDEX ix_access_events_plate_normalized ON access_events (plate_normalized)",
]

PARTITION_FUNCS = [
    """CREATE OR REPLACE FUNCTION ensure_telemetry_partition(ts TIMESTAMPTZ) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $fn$
DECLARE
    m date := date_trunc('month', ts)::date;
    pname text := 'gate_telemetry_logs_' || to_char(m, 'YYYY_MM');
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF gate_telemetry_logs FOR VALUES FROM (%L) TO (%L)',
        pname, m, (m + interval '1 month')::date
    );
END
$fn$""",
    """CREATE OR REPLACE FUNCTION ensure_access_event_partition(ts TIMESTAMPTZ) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $fn$
DECLARE
    q date := date_trunc('quarter', ts)::date;
    pname text := 'access_events_' || to_char(q, 'YYYY') || '_q' || to_char(q, 'Q');
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF access_events FOR VALUES FROM (%L) TO (%L)',
        pname, q, (q + interval '3 months')::date
    );
END
$fn$""",
]

TENANT_PREDICATE = (
    "(tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid "
    "OR current_setting('app.platform_ctx', true) = 'platform')"
)


def upgrade() -> None:
    from app.models import Base

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # least-privileged application role
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_PASSWORD}';
            END IF;
        END $$;
        """
    )

    bind = op.get_bind()
    for table in Base.metadata.sorted_tables:
        if table.name not in PARTITIONED:
            table.create(bind, checkfirst=True)

    for stmt in TELEMETRY_DDL + ACCESS_EVENTS_DDL + PARTITION_FUNCS:
        op.execute(stmt)

    # current + lookahead partitions
    for stmt in (
        "SELECT ensure_telemetry_partition(now())",
        "SELECT ensure_telemetry_partition(now() + interval '1 month')",
        "SELECT ensure_telemetry_partition(now() + interval '2 months')",
        "SELECT ensure_access_event_partition(now())",
        "SELECT ensure_access_event_partition(now() + interval '3 months')",
        "SELECT ensure_access_event_partition(now() + interval '6 months')",
    ):
        op.execute(stmt)

    # RLS on tenant-scoped tables
    for tbl in TENANT_TABLES:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tbl} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {tbl} USING {TENANT_PREDICATE} WITH CHECK {TENANT_PREDICATE}"
        )

    # grants
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT EXECUTE ON FUNCTION ensure_telemetry_partition(TIMESTAMPTZ) TO {APP_ROLE}")
    op.execute(f"GRANT EXECUTE ON FUNCTION ensure_access_event_partition(TIMESTAMPTZ) TO {APP_ROLE}")
    # partitions created later by the migration role must stay accessible
    # (omitting FOR ROLE applies the defaults to the current role)
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE}"
    )


def downgrade() -> None:
    from app.models import Base

    for tbl in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {tbl}")
    bind = op.get_bind()
    for table in reversed(Base.metadata.sorted_tables):
        if table.name in PARTITIONED:
            op.execute(f"DROP TABLE IF EXISTS {table.name} CASCADE")
        else:
            table.drop(bind, checkfirst=True)
    op.execute("DROP FUNCTION IF EXISTS ensure_telemetry_partition(TIMESTAMPTZ)")
    op.execute("DROP FUNCTION IF EXISTS ensure_access_event_partition(TIMESTAMPTZ)")
    op.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
