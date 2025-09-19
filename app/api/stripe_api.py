import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.subscription import Notification, Subscription
from app.models.user import User
from app.services.stripe_service import stripe_service
from app.services.user_service import user_service

logger = logging.getLogger(__name__)

# Router
router = APIRouter()


# Pydantic models
class CreateCustomerRequest(BaseModel):
    user_id: int


class CreateCheckoutRequest(BaseModel):
    user_id: int
    plan_id: str


class ProductInfo(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price_id: str
    price: int  # in cents
    currency: str


class ProductsResponse(BaseModel):
    products: List[ProductInfo]


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    id: int
    plan: str
    status: str
    amount: float
    currency: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    stripe_subscription_id: str

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    amount: Optional[float]
    currency: Optional[str]
    renewal_date: Optional[datetime]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/create-customer")
async def create_stripe_customer(
    request: CreateCustomerRequest, db: Session = Depends(get_db)
):
    """Create a Stripe customer for a user"""
    # Find user using auth service
    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"Creating stripe customer for user: {user.full_name}-{user.email}")

    logger.info(f"Creating stripe customer for user: {user.full_name}-{user.email}")
    if user.stripe_customer_id:
        return {
            "message": "Customer already exists",
            "customer_id": user.stripe_customer_id,
        }

    try:
        # Create customer in Stripe
        customer_id = await stripe_service.create_customer(user.email, user.full_name)

        # Save customer_id in database using auth service
        user_service.update_user(db, user.id, stripe_customer_id=customer_id)

        return {"message": "Customer created successfully", "customer_id": customer_id}

    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error creating customer: {str(e)}"
        )


@router.get("/plans", response_model=ProductsResponse)
async def get_products():
    """Get products from Stripe"""
    products_data = await stripe_service.get_products()
    products = [ProductInfo(**product) for product in products_data]
    return ProductsResponse(products=products)


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest, db: Session = Depends(get_db)
):
    """Create checkout session for subscription"""
    # Find user
    user = user_service.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400, detail="User doesn't have Stripe customer ID"
        )

    try:
        product = await stripe_service.get_product_by_id(request.plan_id)
        if not product:
            raise HTTPException(status_code=400, detail="Invalid plan")
        price_id = product["price_id"]

        # Create checkout session
        checkout_data = await stripe_service.create_checkout_session(
            customer_id=user.stripe_customer_id,
            price_id=price_id,
            success_url=f"{settings.frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/cancel",
        )

        return CheckoutResponse(
            checkout_url=checkout_data["url"], session_id=checkout_data["session_id"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating checkout: {str(e)}"
        )


@router.get("/subscription/{subscription_id}")
async def get_subscription_info(subscription_id: str):
    """Get subscription information"""
    try:
        subscription_data = await stripe_service.get_subscription(subscription_id)
        return subscription_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting subscription: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        # Verify and construct event
        event = stripe_service.construct_webhook_event(payload, sig_header)

        # Handle different event types
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"], db)

        elif event["type"] == "invoice.payment_succeeded":
            await handle_payment_succeeded(event["data"]["object"], db)

        elif event["type"] == "invoice.upcoming":
            await handle_invoice_upcoming(event["data"]["object"], db)

        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"], db)

        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"], db)

        else:
            logger.info(f"Unhandled event type: {event['type']}")

        return {"status": "success"}

    except ValueError as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/user/{user_id}/subscriptions", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    """Get user subscriptions"""
    # Verify user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get subscriptions
    subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    return [SubscriptionResponse.model_validate(sub) for sub in subscriptions]


@router.get("/user/{user_id}/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    """Get user notifications"""
    # Verify user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get notifications ordered by date (newest first)
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [NotificationResponse.model_validate(notif) for notif in notifications]


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int, db: Session = Depends(get_db)
):
    """Mark notification as read"""
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}


@router.put("/user/{user_id}/notifications/read-all")
async def mark_all_notifications_as_read(user_id: int, db: Session = Depends(get_db)):
    """Mark all user notifications as read"""
    # Verify user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark all notifications as read
    db.query(Notification).filter(
        Notification.user_id == user_id, Notification.is_read.is_(False)
    ).update({"is_read": True})

    db.commit()

    return {"message": "All notifications marked as read"}


# Helper functions for webhook handling
async def handle_checkout_completed(session, db: Session):
    """Handle checkout completed - create subscription"""
    try:
        logger.info(f"Processing checkout completed: {session.get('id', 'unknown')}")

        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        if not customer_id:
            logger.error("No customer_id found in session")
            return

        if not subscription_id:
            logger.error("No subscription_id found in session")
            return

        # Find user by customer_id
        user = user_service.get_user_by_stripe_customer_id(db, customer_id)
        if not user:
            logger.error(f"User not found for customer_id: {customer_id}")
            return

        # Get subscription data from Stripe
        stripe_sub = await stripe_service.get_subscription(subscription_id)
        logger.info(f"Retrieved subscription data: {stripe_sub.get('id', 'unknown')}")

        # Determine plan based on price_id
        price_id = None
        if stripe_sub.get("items") and stripe_sub["items"].get("data"):
            items = stripe_sub["items"]["data"]
            if len(items) > 0 and items[0].get("price"):
                price_id = items[0]["price"].get("id")

        plan = await stripe_service.get_product_by_price_id(price_id)
        logger.info(f"Determined plan: {plan} from price_id: {price_id}")

        # Get price information
        price_info = await stripe_service.get_price_info(price_id) if price_id else None

        # Validate required data before creating subscription
        current_period_start = stripe_sub.get("current_period_start")
        current_period_end = stripe_sub.get("current_period_end")

        if not current_period_start or not current_period_end:
            logger.error(
                f"Missing period data in subscription: start={current_period_start}, end={current_period_end}"
            )
            return

        # Create subscription in database
        db_subscription = Subscription(
            user_id=user.id,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            stripe_price_id=price_id or "unknown",
            plan=plan["name"],
            status=stripe_sub.get("status", "unknown"),
            current_period_start=datetime.fromtimestamp(current_period_start),
            current_period_end=datetime.fromtimestamp(current_period_end),
            amount=price_info.get("amount", 0) if price_info else 0,
            currency=price_info.get("currency", "usd") if price_info else "usd",
        )

        db.add(db_subscription)
        db.commit()

        logger.info(f"Subscription created for user {user.id}: {subscription_id}")

    except Exception as e:
        logger.error(f"Error handling checkout completed: {e}")


async def handle_payment_succeeded(invoice, db: Session):
    """Handle successful payment - update subscription"""
    try:
        logger.info(
            f"Processing payment succeeded for invoice: {invoice.get('id', 'unknown')}"
        )

        # Use service method to extract subscription_id
        subscription_id = stripe_service.extract_subscription_id_from_invoice(invoice)

        if not subscription_id:
            logger.error(
                f"No subscription found in invoice: {invoice.get('id', 'unknown')}"
            )
            return

        # Update subscription in database
        db_subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == subscription_id)
            .first()
        )

        if db_subscription:
            db_subscription.status = "active"
            db_subscription.updated_at = datetime.now()
            db.commit()
            logger.info(f"Payment succeeded for subscription: {subscription_id}")
        else:
            logger.warning(f"Subscription not found in database: {subscription_id}")

    except Exception as e:
        logger.error(f"Error handling payment succeeded: {e}")


async def handle_invoice_upcoming(invoice, db: Session):
    """Handle upcoming invoice - subscription about to renew"""
    try:
        logger.info(f"Processing upcoming invoice: {invoice.get('id', 'unknown')}")

        # Extract subscription_id from invoice
        subscription_id = stripe_service.extract_subscription_id_from_invoice(invoice)

        if not subscription_id:
            logger.error(
                f"No subscription found in upcoming invoice: {invoice.get('id', 'unknown')}"
            )
            return

        # Find subscription in database
        db_subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == subscription_id)
            .first()
        )

        if not db_subscription:
            logger.warning(f"Subscription not found in database: {subscription_id}")
            return

        # Find associated user
        user = user_service.get_user_by_id(db, db_subscription.user_id)
        if not user:
            logger.error(f"User not found for subscription: {subscription_id}")
            return

        # Upcoming invoice information
        invoice_amount = invoice.get("amount_due", 0) / 100
        currency = invoice.get("currency", "usd").upper()
        period_start = invoice.get("period_start")
        period_end = invoice.get("period_end")

        # Calculate days until renewal
        renewal_date = None
        days_until_renewal = 0
        if period_start:
            renewal_date = datetime.fromtimestamp(period_start)
            days_until_renewal = (renewal_date - datetime.now()).days

        # Create notification in database
        notification = Notification(
            user_id=user.id,
            subscription_id=db_subscription.id,
            type="renewal_reminder",
            title=f"Your {db_subscription.plan.title()} subscription will renew soon",
            message=f"Your {db_subscription.plan.title()} subscription will renew in {days_until_renewal} days for ${invoice_amount} {currency}. Please ensure your payment method is up to date.",
            amount=invoice_amount,
            currency=currency.lower(),
            renewal_date=renewal_date,
        )

        db.add(notification)
        db.commit()

        logger.info(f"Subscription renewal reminder created for user {user.email}:")
        logger.info(f"  - Subscription: {subscription_id}")
        logger.info(f"  - Plan: {db_subscription.plan}")
        logger.info(f"  - Amount: ${invoice_amount} {currency}")
        logger.info(f"  - Days until renewal: {days_until_renewal}")

        # Structured log for monitoring systems
        logger.info(
            "SUBSCRIPTION_RENEWAL_REMINDER",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "subscription_id": subscription_id,
                "plan": db_subscription.plan,
                "amount": invoice_amount,
                "currency": currency,
                "days_until_renewal": days_until_renewal,
                "renewal_date": renewal_date.isoformat() if renewal_date else None,
                "notification_id": notification.id,
            },
        )

    except Exception as e:
        logger.error(f"Error handling upcoming invoice: {e}")


async def handle_subscription_updated(subscription, db: Session):
    """Handle subscription update"""
    try:
        subscription_id = subscription["id"]

        # Update subscription in database
        db_subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == subscription_id)
            .first()
        )

        if db_subscription:
            db_subscription.status = subscription["status"]
            db_subscription.current_period_start = datetime.fromtimestamp(
                subscription["current_period_start"]
            )
            db_subscription.current_period_end = datetime.fromtimestamp(
                subscription["current_period_end"]
            )
            db_subscription.updated_at = datetime.now()
            db.commit()
            logger.info(f"Subscription updated: {subscription_id}")

    except Exception as e:
        logger.error(f"Error handling subscription updated: {e}")


async def handle_subscription_deleted(subscription, db: Session):
    """Handle subscription cancellation"""
    try:
        subscription_id = subscription["id"]

        # Update status in database
        db_subscription = (
            db.query(Subscription)
            .filter(Subscription.stripe_subscription_id == subscription_id)
            .first()
        )

        if db_subscription:
            db_subscription.status = "canceled"
            db_subscription.updated_at = datetime.now()
            db.commit()
            logger.info(f"Subscription canceled: {subscription_id}")

    except Exception as e:
        logger.error(f"Error handling subscription deleted: {e}")
