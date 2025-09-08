#!/usr/bin/env python3
"""
Script to seed the database with sample data for testing
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the Python path so we can import our app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.core.database import Base
from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, Notification

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_sample_data():
    """Create sample data for testing"""
    print("🌱 Seeding database with sample data...")
    print("=" * 50)

    try:
        # Create engine and session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Create sample users
        users_data = [
            {
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "password123",
                "stripe_customer_id": "cus_sample_john"
            },
            {
                "email": "jane@example.com",
                "full_name": "Jane Smith",
                "password": "password123",
                "stripe_customer_id": "cus_sample_jane"
            },
            {
                "email": "bob@example.com",
                "full_name": "Bob Johnson",
                "password": "password123",
                "stripe_customer_id": "cus_sample_bob"
            }
        ]

        created_users = []
        for user_data in users_data:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing_user:
                user = User(
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=pwd_context.hash(user_data["password"]),
                    is_active=True,
                    stripe_customer_id=user_data["stripe_customer_id"]
                )
                db.add(user)
                created_users.append(user)

        db.commit()

        # Refresh users to get their IDs
        for user in created_users:
            db.refresh(user)

        print(f"✅ Created {len(created_users)} sample users")

        # Create sample subscriptions
        if created_users:
            subscriptions_data = [
                {
                    "user": created_users[0],
                    "stripe_subscription_id": "sub_sample_basic",
                    "stripe_price_id": "price_sample_basic",
                    "plan": "basic",
                    "status": "active",
                    "amount": 9.99,
                    "currency": "usd"
                },
                {
                    "user": created_users[1],
                    "stripe_subscription_id": "sub_sample_pro",
                    "stripe_price_id": "price_sample_pro",
                    "plan": "pro",
                    "status": "active",
                    "amount": 29.99,
                    "currency": "usd"
                }
            ]

            created_subscriptions = []
            for sub_data in subscriptions_data:
                # Check if subscription already exists
                existing_sub = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == sub_data["stripe_subscription_id"]
                ).first()

                if not existing_sub:
                    subscription = Subscription(
                        user_id=sub_data["user"].id,
                        stripe_subscription_id=sub_data["stripe_subscription_id"],
                        stripe_customer_id=sub_data["user"].stripe_customer_id,
                        stripe_price_id=sub_data["stripe_price_id"],
                        plan=sub_data["plan"],
                        status=sub_data["status"],
                        amount=sub_data["amount"],
                        currency=sub_data["currency"],
                        current_period_start=datetime.now(),
                        current_period_end=datetime.now() + timedelta(days=30)
                    )
                    db.add(subscription)
                    created_subscriptions.append(subscription)

            db.commit()

            # Refresh subscriptions to get their IDs
            for subscription in created_subscriptions:
                db.refresh(subscription)

            print(f"✅ Created {len(created_subscriptions)} sample subscriptions")

            # Create sample notifications
            if created_subscriptions:
                notifications_data = [
                    {
                        "user_id": created_subscriptions[0].user_id,
                        "subscription_id": created_subscriptions[0].id,
                        "type": "renewal_reminder",
                        "title": "Your Basic subscription will renew soon",
                        "message": "Your Basic subscription will renew in 3 days for $9.99 USD. Please ensure your payment method is up to date.",
                        "amount": 9.99,
                        "currency": "usd",
                        "renewal_date": datetime.now() + timedelta(days=3),
                        "is_read": False
                    },
                    {
                        "user_id": created_subscriptions[1].user_id,
                        "subscription_id": created_subscriptions[1].id,
                        "type": "renewal_reminder",
                        "title": "Your Pro subscription will renew soon",
                        "message": "Your Pro subscription will renew in 5 days for $29.99 USD. Please ensure your payment method is up to date.",
                        "amount": 29.99,
                        "currency": "usd",
                        "renewal_date": datetime.now() + timedelta(days=5),
                        "is_read": False
                    },
                    {
                        "user_id": created_subscriptions[0].user_id,
                        "subscription_id": created_subscriptions[0].id,
                        "type": "payment_success",
                        "title": "Payment successful",
                        "message": "Your payment of $9.99 USD has been processed successfully.",
                        "amount": 9.99,
                        "currency": "usd",
                        "is_read": True
                    }
                ]

                created_notifications = []
                for notif_data in notifications_data:
                    notification = Notification(**notif_data)
                    db.add(notification)
                    created_notifications.append(notification)

                db.commit()
                print(f"✅ Created {len(created_notifications)} sample notifications")

        db.close()

        print("\n📊 Sample Data Summary:")
        print("=" * 30)
        print(f"👥 Users: {len(created_users)}")
        print(f"💳 Subscriptions: {len(created_subscriptions) if 'created_subscriptions' in locals() else 0}")
        print(f"🔔 Notifications: {len(created_notifications) if 'created_notifications' in locals() else 0}")

        if created_users:
            print("\n👤 Sample Users:")
            for user in created_users:
                print(f"  - {user.email} (ID: {user.id})")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("🌱 FastAPI Stripe Integration - Database Seeding")
    print("=" * 60)

    create_sample_data()

    print("\n" + "=" * 60)
    print("✅ Database seeding completed!")
    print("🎯 You can now:")
    print("=" * 60)
    print("1. Start the application: python scripts/run.py")
    print("2. Login with sample users:")
    print("   - john@example.com / password123")
    print("   - jane@example.com / password123")
    print("   - bob@example.com / password123")
    print("3. Test notification endpoints")
    print("=" * 60)


if __name__ == "__main__":
    main()
