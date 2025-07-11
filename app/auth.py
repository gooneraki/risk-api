""" Authentication utilities for the application. """
from datetime import datetime, timedelta
from typing import Union
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import Session, select
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import settings
from app.db import get_session
from app.models.db_models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def secret_key():
    """ Get the secret key. """
    if not settings.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")
    return settings.jwt_secret_key


def verify_password(plain_password, hashed_password):
    """ Verify a password against a hashed password. """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    """ Hash a password. """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """ Create an access token. """
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key(), algorithm="HS256")


def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: Session = Depends(get_session)):
    """ Get the current user from the token. """

    try:
        payload = jwt.decode(token, secret_key(), algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"})
    except JWTError as exc:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}) from exc

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"})
    return user
