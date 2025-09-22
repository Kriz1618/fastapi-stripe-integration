from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    stripe_customer_id = Column(String, nullable=False)
    stripe_price_id = Column(String, nullable=False)
    plan = Column(String, nullable=False)  # "basic", "pro", "premium"
    status = Column(String, nullable=False)  # "active", "canceled", "past_due", etc.
    amount = Column(Float, nullable=False)
    currency = Column(String, default="usd")
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    user = relationship("User", back_populates="subscriptions")
    notifications = relationship("Notification", back_populates="subscription")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    type = Column(
        String, nullable=False
    )  # "renewal_reminder", "payment_failed", "subscription_canceled"
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    amount = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    renewal_date = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="notifications")
    subscription = relationship("Subscription", back_populates="notifications")
