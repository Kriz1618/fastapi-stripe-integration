from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from .validators import validate_stripe_key


class Settings(BaseSettings):
    # App Configuration
    debug: bool = Field(default=True, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    secret_key: str = Field(default="dev-secret-key-for-testing", env="SECRET_KEY")

    # Database (SQLite local)
    database_url: str = Field(
        default="sqlite:///./data/database.db", env="DATABASE_URL"
    )

    stripe_publishable_key: str = Field(
        default="pk_test_placeholder", env="STRIPE_PUBLISHABLE_KEY"
    )
    stripe_secret_key: str = Field(
        default="sk_test_placeholder", env="STRIPE_SECRET_KEY"
    )
    stripe_webhook_secret: str = Field(
        default="whsec_placeholder", env="STRIPE_WEBHOOK_SECRET"
    )

    # URLs
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    api_url: str = Field(default="http://localhost:8000", env="API_URL")

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("stripe_webhook_secret")
    def validate_stripe_webhook_secret(cls, v):
        return validate_stripe_key(v, "webhook")

    @field_validator("stripe_secret_key")
    def validate_stripe_secret_key(cls, v):
        return validate_stripe_key(v, "secret")

    @field_validator("stripe_publishable_key")
    def validate_stripe_publishable_key(cls, v):
        return validate_stripe_key(v, "publishable")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields to avoid errors


# Global configuration instance
settings = Settings()
