import os
import uuid
import aiofiles
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


async def save_upload(file: UploadFile, pet_id: int) -> tuple[str, str]:
    """
    Save an uploaded file to disk.
    Returns (file_path, public_url).
    """
    os.makedirs(settings.upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "photo.jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    filename = f"{pet_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.upload_dir, filename)

    async with aiofiles.open(file_path, "wb") as out:
        content = await file.read()
        await out.write(content)

    public_url = f"{settings.base_url}/uploads/{filename}"
    return file_path, public_url
