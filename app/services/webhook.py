import hmac
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.subscription import Subscription


async def verify_webhook_signature(signature: str, payload: str, secret: str) -> bool:
    computed_signature = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, computed_signature)


async def update_user_subscription(db: Session, user_id: str, customer_id: str, subscription_id: str, plan: str, status: str, renews_at: str):
    now = datetime.utcnow()
    monthly_character_limit = 100000

    subscription = db.query(Subscription).filter(
        Subscription.user_id == user_id).first()

    if subscription:
        subscription.subscription_id = subscription_id
        subscription.plan = plan
        subscription.subscription_status = status
        subscription.monthly_character_limit = monthly_character_limit
        subscription.renews_at = renews_at
        subscription.updated_at = now
    else:
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

    db.commit()
