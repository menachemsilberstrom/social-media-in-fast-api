import pytest
from fastapi import HTTPException
from jose import jwt

from storeapi import security
from storeapi.config import config


@pytest.mark.anyio
async def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30


@pytest.mark.anyio
async def test_confirm_token_expire_minutes():
    assert security.confirm_token_expire_minutes() == 1440


@pytest.mark.anyio
async def test_create_access_token():
    token = security.create_access_token("123")
    assert {"sub": "123", "type": "access"}.items() <= jwt.decode(
        token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    ).items()


@pytest.mark.anyio
async def test_create_confirmationToken():
    token = security.create_confirmation_token("123")
    assert {"sub": "123", "type": "confirmation"}.items() <= jwt.decode(
        token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
    ).items()


@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_confirmation():
    token = security.create_confirmation_token("123")
    subject = security.get_subject_for_token_type(token, "confirmation")
    assert subject == "123"


@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_access():
    token = security.create_access_token("123")
    subject = security.get_subject_for_token_type(token, "access")
    assert subject == "123"


@pytest.mark.anyio
async def test_get_subject_for_token_type_expired(mocker):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token("123")
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert exc_info.value.status_code == 401
    assert "Token has expired" in exc_info.value.detail


@pytest.mark.anyio
async def test_get_subject_for_invalid_token():
    token = "Invalid token"
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert exc_info.value.status_code == 401
    assert "Invalid token" == exc_info.value.detail


@pytest.mark.anyio
async def test_get_subject_for_token_type_missing_sub():
    email = "123@example.com"
    token = security.create_access_token(email)
    # Remove the 'sub' claim to simulate a missing subject
    payload = jwt.decode(token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM])
    del payload["sub"]
    token = jwt.encode(payload, key=config.SECRET_KEY, algorithm=config.ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert exc_info.value.status_code == 401
    assert "Token is missing subject claim" == exc_info.value.detail


@pytest.mark.anyio
async def test_password_hashed():
    password = "password"
    assert security.varify_password(password, security.get_password_hash(password))


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.net", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["email"], "wrong password")


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user["email"] == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.anyio
async def test_get_current_user_expired_token(registered_user: dict, mocker):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(registered_user["email"])
    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user(token)
    assert exc_info.value.status_code == 401
    assert "Token has expired" in exc_info.value.detail
