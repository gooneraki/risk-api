""" Portfolio routes for the application. """
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
import yfinance as yf


from app.auth import get_current_user
from app.db import get_session
from app.models.db_models import AssetPosition, User
from app.models.yfinance_models import TickerSearchReference

router = APIRouter()


def validate_ticker(ticker):
    """ Validate a ticker symbol. """
    if not ticker:
        raise HTTPException(
            status_code=400, detail="Ticker symbol is required")

    if len(ticker) > 10:
        raise HTTPException(
            status_code=400, detail="Ticker symbol is too long (max 10 characters)")

    if not all(c.isalnum() or c == '.' or c == '^' for c in ticker):
        raise HTTPException(
            status_code=400, detail="Invalid ticker symbol format (only alphanumeric, " +
            "dots and carets allowed)")


def validate_ticker_with_yfinance(ticker):
    """ Validate a ticker symbol with yfinance. """
    try:
        info = yf.Ticker(ticker).info
        print(info)

        if not info or info.get('regularMarketPrice') is None:
            raise HTTPException(
                status_code=404, detail="Ticker not found or invalid.")
    except Exception as e:
        raise HTTPException(
            status_code=404, detail="Ticker not found or invalid.") from e


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

    assert user.id is not None, "Authenticated user must have an id"

    position.ticker = position.ticker.upper().strip()

    # Validate ticker symbol
    validate_ticker(position.ticker)

    # Check if ticker already exists for user
    existing = session.exec(select(AssetPosition).where(
        AssetPosition.user_id == user.id, AssetPosition.ticker == position.ticker)).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Position already exists. Use update instead.")

    # Validate ticker symbol with yfinance
    validate_ticker_with_yfinance(position.ticker)

    position.user_id = user.id
    session.add(position)
    session.commit()
    session.refresh(position)
    return position


@router.put("/portfolio/{symbol}", response_model=AssetPosition)
def update_position(
    symbol: str,
    quantity: float,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a position in the portfolio."""
    assert user.id is not None, "Authenticated user must have an id"

    symbol = symbol.upper().strip()

    # Check if position exists
    pos = session.exec(select(AssetPosition).where(
        AssetPosition.user_id == user.id, AssetPosition.ticker == symbol)).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found.")

    pos.quantity = quantity
    session.add(pos)
    session.commit()
    session.refresh(pos)
    return pos


@router.delete("/portfolio/{symbol}", status_code=204)
def delete_position(
    symbol: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a position from the portfolio."""
    symbol = symbol.upper().strip()

    pos = session.exec(select(AssetPosition).where(
        AssetPosition.user_id == user.id, AssetPosition.ticker == symbol)).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found.")

    session.delete(pos)
    session.commit()
    return


@router.get("/search_ticker", response_model=List[TickerSearchReference])
def search_ticker(q: str = Query(..., min_length=1, max_length=30)):
    """ Search for tickers by name or symbol using yfinance.Search. """
    try:
        data = yf.Search(q).quotes
        results = []
        for item in data:
            if not item.get("symbol") or not item.get("shortname"):
                continue

            results.append(item)

        return results[:10]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
