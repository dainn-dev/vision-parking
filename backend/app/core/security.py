"""Password hashing, JWT, TOTP and field-level encryption helpers."""

import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pyotp
from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()

ACCESS_COOKIE = "vmp_access"
REFRESH_COOKIE = "vmp_refresh"
CSRF_COOKIE = "vmp_csrf"
CSRF_HEADER = "x-csrf-token"


# ---------------------------------------------------------------- passwords


def hash_password(password: str) -> str:
    # bcrypt only uses the first 72 bytes; pre-hash to support longer inputs.
    digest = hashlib.sha256(password.encode()).digest()
    return bcrypt.hashpw(base64.b64encode(digest), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    digest = hashlib.sha256(password.encode()).digest()
    try:
        return bcrypt.checkpw(base64.b64encode(digest), password_hash.encode())
    except ValueError:
        return False


# ---------------------------------------------------------------- JWT


def _encode(subject: str, token_type: str, ttl: timedelta, extra: dict | None = None) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + ttl
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm), expires


def create_access_token(
    user_id: uuid.UUID,
    user_type: str,
    session_id: uuid.UUID,
    tenant_id: uuid.UUID | None = None,
    role: str | None = None,
) -> str:
    token, _ = _encode(
        str(user_id),
        "access",
        timedelta(minutes=settings.access_token_minutes),
        {
            "user_type": user_type,
            "sid": str(session_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "role": role,
        },
    )
    return token


def create_refresh_token(session_id: uuid.UUID) -> tuple[str, datetime]:
    return _encode(str(session_id), "refresh", timedelta(days=settings.refresh_token_days))


def create_short_token(subject: str, token_type: str, minutes: int = 5, extra: dict | None = None) -> str:
    token, _ = _encode(subject, token_type, timedelta(minutes=minutes), extra)
    return token


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def generate_api_key(prefix: str = "vmp") -> tuple[str, str, str]:
    """Returns (plaintext_key, key_prefix, key_hash). Show plaintext once."""

    raw = f"{prefix}_{secrets.token_urlsafe(24)}"
    return raw, raw[:16], hash_token(raw)


# ---------------------------------------------------------------- TOTP / MFA


def _fernet() -> Fernet:
    key = settings.totp_encryption_key
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        # Derive a valid fernet key from arbitrary dev secrets.
        derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        return Fernet(derived)


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def encrypt_totp_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_totp_secret(enc: str) -> str:
    return _fernet().decrypt(enc.encode()).decode()


def totp_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.platform_name)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    if not code or not code.strip().isdigit():
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=window)


# ---------------------------------------------------------------- misc


def client_ip(request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def parse_user_agent(ua: str | None) -> tuple[str | None, str | None, str | None]:
    """Very small UA → (browser, os, device) splitter; details stay in raw UA."""

    if not ua:
        return None, None, None
    browser = None
    for name in ("Edg", "Chrome", "Safari", "Firefox", "PostmanRuntime", "python-requests", "curl"):
        if name in ua:
            browser = "Edge" if name == "Edg" else name
            break
    os_name = None
    for name in ("Windows", "Mac OS", "Linux", "iPhone", "Android"):
        if name in ua:
            os_name = {"Mac OS": "macOS", "iPhone": "iOS"}.get(name, name)
            break
    device = ua.split("/")[0][:120]
    return browser, os_name, device
