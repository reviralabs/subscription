from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionRequest(BaseModel):
    planId: str


class SubscriptionResponse(BaseModel):
    success: bool
    subscription: Optional[dict] = None
    redirectUrl: Optional[str] = None


class SubscriptionDetails(BaseModel):
    plan: str
    status: str
    renewsAt: Optional[datetime]
    createdAt: datetime
    updatedAt: datetime
    monthlyCharacterLimit: int
    availableUpgrades: list
