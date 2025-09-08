#!/usr/bin/env python3
"""
Script to create and initialize the database tables
"""

import sys
import os

# Add the parent directory to the Python path so we can import our app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.core.database import Base
from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, Notification


def create_database():
    """Create all database tables"""
    print("🗃️  Creating database tables...")
    print("=" * 50)

    try:
        # Create engine
        engine = create_engine(settings.database_url)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ Database tables created successfully!")
        print("\n📋 Tables created:")
        print("  - users")
        print("  - subscriptions")
        print("  - notifications")

        print(f"\n📂 Database location: {settings.database_url}")

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("🚀 FastAPI Stripe Integration - Database Setup")
    print("=" * 60)

    create_database()

    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("=" * 60)
    print("1. Start the application: python scripts/run.py")
    print("2. Create a user via: POST /api/auth/register")
    print("3. Create Stripe customer: POST /api/stripe/create-customer")
    print("4. Test webhooks with ngrok")
    print("=" * 60)


if __name__ == "__main__":
    main()
