from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VULNMNO_", extra="ignore")

    env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 30 * 24 * 3600
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    password_reset_ttl_seconds: int = 900
    # Training-lab default: the password-reset code is deterministic so
    # trainees can run the §9 "forgot password" journey without scraping
    # log lines. Per-customer overrides are honoured via
    # Customer.otp_fixed_code (the same field that pins the OTP login
    # code). Set to "" to revert to a random 6-digit code per request.
    password_reset_fixed_code: str = "123456"
    idempotency_ttl_seconds: int = 24 * 3600

    uploads_dir: Path = Path("./uploads")
    attachment_max_bytes: int = 10 * 1024 * 1024

    cors_origins: list[str] = ["http://10.0.2.2", "http://localhost", "http://127.0.0.1"]

    seed_on_startup: bool = True
    seed_phase2_on_startup: bool = True

    # ---------- Phase 2: admin portal ----------
    admin_session_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    admin_session_max_age_seconds: int = 8 * 3600
    admin_csrf_token_bytes: int = 32

    # ---------- Phase 2: gateway drivers ----------
    payment_driver: Literal["dev", "stripe"] = "dev"
    stripe_secret_key: str = ""
    stripe_base_url: str = "https://api.stripe.com"

    provisioning_driver: Literal["dev", "http"] = "dev"
    provisioning_url: str = ""

    push_driver: Literal["dev", "fcm"] = "dev"
    fcm_credentials_path: str = ""

    # ---------- Phase 2: rate limiting ----------
    rate_limit_enabled: bool = True

    # ---------- Phase 2: i18n ----------
    default_locale: Literal["en", "es"] = "en"
    i18n_catalog_path: Path = Path("./app/i18n_catalog.yaml")

    # ---------- Phase 2: campaign scheduler ----------
    campaign_scheduler_interval_seconds: int = 3600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
