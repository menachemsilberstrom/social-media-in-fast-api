import os
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from storeapi.database import database, engine, metadata, user_table

os.environ["ENV_STATE"] = "test"
from storeapi.main import app


@pytest.fixture(scope="session")
def anyio_backends():
    return "asyncio"


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
async def async_db() -> AsyncGenerator:
    metadata.drop_all(engine)
    metadata.create_all(engine)
    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=client.base_url
    ) as ac:
        yield ac


@pytest.fixture()
async def registed_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details
