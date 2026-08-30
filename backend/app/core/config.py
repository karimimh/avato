from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_name: str = "Avato"
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://avato:avato-dev-password@localhost:5432/avato"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_public_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "avato-local"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_use_ssl: bool = False
    s3_server_side_encryption: str = ""

    openai_api_key: str = ""

    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    payment_provider: str = "local"
    payment_callback_url: str = "http://localhost:8080/api/payments/callback"
    payment_local_secret: str = "local-payment-secret-change-me"
    zarinpal_merchant_id: str = ""
    zarinpal_sandbox: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
