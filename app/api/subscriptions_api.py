from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter()


class SubscriptionStatus(str, Enum):
    """Subscription status options"""
    active = "active"
    canceled = "canceled"
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    past_due = "past_due"
    trialing = "trialing"
    unpaid = "unpaid"


class SortBy(str, Enum):
    """Sort options for subscriptions"""
    created_at = "created_at"
    updated_at = "updated_at"
    current_period_start = "current_period_start"
    current_period_end = "current_period_end"
    status = "status"


class SortOrder(str, Enum):
    """Sort order options"""
    asc = "asc"
    desc = "desc"


class SubscriptionResponse(BaseModel):
    """Subscription response model"""
    id: int
    stripe_subscription_id: str
    user_id: int
    user_email: Optional[str] = None
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Response model for subscription list"""
    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


@router.get("/subscriptions", response_model=SubscriptionListResponse)
async def list_subscriptions(
    db: Session = Depends(get_db),
    status: Optional[SubscriptionStatus] = Query(None, description="Filter by subscription status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter subscriptions created after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter subscriptions created before this date"),
    sort_by: SortBy = Query(SortBy.created_at, description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.desc, description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List subscriptions with filtering and sorting options

    - **status**: Filter by subscription status (active, canceled, etc.)
    - **user_id**: Filter by specific user ID
    - **start_date**: Filter subscriptions created after this date
    - **end_date**: Filter subscriptions created before this date
    - **sort_by**: Field to sort by (created_at, updated_at, status, etc.)
    - **sort_order**: Sort order (asc or desc)
    - **page**: Page number for pagination
    - **per_page**: Number of items per page (max 100)
    """
    try:
        # Build base query with user join
        query = db.query(Subscription).join(User, Subscription.user_id == User.id)

        # Apply filters
        if status:
            query = query.filter(Subscription.status == status.value)

        if user_id:
            query = query.filter(Subscription.user_id == user_id)

        if start_date:
            query = query.filter(Subscription.created_at >= start_date)

        if end_date:
            query = query.filter(Subscription.created_at <= end_date)

        # Get total count before applying pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(Subscription, sort_by.value)
        if sort_order == SortOrder.desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (page - 1) * per_page
        subscriptions = query.offset(offset).limit(per_page).all()

        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page

        # Format response with user email
        subscription_responses = []
        for sub in subscriptions:
            user = db.query(User).filter(User.id == sub.user_id).first()
            subscription_responses.append(
                SubscriptionResponse(
                    id=sub.id,
                    stripe_subscription_id=sub.stripe_subscription_id,
                    user_id=sub.user_id,
                    user_email=user.email if user else None,
                    status=sub.status,
                    current_period_start=sub.current_period_start,
                    current_period_end=sub.current_period_end,
                    created_at=sub.created_at,
                    updated_at=sub.updated_at
                )
            )

        return SubscriptionListResponse(
            subscriptions=subscription_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving subscriptions: {str(e)}"
        )


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific subscription by ID"""
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found"
            )

        # Get user email
        user = db.query(User).filter(User.id == subscription.user_id).first()

        return SubscriptionResponse(
            id=subscription.id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            user_id=subscription.user_id,
            user_email=user.email if user else None,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving subscription: {str(e)}"
        )
