from fastapi import APIRouter, Request, HTTPException, Depends
from app.core.config import settings
from app.services.webhook import verify_webhook_signature, update_user_subscription
from app.db.database import get_db
from sqlalchemy.orm import Session
import json

router = APIRouter()


@router.post("/webhook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    signature = request.headers.get("X-Signature")
    body = await request.body()
    body_str = body.decode()

    if not await verify_webhook_signature(signature, body_str, settings.LEMON_SQUEEZY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid signature")

    event = json.loads(body_str)
    event_name = event["meta"]["event_name"]

    if event_name in ["subscription_created", "subscription_updated"]:
        user_id = event["meta"]["custom_data"]["user_id"]
        subscription_id = str(event["data"]["id"])
        subscription_data = event["data"]["attributes"]
        plan = subscription_data["variant_name"]
        status = subscription_data["status"]
        renews_at = subscription_data["renews_at"]
        customer_id = str(subscription_data["customer_id"])

        await update_user_subscription(db, user_id, customer_id, subscription_id, plan, status, renews_at)

    return {"message": "Webhook processed"}
