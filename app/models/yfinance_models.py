""" Yfinance models for the application. """
from typing import Optional
from pydantic import BaseModel


class TickerSearchReference(BaseModel):
    """ A reference to a ticker search result. """
    symbol: str
    shortname: str
    exchange: Optional[str] = None
    quoteType: Optional[str] = None
    longname: Optional[str] = None
    index: Optional[str] = None
    score: Optional[float] = None
    typeDisp: Optional[str] = None
    exchDisp: Optional[str] = None
    isYahooFinance: Optional[bool] = None
