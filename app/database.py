import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mathews_coffee_delivery")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    app.state.db = app.state.mongodb_client[DB_NAME]
    yield
    app.state.mongodb_client.close()


async def get_db(request: Request):
    return request.app.state.db
