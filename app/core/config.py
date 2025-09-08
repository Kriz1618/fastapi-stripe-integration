from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List


class Settings(BaseSettings):
    # App Configuration
    debug: bool = Field(default=True, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    secret_key: str = Field(default="dev-secret-key-for-testing", env="SECRET_KEY")

    # Database (SQLite local)
    database_url: str = Field(default="sqlite:///./data/database.db", env="DATABASE_URL")

    # Stripe (valores por defecto para que no falle)
    stripe_publishable_key: str = Field(default="pk_test_placeholder", env="STRIPE_PUBLISHABLE_KEY")
    stripe_secret_key: str = Field(default="sk_test_placeholder", env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="whsec_placeholder", env="STRIPE_WEBHOOK_SECRET")

    # URLs
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    api_url: str = Field(default="http://localhost:8000", env="API_URL")

    # Stripe Price IDs (valores de ejemplo)
    stripe_basic_price_id: str = Field(default="price_basic_test", env="STRIPE_BASIC_PRICE_ID")
    stripe_pro_price_id: str = Field(default="price_pro_test", env="STRIPE_PRO_PRICE_ID")
    stripe_premium_price_id: str = Field(default="price_premium_test", env="STRIPE_PREMIUM_PRICE_ID")

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]

    @field_validator('stripe_webhook_secret')
    def validate_stripe_webhook_secret(cls, v):
        if v == "whsec_placeholder":
            raise ValueError("STRIPE_WEBHOOK_SECRET debe ser configurado con un valor real de Stripe Dashboard")
        if not v.startswith("whsec_"):
            raise ValueError("STRIPE_WEBHOOK_SECRET debe empezar con 'whsec_'")
        return v

    @field_validator('stripe_secret_key')
    def validate_stripe_secret_key(cls, v):
        if v == "sk_test_placeholder":
            raise ValueError("STRIPE_SECRET_KEY debe ser configurado con un valor real de Stripe Dashboard")
        if not (v.startswith("sk_test_") or v.startswith("sk_live_")):
            raise ValueError("STRIPE_SECRET_KEY debe empezar con 'sk_test_' o 'sk_live_'")
        return v

    @field_validator('stripe_publishable_key')
    def validate_stripe_publishable_key(cls, v):
        if v == "pk_test_placeholder":
            raise ValueError("STRIPE_PUBLISHABLE_KEY debe ser configurado con un valor real de Stripe Dashboard")
        if not (v.startswith("pk_test_") or v.startswith("pk_live_")):
            raise ValueError("STRIPE_PUBLISHABLE_KEY debe empezar con 'pk_test_' o 'pk_live_'")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignorar campos extra para evitar errores


# Instancia global de configuración
settings = Settings()
