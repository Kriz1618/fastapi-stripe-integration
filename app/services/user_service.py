import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Service class for handling user management and authentication operations"""

    def __init__(self):
        logger.info("UserService initialized")

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email address

        Args:
            db: Database session
            email: User email address

        Returns:
            User object if found, None otherwise
        """
        try:
            logger.info(f"Looking up user by email: {email}")
            user = db.query(User).filter(User.email == email).first()

            if user:
                logger.info(f"User found: {user.id}")
            else:
                logger.info(f"No user found with email: {email}")

            return user

        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise Exception(f"Database error: {str(e)}")

    def get_user_by_stripe_customer_id(
        self, db: Session, stripe_customer_id: str
    ) -> Optional[User]:
        """
        Get user by Stripe customer ID

        Args:
            db: Database session
            stripe_customer_id: Stripe customer ID

        Returns:
            User object if found, None otherwise
        """
        try:
            logger.info(f"Looking up user by Stripe customer ID: {stripe_customer_id}")
            user = (
                db.query(User)
                .filter(User.stripe_customer_id == stripe_customer_id)
                .first()
            )

            if user:
                logger.info(f"User found: {user.email}")
            else:
                logger.info(
                    f"No user found with Stripe customer ID: {stripe_customer_id}"
                )

            return user

        except Exception as e:
            logger.error(
                f"Error getting user by Stripe customer ID {stripe_customer_id}: {e}"
            )
            raise Exception(f"Database error: {str(e)}")

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        try:
            logger.info(f"Looking up user by ID: {user_id}")
            user = db.query(User).filter(User.id == user_id).first()

            if user:
                logger.info(f"User found: {user.email}")
            else:
                logger.info(f"No user found with ID: {user_id}")

            return user

        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise Exception(f"Database error: {str(e)}")

    def create_user(
        self, db: Session, email: str, full_name: str, password: str
    ) -> User:
        """
        Create a new user

        Args:
            db: Database session
            email: User email address
            full_name: User full name
            password: Plain text password (will be hashed)

        Returns:
            Created User object

        Raises:
            Exception: If user creation fails
        """
        try:
            logger.info(f"Creating new user: {email}")

            # Create user instance
            db_user = User(email=email, full_name=full_name)

            # Hash and set password
            db_user.set_password(password)

            # Save to database
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            logger.info(f"User created successfully: {db_user.id}")
            return db_user

        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            db.rollback()
            raise Exception(f"Failed to create user: {str(e)}")

    def register_user(
        self, db: Session, email: str, full_name: str, password: str
    ) -> User:
        """
        Register a new user (includes validation)

        Args:
            db: Database session
            email: User email address
            full_name: User full name
            password: Plain text password

        Returns:
            Created User object

        Raises:
            ValueError: If user already exists
            Exception: If registration fails
        """
        try:
            logger.info(f"Registering new user: {email}")

            # Check if user already exists
            existing_user = self.get_user_by_email(db, email)
            if existing_user:
                logger.warning(f"Registration failed - user already exists: {email}")
                raise ValueError("Email already registered")

            # Create the user
            user = self.create_user(db, email, full_name, password)

            logger.info(f"User registered successfully: {user.id}")
            return user

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error registering user {email}: {e}")
            raise Exception(f"Registration failed: {str(e)}")

    def get_all_users(self, db: Session) -> List[User]:
        """
        Get all users from the database

        Args:
            db: Database session

        Returns:
            List of User objects
        """
        try:
            logger.info("Fetching all users")
            users = db.query(User).all()
            logger.info(f"Found {len(users)} users")
            return users

        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise Exception(f"Failed to fetch users: {str(e)}")

    def authenticate_user(
        self, db: Session, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password

        Args:
            db: Database session
            email: User email address
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            logger.info(f"Authenticating user: {email}")

            # Get user by email
            user = self.get_user_by_email(db, email)
            if not user:
                logger.warning(f"Authentication failed - user not found: {email}")
                return None

            # Verify password
            if not user.verify_password(password):
                logger.warning(f"Authentication failed - invalid password for: {email}")
                return None

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Authentication failed - user inactive: {email}")
                return None

            logger.info(f"User authenticated successfully: {email}")
            return user

        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            return None

    def update_user(self, db: Session, user_id: int, **kwargs) -> Optional[User]:
        """
        Update user information

        Args:
            db: Database session
            user_id: User ID to update
            **kwargs: Fields to update

        Returns:
            Updated User object if successful, None if user not found
        """
        try:
            logger.info(f"Updating user: {user_id}")

            user = self.get_user_by_id(db, user_id)
            if not user:
                logger.warning(f"Update failed - user not found: {user_id}")
                return None

            # Update allowed fields
            allowed_fields = ["full_name", "is_active", "stripe_customer_id"]
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
                    logger.info(f"Updated {field} for user {user_id}")

            db.commit()
            db.refresh(user)

            logger.info(f"User updated successfully: {user_id}")
            return user

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            db.rollback()
            raise Exception(f"Failed to update user: {str(e)}")

    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """
        Deactivate a user account

        Args:
            db: Database session
            user_id: User ID to deactivate

        Returns:
            True if successful, False if user not found
        """
        try:
            logger.info(f"Deactivating user: {user_id}")

            user = self.update_user(db, user_id, is_active=False)
            if user:
                logger.info(f"User deactivated successfully: {user_id}")
                return True
            else:
                logger.warning(f"Deactivation failed - user not found: {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            raise Exception(f"Failed to deactivate user: {str(e)}")


# Global service instance
user_service = UserService()
