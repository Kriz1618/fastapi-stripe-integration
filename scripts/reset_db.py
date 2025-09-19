#!/usr/bin/env python3
"""
Script to reset the database (drop and recreate all tables)
⚠️  WARNING: This will delete all data!
"""

import os
import sys

# Add the parent directory to the Python path so we can import our app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine

from app.core.config import settings
from app.core.database import Base
from app.models.subscription import Notification, Subscription
from app.models.user import User


def reset_database():
    """Drop and recreate all database tables"""
    print("⚠️  WARNING: This will delete ALL data in the database!")
    print("=" * 60)

    # Ask for confirmation
    confirmation = (
        input("Are you sure you want to continue? (yes/no): ").lower().strip()
    )

    if confirmation not in ["yes", "y"]:
        print("❌ Operation cancelled.")
        return

    try:
        # Create engine
        engine = create_engine(settings.database_url)

        print("\n🗑️  Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Tables dropped successfully!")

        print("\n🗃️  Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")

        print("\n📋 Tables recreated:")
        print("  - users")
        print("  - subscriptions")
        print("  - notifications")

        print(f"\n📂 Database location: {settings.database_url}")

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("🔄 FastAPI Stripe Integration - Database Reset")
    print("=" * 60)

    reset_database()

    print("\n" + "=" * 60)
    print("✅ Database reset completed!")
    print("🎯 Next Steps:")
    print("=" * 60)
    print("1. Start the application: python scripts/run.py")
    print("2. Create a user via: POST /api/auth/register")
    print("3. Create Stripe customer: POST /api/stripe/create-customer")
    print("=" * 60)


if __name__ == "__main__":
    main()
