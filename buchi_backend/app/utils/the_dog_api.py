import httpx
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

THE_DOG_API_BASE = "https://api.thedogapi.com/v1"


def _map_the_dog_api_dog(dog: dict) -> dict:
    """Convert a TheDogAPI dog object to our PetOut schema."""
    photos = []
    if dog.get("url"):
        photos.append(dog["url"])
    if dog.get("image"):
        photos.append(dog["image"]["url"])

    # TheDogAPI temperament mapping for good_with_children
    good_with_children = False
    temperament = dog.get("temperament", "").lower()
    if any(word in temperament for word in ["good", "friendly", "children", "family"]):
        good_with_children = True

    return {
        "pet_id": str(dog.get("id", "")),
        "source": "thedogapi",
        "type": "Dog",
        "gender": None,  # TheDogAPI doesn't provide gender
        "size": None,  # TheDogAPI doesn't provide size directly
        "age": None,  # TheDogAPI doesn't provide age directly
        "good_with_children": good_with_children,
        "Photos": photos,
    }


async def search_the_dog_api(
    type: Optional[str] = None,
    gender: Optional[str] = None,
    size: Optional[str] = None,
    age: Optional[str] = None,
    good_with_children: Optional[bool] = None,
    limit: int = 10,
) -> list[dict]:
    """Search TheDogAPI and return normalized pet list."""
    if not settings.the_dog_api_key:
        logger.warning("THE_DOG_API_KEY not configured")
        return []

    # TheDogAPI uses query parameters for filtering
    params: dict = {"limit": min(limit, 100)}
    
    # Map our filters to TheDogAPI parameters
    # TheDogAPI doesn't support all our filters, but we can use breed groups
    if type and type.lower() == "cat":
        # TheDogAPI is dog-specific, return empty for cats
        return []

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

            dogs = resp.json()
            return [_map_the_dog_api_dog(d) for d in dogs]
    except Exception as e:
        logger.error(f"TheDogAPI request error: {e}")
        return []
