import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

from app.cassandra import create_cassandra_session
from app.redis import create_redis_client

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mathews_coffee_delivery")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── MongoDB ───────────────────────────────────────────────────────────────
    app.state.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.state.db = app.state.mongodb_client[DB_NAME]

    # ── Redis (lazy — conecta en el primer comando) ───────────────────────────
    app.state.redis = create_redis_client()

    # ── Cassandra (AsyncioConnection — debe correr en el event loop, no en executor) ──
    app.state.cassandra = create_cassandra_session()

    # ── Background tasks ──────────────────────────────────────────────────────
    # Imports diferidos para evitar circular imports en el momento de módulo
    from app.workers.breadcrumb_flush import start_flush_worker
    from app.routes.ws import start_pubsub_listener

    app.state.flush_task = asyncio.create_task(start_flush_worker(app))
    app.state.pubsub_task = asyncio.create_task(start_pubsub_listener(app))

    logger.info("All connections established — app ready")

    yield

    # ── Cleanup ───────────────────────────────────────────────────────────────
    app.state.flush_task.cancel()
    app.state.pubsub_task.cancel()

    app.state.mongodb_client.close()
    await app.state.redis.aclose()
    app.state.cassandra.cluster.shutdown()

    logger.info("All connections closed")


async def get_db(request: Request):
    return request.app.state.db
