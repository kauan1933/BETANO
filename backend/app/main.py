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

    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized.")

    # Start background scheduler
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
