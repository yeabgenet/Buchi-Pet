from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://buchi:buchi123@localhost:5432/buchi")
    the_dog_api_key: str = os.getenv("THE_DOG_API_KEY", "")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
