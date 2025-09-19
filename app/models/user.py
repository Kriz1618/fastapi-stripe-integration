from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Stripe fields
    stripe_customer_id = Column(String, unique=True, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verificar password"""
        return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generar hash de password"""
        return pwd_context.hash(password)

    def set_password(self, password: str):
        """Establecer password hasheado"""
        self.hashed_password = self.get_password_hash(password)

    def __repr__(self):
        return f"<User(email='{self.email}')>"
