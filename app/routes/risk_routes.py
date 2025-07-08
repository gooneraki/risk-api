""" Routes for risk metrics calculation. """
import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException
from app.models.models import PriceInput, TickerInput
from app.utils import calculate_risk_from_prices

router = APIRouter()


@router.post("/risk_metrics")
def risk_from_prices(data: PriceInput):
    """ Calculate risk metrics from a list of prices. """
    prices = pd.Series(data.prices)

    if len(prices) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 prices required")

    return calculate_risk_from_prices(prices)


@router.post("/risk_metrics_from_ticker")
def risk_from_ticker(ticker_input: TickerInput):
    """ Calculate risk metrics from a stock ticker. """
    ticker = ticker_input.ticker.upper().strip()

    # Basic ticker validation
    if not ticker or len(ticker) > 10:
        raise HTTPException(
            status_code=400, detail="Invalid ticker symbol length (max 10)")

    # Only allow alphanumeric characters and dots
    if not all(c.isalnum() or c == '.' or c == '^' for c in ticker):
        raise HTTPException(
            status_code=400, detail="Invalid ticker symbol format (only alphanumeric," +
            " dots and carets allowed)")

    try:
        df = yf.download(ticker, period="6mo", progress=False)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch data for {ticker}: {str(e)}") from e

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data found")

    prices = df["Close"].dropna()
    if not isinstance(prices, pd.DataFrame):
        raise HTTPException(status_code=500, detail="Invalid data format")

    if len(prices) < 2:
        raise HTTPException(status_code=400, detail="Not enough data")

    return {
        "ticker": ticker,
        **calculate_risk_from_prices(prices)
    }
