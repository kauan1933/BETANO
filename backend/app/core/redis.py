import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis | None = None


async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=10,
    )
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def get_redis() -> aioredis.Redis:
    return redis_client
