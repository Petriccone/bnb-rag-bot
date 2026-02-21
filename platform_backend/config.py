"""
Configuração do platform backend (variáveis de ambiente).
Usa só os.environ para não depender de pydantic_settings na Vercel.
"""
import os
from functools import lru_cache
from types import SimpleNamespace


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, "").strip() or default


@lru_cache
def get_settings():
    return SimpleNamespace(
        database_url=_env("DATABASE_URL") or _env("PLATFORM_DATABASE_URL"),
        jwt_secret=_env("PLATFORM_JWT_SECRET", "change-me-in-production"),
        jwt_algorithm="HS256",
        jwt_expire_minutes=60,
        jwt_refresh_expire_days=30,
        stripe_secret_key=_env("STRIPE_SECRET_KEY"),
        stripe_webhook_secret=_env("STRIPE_WEBHOOK_SECRET"),
        stripe_starter_price_id=_env("STRIPE_STARTER_PRICE_ID"),
        stripe_growth_price_id=_env("STRIPE_GROWTH_PRICE_ID"),
        stripe_business_price_id=_env("STRIPE_BUSINESS_PRICE_ID"),
        stripe_enterprise_price_id=_env("STRIPE_ENTERPRISE_PRICE_ID"),
        upload_dir=_env("PLATFORM_UPLOAD_DIR") or ("/tmp/uploads" if os.environ.get("VERCEL") else ".tmp/uploads"),
    )
