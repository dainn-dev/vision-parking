import uuid

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    otp_code: str | None = Field(default=None, max_length=10)
    tenant_code: str | None = None


class MfaChallengeRequest(CamelModel):
    challenge_token: str
    otp_code: str = Field(min_length=6, max_length=10)


class UserInfo(CamelModel):
    id: uuid.UUID
    name: str
    email: str
    user_type: str
    role: str | None = None
    tenant_id: uuid.UUID | None = None
    mfa_enabled: bool = False


class LoginResponse(CamelModel):
    status: str  # AUTHENTICATED | MFA_REQUIRED | MFA_ENROLLMENT_REQUIRED
    user: UserInfo | None = None
    challenge_token: str | None = None
    mfa_enroll_token: str | None = None
    message: str | None = None


class MfaEnrollStart(CamelModel):
    secret: str
    otpauth_uri: str


class MfaEnrollVerify(CamelModel):
    otp_code: str = Field(min_length=6, max_length=10)


class MessageResponse(CamelModel):
    message: str
