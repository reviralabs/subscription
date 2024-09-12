from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.subscription import Subscription
from app.services.lemon_squeezy import (
    create_checkout_session,
    update_lemon_squeezy_subscription,
    cancel_lemon_squeezy_subscription
)
from datetime import datetime


async def get_existing_subscription(db: Session, user_id: str):
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()


async def create_subscription(user_id: str, plan_id: str):
    db = next(get_db())
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


async def get_subscription(user_id: str):
    db = next(get_db())
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


async def update_subscription(user_id: str, variant_id: str):
    db = next(get_db())
    subscription = await get_existing_subscription(db, user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    result = await update_lemon_squeezy_subscription(subscription.subscription_id, variant_id)

    # subscription.plan = result["data"]["attributes"]["product_name"]
    # subscription.subscription_status = result["data"]["attributes"]["status"]
    # subscription.monthly_character_limit = 1000000
    # subscription.renews_at = result["data"]["attributes"]["renews_at"]
    # subscription.updated_at = datetime.now()
    # db.commit()

    return result["data"]


async def cancel_subscription(user_id: str):
    db = next(get_db())
    subscription = await get_existing_subscription(db, user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await cancel_lemon_squeezy_subscription(subscription.subscription_id)

    subscription.subscription_status = "canceled"
    subscription.updated_at = datetime.now()
    db.commit()

    return {"success": True}


async def resume_subscription(user_id: str, plan_id: str):
    db = next(get_db())
    subscription = await get_existing_subscription(db, user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    result = await update_lemon_squeezy_subscription(subscription.subscription_id, plan_id)

    subscription.plan = result["data"]["attributes"]["product_name"]
    subscription.subscription_status = result["data"]["attributes"]["status"]
    subscription.monthly_character_limit = 1000000
    subscription.renews_at = result["data"]["attributes"]["renews_at"]
    subscription.updated_at = datetime.now()
    db.commit()

    return result["data"]
