""" Portfolio routes for the application. """
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
import yfinance as yf
import httpx

from app.config import settings
from app.auth import get_current_user
from app.db import get_session
from app.models.db_models import AssetPosition, User
from app.models.yfinance_models import TickerSearchReference
from app.redis_service import redis_service

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
async def add_position(
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

    # Publish ticker update event to Redis
    try:
        await redis_service.publish_ticker_update(
            ticker=position.ticker,
            user_id=user.id,
            action="add"
        )
    except Exception as e:
        print(f"⚠️  Failed to publish ticker update event: {e}")
        # Don't fail the request if Redis is unavailable

    return position


@router.put("/portfolio/{symbol}", response_model=AssetPosition)
async def update_position(
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

    # Publish ticker update event to Redis
    try:
        await redis_service.publish_ticker_update(
            ticker=symbol,
            user_id=user.id,
            action="update"
        )
    except Exception as e:
        print(f"⚠️  Failed to publish ticker update event: {e}")
        # Don't fail the request if Redis is unavailable

    return pos


@router.delete("/portfolio/{symbol}", status_code=204)
async def delete_position(
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

    # Publish ticker update event to Redis
    try:
        if user.id is not None:
            await redis_service.publish_ticker_update(
                ticker=symbol,
                user_id=user.id,
                action="delete"
            )
    except Exception as e:
        print(f"⚠️  Failed to publish ticker update event: {e}")
        # Don't fail the request if Redis is unavailable

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
    except (ConnectionError, TimeoutError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    """ Get the current user. """
    return user


@router.get("/redis-info")
async def redis_info():
    """Get Redis connection information for debugging."""
    try:
        info = await redis_service.get_redis_info()
        return {
            "redis_status": info,
            "environment": {
                "REDIS_HOST": settings.redis_config.host,
                "REDIS_PORT": settings.redis_config.port,
                "REDIS_URL": "***" if settings.redis_config.url else None
            }
        }
    except Exception as e:
        return {
            "redis_status": {
                "connection_status": "error",
                "error": str(e)
            },
            "environment": {
                "REDIS_HOST": settings.redis_config.host,
                "REDIS_PORT": settings.redis_config.port,
                "REDIS_URL": "***" if settings.redis_config.url else None
            }
        }


@router.post("/trigger-price-update")
async def trigger_price_update(request: dict):
    """Trigger a price update for a ticker via Redis pub/sub."""
    ticker = request.get("ticker")
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    ticker = ticker.upper().strip()

    try:
        # Publish ticker update event to Redis
        await redis_service.publish_ticker_update(
            ticker=ticker,
            user_id=0,  # System triggered
            action="fetch"
        )

        return {
            "message": f"Price update triggered for {ticker}",
            "ticker": ticker,
            "status": "success"
        }
    except Exception as e:
        print(f"⚠️  Failed to trigger price update: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Price update service unavailable",
                "message": f"Cannot trigger price update for {ticker}. " +
                "Redis pub/sub is unavailable.",
                "suggestion": "Start Redis service or use /search_ticker " +
                "to verify ticker information."
            }
        ) from e


@router.get("/latest-price/{ticker}")
async def get_latest_price(ticker: str):
    """Get the latest price for a ticker from Redis cache or risk-worker."""

    try:
        # First try Redis cache
        try:
            price = await redis_service.get_latest_price(ticker)
            if price is not None:
                return {
                    "ticker": ticker.upper(),
                    "price": price,
                    "source": "redis_cache"
                }
        except Exception as e:
            print(f"⚠️  Redis cache unavailable: {e}")

        # If not in cache, try to get from risk-worker
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://risk-worker:8000/latest-price/{ticker}")
                if response.status_code == 200:
                    data = response.json()
                    # Try to cache the price for future requests
                    try:
                        await redis_service.set_latest_price(ticker, data["price"])
                    except Exception as cache_e:
                        print(f"⚠️  Could not cache price: {cache_e}")
                    return {
                        "ticker": ticker.upper(),
                        "price": data["price"],
                        "source": "risk_worker"
                    }
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"⚠️  Risk-worker unavailable: {e}")

        # If all services are unavailable, provide helpful error message
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Price service unavailable",
                "message": f"Cannot fetch price for {ticker.upper()}. " +
                "Both Redis cache and risk-worker are unavailable.",
                "suggestion": "Try using /search_ticker to verify the ticker symbol, " +
                "or check service status."
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving price for {ticker}: {str(e)}"
        ) from e
