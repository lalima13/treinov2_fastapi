import asyncio
import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", f"sqlite:///tests.db")


@pytest_asyncio.fixture
async def db():
    from src.database import database, engine, metadata
    from src.models.post import posts

    await database.connect()
    metadata.create_all(engine)

    yield

    await database.disconnect()
    metadata.drop_all(engine)

@pytest_asyncio.fixture
async def client(db):
    from src.main import app         

    transport = ASGITransport(app=app)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }           
    async with AsyncClient(base_url="http://test", transport=transport, headers=headers) as client:
        yield client


@pytest_asyncio.fixture
async def access_token(client: AsyncClient):
    response = await client.post("/auth/login", json={"user_id":1})
    return response.json()["access_token"] 