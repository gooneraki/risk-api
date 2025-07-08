""" User routes for the application. """
import os
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.db import get_session

from app.models.db_models import User
from app.auth import create_access_token, hash_password, verify_password

router = APIRouter()


def normalize_username(username: str) -> str:
    """Normalize username: lowercase, remove spaces, only alphanumeric, max 15 chars."""
    username = username.lower().replace(' ', '')
    username = re.sub(r'[^a-z0-9]', '', username)
    return username[:15]


def is_valid_username(username: str) -> bool:
    """Check if username is only alphanumeric, no spaces, max 15 chars, not empty."""
    return bool(username) and username.isalnum() and len(username) > 2 and len(username) <= 15


@router.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """ Register a new user. """
    norm_username = normalize_username(form.username)
    if not is_valid_username(norm_username):
        raise HTTPException(
            status_code=400, detail="Invalid username: must be alphanumeric, no spaces, " +
            "min 3 chars, max 15 chars.")
    user = session.exec(select(User).where(
        User.username == norm_username)).first()

    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=norm_username,
                    hashed_password=hash_password(form.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User registered successfully"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """ Login a user. """
    norm_username = normalize_username(form.username)
    user = session.exec(select(User).where(
        User.username == norm_username)).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/users")
def list_users(session: Session = Depends(get_session)):
    """ List all users. """
    if os.getenv("ENV", "dev") == "prod":
        raise HTTPException(
            status_code=403, detail="Not allowed in production")
    users = session.exec(select(User)).all()
    return [{"id": user.id, "username": user.username} for user in users]
