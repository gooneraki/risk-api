""" Models for risk metrics calculation inputs. """
from pydantic import BaseModel


class PriceInput(BaseModel):
    """Input model for risk metrics calculation from prices."""
    prices: list[float]


class TickerInput(BaseModel):
    """Input model for risk metrics calculation from a ticker."""
    ticker: str
