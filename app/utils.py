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

    mean_return = returns.mean()
    volatility = returns.std()

    sharpe_ratio = mean_return / volatility
    drawdown = (prices / prices.cummax()) - 1
    max_drawdown = drawdown.min()

    return {
        "mean_return": round(_safe_float(mean_return), 4),
        "volatility": round(_safe_float(volatility), 4),
        "sharpe_ratio": round(_safe_float(sharpe_ratio), 2),
        "max_drawdown": round(_safe_float(max_drawdown), 4)
    }
