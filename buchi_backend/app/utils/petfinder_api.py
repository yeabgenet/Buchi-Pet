import httpx
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

PETFINDER_BASE = "https://api.petfinder.com/v2"

# Token cache
_token_cache: dict = {"access_token": None, "expires_in": 0}


async def _get_access_token() -> str:
    """Fetch a new OAuth2 token from Petfinder if needed."""
    import time

    if _token_cache["access_token"] and _token_cache["expires_in"] > time.time():
        return _token_cache["access_token"]

    # Petfinder uses client_credentials flow
    # The key is both client_id and client_secret (for secret key APIs)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{PETFINDER_BASE}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.petfinder_api_key,
                "client_secret": settings.petfinder_api_key,
            },
        )
        if resp.status_code != 200:
            logger.warning(f"Petfinder token fetch failed: {resp.text}")
            return ""

        data = resp.json()
        _token_cache["access_token"] = data.get("access_token", "")
        _token_cache["expires_in"] = time.time() + data.get("expires_in", 3600) - 60
        return _token_cache["access_token"]


def _map_petfinder_animal(animal: dict) -> dict:
    """Convert a Petfinder animal object to our PetOut schema."""
    photos = []
    for photo in animal.get("photos", []):
        url = photo.get("medium") or photo.get("small") or photo.get("full")
        if url:
            photos.append(url)

    age_map = {
        "Baby": "baby",
        "Young": "young",
        "Adult": "adult",
        "Senior": "senior",
    }
    size_map = {
        "Small": "small",
        "Medium": "medium",
        "Large": "large",
        "Extra Large": "large",
    }
    gender_map = {
        "Male": "male",
        "Female": "female",
        "Unknown": None,
    }

    return {
        "pet_id": str(animal.get("id", "")),
        "source": "petfinder",
        "type": animal.get("type", "Unknown"),
        "gender": gender_map.get(animal.get("gender", ""), None),
        "size": size_map.get(animal.get("size", ""), None),
        "age": age_map.get(animal.get("age", ""), None),
        "good_with_children": animal.get("environment", {}).get("children"),
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
    """Search Petfinder API and return normalized pet list."""
    token = await _get_access_token()
    if not token:
        return []

    # Petfinder uses capitalized values
    gender_map = {"male": "Male", "female": "Female"}
    size_map = {"small": "Small", "medium": "Medium", "large": "Large"}
    age_map = {"baby": "Baby", "young": "Young", "adult": "Adult", "senior": "Senior"}

    params: dict = {"limit": min(limit, 100)}
    if type:
        params["type"] = type
    if gender:
        params["gender"] = gender_map.get(gender.lower(), gender)
    if size:
        params["size"] = size_map.get(size.lower(), size)
    if age:
        params["age"] = age_map.get(age.lower(), age)
    if good_with_children is not None:
        params["good_with_children"] = str(good_with_children).lower()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{PETFINDER_BASE}/animals",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            if resp.status_code != 200:
                logger.warning(f"Petfinder search failed [{resp.status_code}]: {resp.text[:200]}")
                return []

            animals = resp.json().get("animals", [])
            return [_map_petfinder_animal(a) for a in animals]
    except Exception as e:
        logger.error(f"Petfinder request error: {e}")
        return []
