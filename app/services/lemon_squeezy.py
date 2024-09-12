import httpx
from app.core.config import settings

PRODUCT_VARIANT_ID_MAP = {
    "Starter": "472351",
    "Pro": "472366",
}


async def create_checkout_session(user_id: str, plan_id: str):
    variant_id = PRODUCT_VARIANT_ID_MAP[plan_id]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.lemonsqueezy.com/v1/checkouts",
            headers={
                "Authorization": f"Bearer {settings.LEMON_SQUEEZY_API_KEY}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json"
            },
            json={
                "data": {
                    "type": "checkouts",
                    "attributes": {
                        "custom_price": None,
                        "product_options": {
                            "enabled_variants": [variant_id],
                            "redirect_url": "http://localhost:5173/app/subscription"
                        },
                        "checkout_options": {
                            "button_color": "#2DD272"
                        },
                        "checkout_data": {
                            "custom": {
                                "user_id": user_id
                            }
                        },
                        "expires_at": None,
                        "preview": False
                    },
                    "relationships": {
                        "store": {
                            "data": {
                                "type": "stores",
                                "id": settings.STORE_ID
                            }
                        },
                        "variant": {
                            "data": {
                                "type": "variants",
                                "id": variant_id
                            }
                        }
                    }
                }
            }
        )
    response.raise_for_status()
    return response.json()


async def update_lemon_squeezy_subscription(subscription_id: str, variant_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"https://api.lemonsqueezy.com/v1/subscriptions/{subscription_id}",
            headers={
                "Authorization": f"Bearer {settings.LEMON_SQUEEZY_API_KEY}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json"
            },
            json={
                "data": {
                    "type": "subscriptions",
                    "id": subscription_id,
                    "attributes": {
                        "variant_id": variant_id
                    }
                }
            }
        )
    response.raise_for_status()
    return response.json()


async def cancel_lemon_squeezy_subscription(subscription_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"https://api.lemonsqueezy.com/v1/subscriptions/{subscription_id}",
            headers={
                "Authorization": f"Bearer {settings.LEMON_SQUEEZY_API_KEY}",
                "Accept": "application/vnd.api+json"
            }
        )
    response.raise_for_status()
    return response.json()
