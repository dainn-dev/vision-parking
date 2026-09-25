from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Vehicle Governance Platform API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # app connects as least-privileged vmp_app so FORCE RLS binds it;
    # migrations use ALEMBIC_DATABASE_URL (postgres superuser vmp)
    database_url: str = "postgresql+asyncpg://vmp_app:vmp_app_dev_password@localhost:5432/vision_parking"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "dev-insecure-secret-change-me"
    totp_encryption_key: str = "dev-only-fernet-key-replace-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cookie_secure: bool = False
    cookie_domain: str | None = None
    cookie_samesite: str = "lax"

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_client_prefix: str = "vmp-api"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin_dev"
    s3_bucket: str = "vision-parking"
    s3_region: str = "us-east-1"
    s3_secure: bool = False
    plate_image_retention_days: int = 90

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "no-reply@vehicle.platform.internal"
    smtp_from_name: str = "Platform Governance Control Center"
    smtp_starttls: bool = False

    platform_name: str = "Vehicle Governance Platform"
    public_base_url: str = "http://localhost:8000"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    seed_admin_email: str = "anh.nh@kyanon.digital"
    seed_admin_password: str = "ChangeMe!2026"
    seed_tenant_password: str = "TenantDemo!2026"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
