"""
ShotSaaS - Sports Betting Analysis Platform
Main FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, async_session_factory
from app.core.redis import init_redis, close_redis
from app.models.base import Base
from app.api import players, matches, value_bets, admin
from app.tasks.scheduler import start_scheduler, stop_scheduler
from app.seed import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME}...")

    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")

    # Check if we have real API key
    has_real_api = bool(settings.API_FOOTBALL_KEY and len(settings.API_FOOTBALL_KEY) > 10)

    async with async_session_factory() as session:
        from sqlalchemy import select
        from app.models.league import League
        result = await session.execute(select(League).limit(1))
        db_has_data = result.scalar_one_or_none() is not None

        if not db_has_data:
            if has_real_api:
                logger.info("API-Football key found. Will fetch real data on first refresh.")
                from app.services.data_fetcher import DataFetcher
                fetcher = DataFetcher()
                fixtures = await fetcher.get_today_fixtures()
                if fixtures:
                    logger.info(f"Found {len(fixtures)} real fixtures. Running full refresh...")
                    from app.tasks.refresh import (
                        refresh_today_matches, refresh_player_stats,
                        refresh_odds, calculate_all_probabilities, detect_value_bets,
                    )
                    await refresh_today_matches()
                    await refresh_player_stats()
                    await refresh_odds()
                    await calculate_all_probabilities()
                    await detect_value_bets()
                    logger.info("Real data refresh complete.")
                else:
                    logger.info("No real fixtures found. Running seed...")
                    await seed_database()
            else:
                logger.info("No API key. Running seed with mock data...")
                await seed_database()
            logger.info("Database initialized.")
        else:
            logger.info("Database already contains data. Skipping initialization.")

    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized.")

    # Start background scheduler (fetches real data every 15 min)
    await start_scheduler()
    logger.info("Background scheduler started.")

    yield

    # Shutdown
    await stop_scheduler()
    await close_redis()
    await engine.dispose()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Sports Betting Analysis Platform - Focused on player shooting statistics",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(value_bets.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# WebSocket endpoint for real-time updates
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.active_connections -= dead


manager = ConnectionManager()


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
