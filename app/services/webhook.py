import hmac
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.subscription import Subscription
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define subscription plans and their character limits
SUBSCRIPTION_PLANS = {
    "Free": 10000,
    "Starter": 100000,
    "Pro": 1000000,
    # Add more plans as needed
}


async def verify_webhook_signature(signature: str, payload: str, secret: str) -> bool:
    """
    Verify the webhook signature using HMAC-SHA256.

    Args:
        signature (str): The provided signature from the webhook header.
        payload (str): The raw payload of the webhook.
        secret (str): The webhook secret used for signature verification.

    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    try:
        computed_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, computed_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


async def update_user_subscription(
    db: Session,
    user_id: str,
    customer_id: str,
    subscription_id: str,
    plan: str,
    status: str,
    renews_at: str
) -> Optional[Subscription]:
    """
    Update or create a user's subscription based on webhook data.

    Args:
        db (Session): The database session.
        user_id (str): The ID of the user.
        customer_id (str): The Lemon Squeezy customer ID.
        subscription_id (str): The Lemon Squeezy subscription ID.
        plan (str): The subscription plan name.
        status (str): The subscription status.
        renews_at (str): The renewal date of the subscription.

    Returns:
        Optional[Subscription]: The updated or created Subscription object, or None if an error occurred.

    Raises:
        ValueError: If an invalid plan is provided.
    """
    if plan not in SUBSCRIPTION_PLANS:
        logger.error(f"Invalid subscription plan: {plan}")
        raise ValueError(f"Invalid subscription plan: {plan}")

    now = datetime.utcnow()
    monthly_character_limit = SUBSCRIPTION_PLANS[plan]

    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id).first()

        if subscription:
            # Update existing subscription
            subscription.subscription_id = subscription_id
            subscription.plan = plan
            subscription.subscription_status = status
            subscription.monthly_character_limit = monthly_character_limit
            subscription.renews_at = renews_at
            subscription.updated_at = now
            logger.info(f"Updated subscription for user {user_id}")
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                ls_customer_id=customer_id,
                subscription_id=subscription_id,
                plan=plan,
                subscription_status=status,
                monthly_character_limit=monthly_character_limit,
                renews_at=renews_at,
                created_at=now,
                updated_at=now
            )
            db.add(subscription)
            logger.info(f"Created new subscription for user {user_id}")

        db.commit()
        return subscription

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Database error while updating subscription for user {user_id}: {str(e)}")
        return None

    except Exception as e:
        db.rollback()
        logger.error(
            f"Unexpected error while updating subscription for user {user_id}: {str(e)}")
        return None
