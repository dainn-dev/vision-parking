"""Schema contract tests — camelCase aliasing & pagination envelope."""

import uuid
from datetime import datetime, timezone

from app.core.pagination import Page, PageParams
from app.schemas.platform import TenantOut, TenantStatistics
from app.schemas.tenant import VehicleOut


def test_tenant_out_camel_serialization():
    t = TenantOut(
        id=uuid.uuid4(),
        name="Acme",
        code="ACME",
        email="a@b.c",
        phone=None,
        timezone="UTC",
        status="ACTIVE",
        administrator=None,
        statistics=TenantStatistics(
            users_count=1,
            vehicles_count=2,
            cameras_count=3,
            gates_count=4,
            edge_devices_count=5,
            events_count=6,
            storage_used_gb=0.5,
        ),
        created_at=datetime.now(timezone.utc),
        last_activity_at=None,
    )
    data = t.model_dump(by_alias=True)
    assert "lastActivityAt" in data
    assert "createdAt" in data
    assert data["statistics"]["usersCount"] == 1
    assert data["statistics"]["storageUsedGb"] == 0.5
    assert "snake_case" not in "".join(data.keys())


def test_vehicle_out_alias():
    v = VehicleOut(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        plate_raw="30A-12345",
        plate_normalized="30A12345",
        owner_name=None,
        owner_type="STAFF",
        brand_model=None,
        color=None,
        status="ACTIVE",
        valid_from=None,
        valid_until=None,
        created_at=datetime.now(timezone.utc),
    )
    data = v.model_dump(by_alias=True)
    assert data["plateNormalized"] == "30A12345"
    assert data["ownerType"] == "STAFF"


def test_page_envelope():
    page = Page[int](items=[1, 2], total=10, page=1, page_size=2)
    data = page.model_dump(by_alias=True)
    assert data == {"items": [1, 2], "total": 10, "page": 1, "pageSize": 2}


def test_page_params_offset():
    p = PageParams(page=2, page_size=25)
    assert p.page_size == 25
    assert p.offset == 25
