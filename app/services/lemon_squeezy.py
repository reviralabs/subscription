import httpx
from typing import Dict, Any
from app.core.config import settings
import logging
from fastapi import HTTPException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of plan names to their corresponding variant IDs
PRODUCT_VARIANT_ID_MAP = {
    "Starter": "472351",
    "Pro": "472366",
}

# Base URL for Lemon Squeezy API
LEMON_SQUEEZY_BASE_URL = "https://api.lemonsqueezy.com/v1"

# Common headers for Lemon Squeezy API requests


def get_lemon_squeezy_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.LEMON_SQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }


async def make_lemon_squeezy_request(method: str, endpoint: str, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Make a request to the Lemon Squeezy API.

    Args:
        method (str): HTTP method (e.g., 'GET', 'POST', 'PATCH', 'DELETE').
        endpoint (str): API endpoint.
        json_data (Dict[str, Any], optional): JSON data to send with the request.

    Returns:
        Dict[str, Any]: JSON response from the API.

    Raises:
        HTTPException: If the API request fails.
    """
    url = f"{LEMON_SQUEEZY_BASE_URL}/{endpoint}"
    headers = get_lemon_squeezy_headers()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Lemon Squeezy API error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code,
                            detail="Lemon Squeezy API error")
    except Exception as e:
        logger.error(
            f"Unexpected error in Lemon Squeezy API request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def create_checkout_session(user_id: str, plan_id: str) -> Dict[str, Any]:
    """
    Create a checkout session for a user.

    Args:
        user_id (str): The ID of the user.
        plan_id (str): The ID of the plan (e.g., 'Starter', 'Pro').

    Returns:
        Dict[str, Any]: The checkout session data.

    Raises:
        HTTPException: If the plan_id is invalid or if the API request fails.
    """
    if plan_id not in PRODUCT_VARIANT_ID_MAP:
        raise HTTPException(status_code=400, detail="Invalid plan ID")

    variant_id = PRODUCT_VARIANT_ID_MAP[plan_id]

    json_data = {
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

    return await make_lemon_squeezy_request('POST', 'checkouts', json_data)


async def update_lemon_squeezy_subscription(subscription_id: str, variant_id: str) -> Dict[str, Any]:
    """
    Update a Lemon Squeezy subscription.

    Args:
        subscription_id (str): The ID of the subscription to update.
        variant_id (str): The ID of the new variant.

    Returns:
        Dict[str, Any]: The updated subscription data.

    Raises:
        HTTPException: If the API request fails.
    """
    json_data = {
        "data": {
            "type": "subscriptions",
            "id": subscription_id,
            "attributes": {
                "variant_id": variant_id
            }
        }
    }

    return await make_lemon_squeezy_request('PATCH', f'subscriptions/{subscription_id}', json_data)


async def cancel_lemon_squeezy_subscription(subscription_id: str) -> Dict[str, Any]:
    """
    Cancel a Lemon Squeezy subscription.

    Args:
        subscription_id (str): The ID of the subscription to cancel.

    Returns:
        Dict[str, Any]: The response data from the cancellation request.

    Raises:
        HTTPException: If the API request fails.
    """
    return await make_lemon_squeezy_request('DELETE', f'subscriptions/{subscription_id}')
