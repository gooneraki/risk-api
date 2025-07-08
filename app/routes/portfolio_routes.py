""" Portfolio routes for the application. """
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth import get_current_user
from app.db import get_session
from app.models.db_models import AssetPosition, User

router = APIRouter()


@router.get("/portfolio", response_model=List[AssetPosition])
def get_portfolio(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """ Get the portfolio for a user. """
    return session.exec(select(AssetPosition).where(AssetPosition.user_id == user.id)).all()


@router.post("/portfolio", response_model=AssetPosition)
def add_position(
    position: AssetPosition,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """ Add a position to the portfolio. """
    if user.id is None:
        raise ValueError("User ID cannot be None")
    position.user_id = user.id

    session.add(position)
    session.commit()
    session.refresh(position)
    return position
