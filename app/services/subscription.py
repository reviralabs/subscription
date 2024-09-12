from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import get_db
from app.models.subscription import Subscription
from app.services.lemon_squeezy import (
    create_checkout_session,
    update_lemon_squeezy_subscription,
    cancel_lemon_squeezy_subscription
)
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_existing_subscription(db: Session, user_id: str) -> Optional[Subscription]:
    """
    Retrieve the existing subscription for a given user.

    Args:
        db (Session): The database session.
        user_id (str): The ID of the user.

    Returns:
        Optional[Subscription]: The user's subscription if it exists, None otherwise.
    """
    try:
        return db.query(Subscription).filter(Subscription.user_id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(
            f"Database error while fetching subscription for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def create_subscription(user_id: str, plan_id: str) -> Dict[str, Any]:
    """
    Create or update a subscription for a user.

    Args:
        user_id (str): The ID of the user.
        plan_id (str): The ID of the subscription plan.

    Returns:
        Dict[str, Any]: A dictionary containing subscription details and redirect URL.
    """
    db = next(get_db())
    try:
        subscription = await get_existing_subscription(db, user_id)

        if subscription:
            if subscription.subscription_status == "active":
                result = await update_subscription(user_id, plan_id)
                return {
                    "success": True,
                    "subscription": result,
                    "redirectUrl": "http://localhost:5173/app/subscription"
                }
            elif subscription.subscription_status == "cancelled" and subscription.plan == plan_id:
                result = await resume_subscription(user_id, plan_id)
                return {
                    "success": True,
                    "subscription": result,
                    "redirectUrl": "http://localhost:5173/app/subscription"
                }

        checkout_session = await create_checkout_session(user_id, plan_id)
        return {"success": True, "redirectUrl": checkout_session["data"]["attributes"]["url"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error creating subscription for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create subscription")


async def get_subscription(user_id: str) -> Dict[str, Any]:
    """
    Get the subscription details for a user.

    Args:
        user_id (str): The ID of the user.

    Returns:
        Dict[str, Any]: A dictionary containing subscription details.
    """
    db = next(get_db())
    try:
        subscription = await get_existing_subscription(db, user_id)

        if subscription and subscription.subscription_status == "active":
            return {
                "plan": subscription.plan,
                "status": subscription.subscription_status,
                "renewsAt": subscription.renews_at,
                "createdAt": subscription.created_at,
                "updatedAt": subscription.updated_at,
                "monthlyCharacterLimit": subscription.monthly_character_limit,
                "availableUpgrades": [{"plan": "Pro", "description": "For expert users"}] if subscription.plan == "Starter" else []
            }
        else:
            return {
                "plan": "free",
                "status": "free",
                "monthlyCharacterLimit": 10000,
                "renewsAt": datetime.now(),
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "availableUpgrades": [
                    {"plan": "Starter", "description": "Good for beginners"},
                    {"plan": "Pro", "description": "For expert users"}
                ]
            }
    except Exception as e:
        logger.error(
            f"Error fetching subscription for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch subscription details")


async def update_subscription(user_id: str, variant_id: str) -> Dict[str, Any]:
    """
    Update an existing subscription.

    Args:
        user_id (str): The ID of the user.
        variant_id (str): The ID of the new subscription variant.

    Returns:
        Dict[str, Any]: A dictionary containing updated subscription details.
    """
    db = next(get_db())
    try:
        subscription = await get_existing_subscription(db, user_id)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        result = await update_lemon_squeezy_subscription(subscription.subscription_id, variant_id)

        # TODO: Uncomment and adjust these lines once the update logic is finalized
        # subscription.plan = result["data"]["attributes"]["product_name"]
        # subscription.subscription_status = result["data"]["attributes"]["status"]
        # subscription.monthly_character_limit = 1000000
        # subscription.renews_at = result["data"]["attributes"]["renews_at"]
        # subscription.updated_at = datetime.now()
        # db.commit()

        return result["data"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating subscription for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to update subscription")


async def cancel_subscription(user_id: str) -> Dict[str, bool]:
    """
    Cancel an existing subscription.

    Args:
        user_id (str): The ID of the user.

    Returns:
        Dict[str, bool]: A dictionary indicating the success of the operation.
    """
    db = next(get_db())
    try:
        subscription = await get_existing_subscription(db, user_id)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        await cancel_lemon_squeezy_subscription(subscription.subscription_id)

        subscription.subscription_status = "canceled"
        subscription.updated_at = datetime.now()
        db.commit()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error canceling subscription for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to cancel subscription")


async def resume_subscription(user_id: str, plan_id: str) -> Dict[str, Any]:
    """
    Resume a cancelled subscription.

    Args:
        user_id (str): The ID of the user.
        plan_id (str): The ID of the subscription plan to resume.

    Returns:
        Dict[str, Any]: A dictionary containing resumed subscription details.
    """
    db = next(get_db())
    try:
        subscription = await get_existing_subscription(db, user_id)
        if not subscription:
            raise HTTPException(
                status_code=404, detail="Subscription not found")

        result = await update_lemon_squeezy_subscription(subscription.subscription_id, plan_id)

        subscription.plan = result["data"]["attributes"]["product_name"]
        subscription.subscription_status = result["data"]["attributes"]["status"]
        subscription.monthly_character_limit = 1000000
        subscription.renews_at = result["data"]["attributes"]["renews_at"]
        subscription.updated_at = datetime.now()
        db.commit()

        return result["data"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error resuming subscription for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to resume subscription")
