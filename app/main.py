from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import stripe_api, subscriptions_api, user_api
from app.core.config import settings
from app.core.database import Base, create_tables, engine
from app.models.subscription import Subscription

# Import models so SQLAlchemy knows them
from app.models.user import User

# Create tables on import
create_tables()

# Create FastAPI instance
app = FastAPI(
    title="FastAPI Stripe Integration",
    description="Complete FastAPI application with Stripe integration for subscription management",
    version="1.0.0",
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FastAPI Stripe Integration",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "users": "/api/users/",
            "stripe": "/api/stripe/",
            "subscriptions": "/api/subscriptions/",
        },
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "environment": settings.environment}


# Include routes
app.include_router(user_api.router, prefix="/api/users", tags=["Users"])
app.include_router(stripe_api.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(subscriptions_api.router, prefix="/api", tags=["Subscriptions"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
