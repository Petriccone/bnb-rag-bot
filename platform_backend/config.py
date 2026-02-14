"""
Configuração do platform backend (variáveis de ambiente).
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = ""
    jwt_secret: str = os.environ.get("PLATFORM_JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    upload_dir: str = os.environ.get("PLATFORM_UPLOAD_DIR", ".tmp/uploads")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
