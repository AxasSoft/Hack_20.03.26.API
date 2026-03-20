import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str = 'porto'
    SERVER_HOST: AnyHttpUrl = '0.0.0.0'
    BACKEND_CORS_ORIGINS: List[str] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    TOKEN_CLAIMS_EXTRA_FIELDS = ["exp", "nbf", "iat", "jti"]
    TOKEN_CHECKS = ["nbf"]

    ERROR_NOTIFIER_TOKEN = "5329457752:AAEpcb_FgorezISI3GsKfYGkJuoEVc_Xg8A"
    ERROR_NOTIFIER_RECIPIENTS = ["854939865", "1138544165", "408003762"]
    ERROR_NOTIFIER_CODES = [500]

    DOMAIN = os.getenv('DOMAIN', 'localhost')

    class Config:
        case_sensitive = True

    S3_SERVICE_NAME: str
    S3_ENDPOINTS_URL: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str

    FIREBASE_API_KEY: Optional[str]

    fcm_service_account_file = "mykrasnodar-a6b26-firebase-adminsdk-somhz-8b6661df1f.json"

    
    REDIS_URL: str
    CACHE_TTL: int

    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # dev test
    SUPERUSER_EMAIL: List[str] = ["s.pashov@axas.ru", "tour@soktur.ru", "d.pavlenko@axas.ru", "a.ozerov@axas.ru"]

    # ETG_KEY_ID: str
    # ETG_API_KEY: str


settings = Settings()
