"""
models/market_model_engine.py
=============================
Core mathematical engine for return calculations and Ordinary Least Squares (OLS) regression.
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd


def calculate_returns(prices: pd.Series, method: str = "log") -> pd.Series:
    """
    Calculate daily returns from a price series.

    Parameters
    ----------
    prices : pd.Series
        Series of prices sorted chronologically.
    method : str
        Return calculation method: 'log' or 'simple'.

    Returns
    -------
    pd.Series
        Daily returns Series with the first element dropped (NaN).
    """
    if prices.empty or len(prices) < 2:
        return pd.Series(dtype=float)

    if method.lower() == "log":
        # log returns = ln(P_t / P_{t-1})
        returns = np.log(prices / prices.shift(1))
    elif method.lower() == "simple":
        # simple returns = (P_t - P_{t-1}) / P_{t-1}
        returns = (prices - prices.shift(1)) / prices.shift(1)
    else:
        raise ValueError(f"Unknown return calculation method: '{method}'")

    return returns.dropna()


def estimate_ols(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """
    Estimate the parameters of the linear regression y = alpha + beta * x + epsilon
    using Ordinary Least Squares (OLS).

    Parameters
    ----------
    x : np.ndarray
        Independent variable (e.g., benchmark returns).
    y : np.ndarray
        Dependent variable (e.g., asset returns).

    Returns
    -------
    dict
        Estimation summary containing:
        - alpha
        - beta
        - r_squared
        - residual_variance
        - standard_error
        - beta_stderr
        - alpha_stderr
        - n_observations
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    n = len(x)
    if n < 3:
        raise ValueError(f"At least 3 observations are required for OLS estimation. Got {n}.")

    mean_x = np.mean(x)
    mean_y = np.mean(y)

    dev_x = x - mean_x
    dev_y = y - mean_y

    sum_sq_x = np.sum(dev_x**2)
    if sum_sq_x == 0:
        raise ValueError("Independent variable (x) has zero variance; cannot run regression.")

    sum_prod = np.sum(dev_x * dev_y)

    beta = sum_prod / sum_sq_x
    alpha = mean_y - beta * mean_x

    residuals = y - (alpha + beta * x)
    sum_sq_resid = np.sum(residuals**2)

    # Degrees of freedom for residuals is n - 2
    df = n - 2
    residual_variance = sum_sq_resid / df
    standard_error = np.sqrt(residual_variance)

    # R-squared
    sum_sq_total = np.sum(dev_y**2)
    if sum_sq_total == 0:
        r_squared = 0.0
    else:
        r_squared = 1.0 - (sum_sq_resid / sum_sq_total)

    # Standard errors of coefficients
    beta_stderr = np.sqrt(residual_variance / sum_sq_x)
    alpha_stderr = standard_error * np.sqrt((1.0 / n) + (mean_x**2 / sum_sq_x))

    return {
        "alpha": float(alpha),
        "beta": float(beta),
        "r_squared": float(r_squared),
        "residual_variance": float(residual_variance),
        "standard_error": float(standard_error),
        "beta_stderr": float(beta_stderr),
        "alpha_stderr": float(alpha_stderr),
        "n_observations": int(n),
    }
