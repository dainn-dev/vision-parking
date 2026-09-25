"""App-level contract tests (no DB needed — lifespan is skipped)."""

from fastapi.testclient import TestClient

from app.main import app


def test_healthz():
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_api_health():
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_error_envelope_unauthorized():
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/api/v1/platform/tenants")
    assert r.status_code in (401, 403)
    body = r.json()
    assert "error" in body
    assert body["error"]["code"]
    assert body["error"]["message"]


def test_request_id_header():
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/healthz")
    assert r.headers.get("x-request-id", "").startswith("req-")
