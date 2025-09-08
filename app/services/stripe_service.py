import stripe
from typing import Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key
logger.info(f"Stripe configured with API key: {settings.stripe_secret_key[:20]}...")


class StripeService:
    def __init__(self):
        self.api_key = settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret
        stripe.api_key = self.api_key
        logger.info("StripeService initialized successfully")

    async def create_customer(self, email: str, name: str) -> str:
        """Create customer in Stripe"""
        try:
            logger.info(f"Creating Stripe customer for: {email}")

            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise Exception(f"Error creating customer: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating customer: {e}")
            raise Exception(f"Error creating customer: {str(e)}")

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """Create checkout session for subscription"""
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url or f"{settings.frontend_url}/success",
                cancel_url=cancel_url or f"{settings.frontend_url}/cancel"
            )

            logger.info(f"Created checkout session: {session.id}")
            return {
                "session_id": session.id,
                "url": session.url
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {e}")
            raise Exception(f"Error creating checkout session: {str(e)}")

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details from Stripe"""
        try:
            logger.info(f"Retrieving subscription: {subscription_id}")
            subscription = stripe.Subscription.retrieve(subscription_id)

            logger.info(f"Subscription retrieved: {subscription.id}")

            # Convert to dict for easy data access
            subscription_dict = subscription.to_dict_recursive()

            # Get items and periods from first item
            items_data = subscription_dict.get('items', {}).get('data', [])
            current_period_start = None
            current_period_end = None

            if items_data:
                first_item = items_data[0]
                current_period_start = first_item.get('current_period_start')
                current_period_end = first_item.get('current_period_end')

            result = {
                "id": subscription.id,
                "customer": subscription.customer,
                "status": subscription.status,
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "items": {
                    "data": items_data
                }
            }

            logger.info(f"Subscription data prepared successfully")
            return result

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {e}")
            raise Exception(f"Error retrieving subscription: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving subscription: {e}")
            raise Exception(f"Unexpected error retrieving subscription: {str(e)}")

    def construct_webhook_event(self, payload: bytes, sig_header: str):
        """Construct and validate Stripe webhook event"""
        try:
            logger.info("Processing webhook event...")

            if not self.webhook_secret or self.webhook_secret == "whsec_placeholder":
                raise ValueError("Webhook secret is not configured correctly")

            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            logger.info(f"Webhook event received: {event['type']}")
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise ValueError("Invalid signature")
        except Exception as e:
            logger.error(f"Unexpected webhook error: {e}")
            raise ValueError(f"Webhook error: {str(e)}")

    async def get_price_info(self, price_id: str) -> Dict[str, Any]:
        """Get price details from Stripe"""
        try:
            price = stripe.Price.retrieve(price_id)
            return {
                "id": price.id,
                "amount": price.unit_amount / 100,  # Convert from cents
                "currency": price.currency,
                "interval": price.recurring.interval if price.recurring else "one_time"
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving price: {e}")
            return None

    def extract_subscription_id_from_invoice(self, invoice: Dict[str, Any]) -> Optional[str]:
        """Extract subscription ID from invoice object with robust error handling

        Handles different invoice structures that may contain subscription_id in:
        - Direct invoice.subscription field
        - invoice.parent.subscription_details.subscription field
        - invoice.lines.data[].subscription field
        """
        # Method 1: Direct access (previous versions)
        subscription_id = invoice.get('subscription')
        if subscription_id:
            logger.info(f"Found subscription_id directly: {subscription_id}")
            return subscription_id

        # Method 2: From parent.subscription_details (new structure)
        parent = invoice.get('parent', {})
        if parent and parent.get('type') == 'subscription_details':
            subscription_details = parent.get('subscription_details', {})
            subscription_id = subscription_details.get('subscription')
            if subscription_id:
                logger.info(f"Found subscription_id in parent: {subscription_id}")
                return subscription_id

        # Method 3: From lines (alternative)
        lines = invoice.get('lines', {}).get('data', [])
        for line in lines:
            parent_line = line.get('parent', {})
            if parent_line.get('type') == 'subscription_item_details':
                subscription_details = parent_line.get('subscription_item_details', {})
                subscription_id = subscription_details.get('subscription')
                if subscription_id:
                    logger.info(f"Found subscription_id in line: {subscription_id}")
                    return subscription_id

        logger.warning("No subscription_id found in invoice")
        return None


# Global service instance
stripe_service = StripeService()
