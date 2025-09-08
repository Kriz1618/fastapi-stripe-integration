from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.services.user_service import user_service

# Router
router = APIRouter()

# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user

    Args:
        user: User registration data
        db: Database session

    Returns:
        Created user information

    Raises:
        HTTPException: If email already exists or registration fails
    """
    try:
        # Use user service to register user
        db_user = user_service.register_user(
            db=db,
            email=user.email,
            full_name=user.full_name,
            password=user.password
        )

        return UserResponse.model_validate(db_user)

    except ValueError as e:
        # Handle validation errors (e.g., email already exists)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/users", response_model=list[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """
    Get all users (admin endpoint)

    Args:
        db: Database session

    Returns:
        List of all users

    Raises:
        HTTPException: If fetching users fails
    """
    try:
        # Use user service to get all users
        users = user_service.get_all_users(db)
        return [UserResponse.model_validate(user) for user in users]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID

    Args:
        user_id: User ID to fetch
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    try:
        user = user_service.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Update user information

    Args:
        user_id: User ID to update
        user_update: Fields to update
        db: Database session

    Returns:
        Updated user information

    Raises:
        HTTPException: If user not found or update fails
    """
    try:
        update_data = user_update.model_dump(exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        updated_user = user_service.update_user(db, user_id, **update_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse.model_validate(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/users/{user_id}")
async def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    Deactivate user account

    Args:
        user_id: User ID to deactivate
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or deactivation fails
    """
    try:
        # Use user service to deactivate user
        success = user_service.deactivate_user(db, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": f"User {user_id} deactivated successfully"}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
