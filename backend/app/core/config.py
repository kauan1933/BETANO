from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "ShotSaaS"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./shotsaas.db"
    DATABASE_URL_SYNC: str = "sqlite:///./shotsaas.db"

    REDIS_URL: str = "redis://localhost:6379/0"

    API_FOOTBALL_KEY: Optional[str] = None
    FOOTBALL_DATA_KEY: Optional[str] = None

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://shotsaas.vercel.app",
        "https://betano-j6rx.vercel.app",
        "https://betano-mu.vercel.app",
        "https://betano-6y7i.vercel.app",
    ]

    # Probability model weights
    WEIGHT_LAST_5: float = 0.50
    WEIGHT_GAMES_6_10: float = 0.30
    WEIGHT_SEASON_BASELINE: float = 0.20

    # Value bet config
    EV_THRESHOLD: float = 0.05  # 5% minimum edge

    # Refresh intervals (seconds)
    MATCH_REFRESH_INTERVAL: int = 300  # 5 min
    ODDS_REFRESH_INTERVAL: int = 60   # 1 min

    class Config:
        env_file = ".env"


settings = Settings()
