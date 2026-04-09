import httpx
import logging
from typing import Optional, List, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

THE_DOG_API_BASE = "https://api.thedogapi.com/v1"


def _map_thedogapi_item(item: dict) -> dict:
    """Convert a TheDogAPI image object to our PetOut schema."""
    photos = []
    if item.get("url"):
        photos.append(item["url"])
    if item.get("image") and item["image"].get("url"):
        photos.append(item["image"]["url"])

    temperament = ""
    breeds = item.get("breeds") or []
    if breeds and isinstance(breeds, list):
        temperament = breeds[0].get("temperament", "") or ""

    good_with_children = None
    if temperament:
        temp_lower = temperament.lower()
        good_with_children = any(word in temp_lower for word in ["good", "friendly", "children", "family"])

    return {
        "pet_id": str(item.get("id", "")),
        "source": "thedogapi",
        "type": "Dog",
        "gender": None,
        "size": None,
        "age": None,
        "good_with_children": good_with_children,
        "Photos": photos,
    }


async def search_petfinder(
    type: Optional[str] = None,
    gender: Optional[str] = None,
    size: Optional[str] = None,
    age: Optional[str] = None,
    good_with_children: Optional[bool] = None,
    limit: int = 10,
) -> list[dict]:
    """Search TheDogAPI using THE_DOG_API_KEY and return normalized pet list."""
    if not settings.the_dog_api_key:
        logger.warning("THE_DOG_API_KEY not configured")
        return []

    if type and type.lower() == "cat":
        return []

    params: dict = {"limit": min(limit, 100)}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{THE_DOG_API_BASE}/images/search",
                headers={"x-api-key": settings.the_dog_api_key},
                params=params,
            )
            if resp.status_code != 200:
                logger.warning(f"TheDogAPI search failed [{resp.status_code}]: {resp.text[:200]}")
                return []

            items = resp.json()
            pets = [_map_thedogapi_item(item) for item in items]
            if good_with_children is True:
                pets = [pet for pet in pets if pet["good_with_children"]]
            return pets[:limit]
    except Exception as e:
        logger.error(f"TheDogAPI request error: {e}")
        return []


async def upload_image(file_data: bytes, filename: str, sub_id: Optional[str] = None) -> dict:
    """Upload an image to TheDogAPI and return the response."""
    if not settings.the_dog_api_key:
        logger.warning("THE_DOG_API_KEY not configured")
        return {}

    files = {"file": (filename, file_data, "image/jpeg")}
    data = {}
    if sub_id:
        data["sub_id"] = sub_id

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{THE_DOG_API_BASE}/images/upload",
                headers={"x-api-key": settings.the_dog_api_key},
                files=files,
                data=data,
            )
            if resp.status_code not in {200, 201, 202}:
                logger.warning(f"TheDogAPI upload failed [{resp.status_code}]: {resp.text[:200]}")
                return {}

            return resp.json()
    except Exception as e:
        logger.error(f"TheDogAPI upload error: {e}")
        return {}


async def list_uploaded_images(sub_id: Optional[str] = None, limit: int = 10) -> list[dict]:
    """List uploaded images from TheDogAPI."""
    if not settings.the_dog_api_key:
        logger.warning("THE_DOG_API_KEY not configured")
        return []

    params = {"limit": min(limit, 100)}
    if sub_id:
        params["sub_id"] = sub_id

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{THE_DOG_API_BASE}/images",
                headers={"x-api-key": settings.the_dog_api_key},
                params=params,
            )
            if resp.status_code != 200:
                logger.warning(f"TheDogAPI list failed [{resp.status_code}]: {resp.text[:200]}")
                return []

            return resp.json()
    except Exception as e:
        logger.error(f"TheDogAPI list error: {e}")
        return []


async def get_image_details(image_id: str) -> dict:
    """Get details of a specific image by ID."""
    if not settings.the_dog_api_key:
        logger.warning("THE_DOG_API_KEY not configured")
        return {}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{THE_DOG_API_BASE}/images/{image_id}",
                headers={"x-api-key": settings.the_dog_api_key},
            )
            if resp.status_code != 200:
                logger.warning(f"TheDogAPI get details failed [{resp.status_code}]: {resp.text[:200]}")
                return {}

            return resp.json()
    except Exception as e:
        logger.error(f"TheDogAPI get details error: {e}")
        return {}


async def delete_image(image_id: str) -> bool:
    """Delete an uploaded image by ID."""
    if not settings.the_dog_api_key:
        logger.warning("THE_DOG_API_KEY not configured")
        return False

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(
                f"{THE_DOG_API_BASE}/images/{image_id}",
                headers={"x-api-key": settings.the_dog_api_key},
            )
            return resp.status_code == 204
    except Exception as e:
        logger.error(f"TheDogAPI delete error: {e}")
        return False
