""" Utility functions for risk metrics calculation. """
import pandas as pd


def _safe_float(value):
    """ Safely convert pandas Series or scalar to float. """
    if isinstance(value, pd.Series):
        if value.shape[0] > 1:
            raise ValueError("Series has more than one element")
        return float(value.iloc[0])
    return float(value)


def calculate_risk_from_prices(prices: pd.Series | pd.DataFrame):
    """ Calculate risk metrics from a series of prices. """
    returns = prices.pct_change().dropna()

    mean_return = _safe_float(returns.mean())
    volatility = _safe_float(returns.std())

    # Avoid division by zero
    if volatility == 0:
        sharpe_ratio = 999
    else:
        sharpe_ratio = mean_return / volatility
    drawdown = (prices / prices.cummax()) - 1
    max_drawdown = drawdown.min()

    return {
        "mean_return": round(mean_return, 4),
        "volatility": round(volatility, 4),
        "sharpe_ratio": round(_safe_float(sharpe_ratio), 2),
        "max_drawdown": round(_safe_float(max_drawdown), 4)
    }
