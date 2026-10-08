import datetime
import logging

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from storeapi.config import config
from storeapi.database import database, user_table

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


cradentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="could not validate cradentials",
)


def access_token_expire_minutes():
    return 30


def create_access_token(email: str):
    logger.debug("creating acsses token", extra={"email": email})
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire}
    encodes_jwt = jwt.encode(jwt_data, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encodes_jwt


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
        raise cradentials_exception
    if not varify_password(password, user.password):
        raise cradentials_exception
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except JWTError as e:
        raise credentials_exception from e

    # שליפת המשתמש במסד הנתונים
    user = await get_user(email=email)
    if user is None:
        raise credentials_exception

    return user
