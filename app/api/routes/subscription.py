from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.schemas.subscription import SubscriptionRequest, SubscriptionResponse
from app.services.subscription import (
    create_subscription,
    get_subscription,
    update_subscription,
    cancel_subscription
)

router = APIRouter()


@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription_route(
    request: SubscriptionRequest,
    current_user: str = Depends(get_current_user)
):
    return await create_subscription(current_user, request.planId)


@router.get("/subscriptions", response_model=dict)
async def get_subscription_route(current_user: str = Depends(get_current_user)):
    return await get_subscription(current_user)


@router.post("/subscriptions/update")
async def update_subscription_route(
    variant_id: str,
    current_user: str = Depends(get_current_user)
):
    return await update_subscription(current_user, variant_id)


@router.post("/subscriptions/cancel")
async def cancel_subscription_route(current_user: str = Depends(get_current_user)):
    return await cancel_subscription(current_user)
