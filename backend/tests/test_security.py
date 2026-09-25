"""Unit tests for core/security.py — no infra required."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pyotp

from app.core import security


def test_password_roundtrip():
    hashed = security.hash_password("Sup3r$ecret!")
    assert hashed.startswith("$2")
    assert security.verify_password("Sup3r$ecret!", hashed)
    assert not security.verify_password("wrong", hashed)


def test_password_over_72_bytes():
    # bcrypt truncates at 72 bytes — the sha256 pre-hash must handle any length
    long_pw = "A" * 200 + "!complex9"
    assert security.verify_password(long_pw, security.hash_password(long_pw))


def test_access_token_claims():
    uid, sid, tid = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    token = security.create_access_token(uid, "PLATFORM_ADMIN", sid, tid, role="PLATFORM_ADMIN")
    claims = security.decode_token(token)
    assert claims["sub"] == str(uid)
    assert claims["type"] == "access"
    assert claims["user_type"] == "PLATFORM_ADMIN"
    assert claims["sid"] == str(sid)
    assert claims["tenant_id"] == str(tid)
    assert claims["role"] == "PLATFORM_ADMIN"


def test_access_token_tamper_rejected():
    token = security.create_access_token(uuid.uuid4(), "MEMBER", uuid.uuid4())
    head, payload, sig = token.split(".")
    import base64
    import json

    decoded = json.loads(base64.urlsafe_b64decode(payload + "=="))
    decoded["role"] = "PLATFORM_ADMIN"
    forged = (
        head + "." + base64.urlsafe_b64encode(json.dumps(decoded).encode()).rstrip(b"=").decode() + "." + sig
    )
    try:
        security.decode_token(forged)
        raise AssertionError("forged token decoded")
    except pyjwt.InvalidTokenError:
        pass


def test_refresh_token_expiry():
    sid = uuid.uuid4()
    token, expires = security.create_refresh_token(sid)
    claims = security.decode_token(token)
    assert claims["sub"] == str(sid)
    assert claims["type"] == "refresh"
    assert expires > datetime.now(timezone.utc) + timedelta(days=6)


def test_short_token():
    token = security.create_short_token(str(uuid.uuid4()), "mfa_challenge", minutes=5)
    claims = security.decode_token(token)
    assert claims["type"] == "mfa_challenge"


def test_totp_fernet_roundtrip():
    secret = security.generate_totp_secret()
    enc = security.encrypt_totp_secret(secret)
    assert enc != secret
    assert security.decrypt_totp_secret(enc) == secret


def test_totp_verify():
    secret = security.generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert security.verify_totp(secret, code)
    assert not security.verify_totp(secret, "000000")
    assert not security.verify_totp(secret, "")


def test_totp_uri():
    uri = security.totp_uri("ABC123", "user@example.com")
    assert uri.startswith("otpauth://totp/")
    assert "user%40example.com" in uri or "user@example.com" in uri


def test_generate_api_key():
    raw, prefix, digest = security.generate_api_key("plt")
    assert raw.startswith("plt_")
    assert prefix == raw[:16]
    assert digest == security.hash_token(raw)


def test_csrf_token():
    t = security.generate_csrf_token()
    assert len(t) >= 32
    assert t != security.generate_csrf_token()


def test_parse_user_agent():
    browser, os_, device = security.parse_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    )
    assert browser == "Chrome"
    assert device is not None


def test_parse_user_agent_none():
    assert security.parse_user_agent(None) == (None, None, None)
