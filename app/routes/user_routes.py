""" User routes for the application. """
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.db import get_session

from app.models.db_models import User
from app.auth import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """ Register a new user. """
    user = session.exec(select(User).where(
        User.username == form.username)).first()

    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=form.username,
                    hashed_password=hash_password(form.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User registered successfully"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """ Login a user. """
    user = session.exec(select(User).where(
        User.username == form.username)).first()
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
