from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.webhook import verify_webhook_signature, update_user_subscription
from app.db.database import get_db
import json
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_EVENTS = ["subscription_created", "subscription_updated"]


async def process_webhook_body(request: Request) -> Dict[str, Any]:
    """
    Process the webhook request body.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        Dict[str, Any]: The parsed JSON body of the webhook.

    Raises:
        HTTPException: If the body cannot be decoded or parsed.
    """
    try:
        body = await request.body()
        body_str = body.decode()
        return json.loads(body_str)
    except UnicodeDecodeError:
        logger.error("Failed to decode webhook body")
        raise HTTPException(status_code=400, detail="Invalid body encoding")
    except json.JSONDecodeError:
        logger.error("Failed to parse webhook body as JSON")
        raise HTTPException(
            status_code=400, detail="Invalid JSON in webhook body")


async def extract_subscription_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant subscription data from the webhook event.

    Args:
        event (Dict[str, Any]): The webhook event data.

    Returns:
        Dict[str, Any]: Extracted subscription data.

    Raises:
        HTTPException: If required data is missing from the event.
    """
    try:
        return {
            "user_id": event["meta"]["custom_data"]["user_id"],
            "subscription_id": str(event["data"]["id"]),
            "customer_id": str(event["data"]["attributes"]["customer_id"]),
            "plan": event["data"]["attributes"]["variant_name"],
            "status": event["data"]["attributes"]["status"],
            "renews_at": event["data"]["attributes"]["renews_at"]
        }
    except KeyError as e:
        logger.error(f"Missing required field in webhook data: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Missing required field: {str(e)}")


@router.post("/webhook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming webhooks from Lemon Squeezy.

    This endpoint verifies the webhook signature, processes supported events,
    and updates user subscriptions accordingly.

    Args:
        request (Request): The FastAPI request object.
        db (Session): The database session.

    Returns:
        Dict[str, str]: A message indicating the webhook was processed.

    Raises:
        HTTPException: If the signature is invalid or if there's an error processing the webhook.
    """
    signature = request.headers.get("X-Signature")
    if not signature:
        raise HTTPException(
            status_code=400, detail="Missing X-Signature header")

    try:
        event = await process_webhook_body(request)

        if not await verify_webhook_signature(signature, json.dumps(event), settings.LEMON_SQUEEZY_WEBHOOK_SECRET):
            raise HTTPException(status_code=400, detail="Invalid signature")

        event_name = event["meta"]["event_name"]
        if event_name not in SUPPORTED_EVENTS:
            logger.info(f"Ignoring unsupported event: {event_name}")
            return {"message": "Webhook ignored (unsupported event)"}

        subscription_data = await extract_subscription_data(event)

        await update_user_subscription(
            db,
            subscription_data["user_id"],
            subscription_data["customer_id"],
            subscription_data["subscription_id"],
            subscription_data["plan"],
            subscription_data["status"],
            subscription_data["renews_at"]
        )

        logger.info(
            f"Successfully processed {event_name} event for user {subscription_data['user_id']}")
        return {"message": "Webhook processed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
