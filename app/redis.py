import os

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import Request

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def create_redis_client() -> aioredis.Redis:
    """
    Crea un cliente Redis async con decode_responses=True
    para recibir strings en lugar de bytes.
    La conexión es lazy — no se establece hasta el primer comando.
    """
    return aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis
