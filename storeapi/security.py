import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from storeapi.config import config
from storeapi.database import database, user_table

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def access_token_expire_minutes():
    return 30


def confirm_token_expire_minutes():
    return 1440


def create_access_token(email: str):
    logger.debug("creating acsses token", extra={"email": email})
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encodes_jwt = jwt.encode(jwt_data, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encodes_jwt


def create_confirmationToken(email: str):
    logger.debug("creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {
        "sub": email,
        "exp": expire,
        "type": "confirmation",
    }
    encodes_jwt = jwt.encode(jwt_data, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encodes_jwt


def get_subject_for_token_type(
    token: str, type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    email: str = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing subject claim")

    token_type = payload.get("type")
    if type is None or token_type != type:
        raise create_credentials_exception("Token type mismatch")

    return email


def get_password_hash(password: str):
    return pwd_context.hash(password)


def varify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    logger.debug("feching user from database")
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.debug("authrecated user")
    user = await get_user(email)
    if not user:
        raise create_credentials_exception("Invalid email or password")
    if not varify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    email = get_subject_for_token_type(token, "access")
    user = await get_user(email=email)
    if user is None:
        raise create_credentials_exception("Could not find user with this token")

    return user
