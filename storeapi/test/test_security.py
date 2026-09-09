import pytest
from jose import jwt

from storeapi import security
from storeapi.config import config


@pytest.mark.anyio
async def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30


@pytest.mark.anyio
async def test_create_access_token():
    token = security.cerate_access_token("123")
    assert {"sub": "123"}.items() <= jwt.decode(
        token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    ).items()


@pytest.mark.anyio
async def test_password_hashed():
    password = "password"
    assert security.varify_password(password, security.get_password_hash(password))


@pytest.mark.anyio
async def test_get_user(registed_user: dict):
    user = await security.get_user(registed_user["email"])

    assert user.email == registed_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(registed_user: dict):
    user = await security.authenticate_user(
        registed_user["email"], registed_user["password"]
    )
    assert user.email == registed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.net", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registed_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registed_user["email"], "wrong password")