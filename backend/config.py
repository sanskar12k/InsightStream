from pydantic_settings import BaseSettings
from typing import List 


class Settings(BaseSettings):
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:3001"]

setting = Settings()