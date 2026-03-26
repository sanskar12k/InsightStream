from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Get production frontend URL from environment (update when frontend is deployed)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Build CORS allowed origins list
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:3001",
            "https://insightstream-ivory.vercel.app"
        ]

        # Add Railway backend URL (for testing from Railway docs UI)
        railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if railway_url:
            origins.append(f"https://{railway_url}")

        # Add production frontend URL if different from localhost
        if self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)

        return origins


setting = Settings()
