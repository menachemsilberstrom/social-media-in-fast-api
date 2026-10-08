import os
import secrets
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

test_db_fd, test_db_path = tempfile.mkstemp(
    prefix="storeapi-test-", suffix=".db", dir=Path.cwd()
)
os.close(test_db_fd)

os.environ["ENV_STATE"] = "test"
os.environ["TEST_DATABASE_URL"] = f"sqlite:///{Path(test_db_path).name}"
os.environ.setdefault("TEST_SECRET_KEY", secrets.token_urlsafe(32))
os.environ.setdefault("TEST_ALGORITHM", "HS256")

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from storeapi.database import database, engine, metadata, user_table
from storeapi.main import app


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    yield
    engine.dispose()
    Path(test_db_path).unlink(missing_ok=True)


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
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict) -> str:
    response = await async_client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    return response.json()["access_token"]