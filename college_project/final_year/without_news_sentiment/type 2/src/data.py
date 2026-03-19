"""
src/data.py — Data fetching & feature engineering  (v5 — Quant Factors)

Feature split
─────────────
  PRICE BRANCH  (16 features)  fed to CNN → BiLSTM → Self-Attention
      OHLCV (5)      : Open, High, Low, Close, Volume
      Trend (4)      : SMA_10, SMA_50, MACD, MACD_Signal
      Momentum (3)   : RSI, ROC_10, Stoch_K
      Volatility (3) : BB_Upper, BB_Lower, ATR
      Volume (1)     : OBV_norm

  FACTOR BRANCH (6 features)  fed to Factor BiLSTM → Cross-Attention
      Beta_60        : rolling 60-day CAPM beta vs SPY
      Alpha_60       : rolling Jensen's alpha, annualised
      Momentum_12_1  : Jegadeesh-Titman 12-1 month momentum factor
      Sharpe_60      : rolling 60-day Sharpe ratio
      Vol_Ratio      : 10-day vol / 60-day vol (regime signal)
      Mkt_Return     : SPY daily log return

  Prediction target (unchanged from v4)
      log return  =  log(Close[t] / Close[t-1])   — stationary
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf


# ── Feature column definitions ─────────────────────────────────────────────────

PRICE_FEATURE_COLS: list[str] = [
    'Open', 'High', 'Low', 'Close', 'Volume',
    'SMA_10', 'SMA_50', 'MACD', 'MACD_Signal',
    'RSI', 'ROC_10', 'Stoch_K',
    'BB_Upper', 'BB_Lower', 'ATR',
    'OBV_norm',
]

FACTOR_FEATURE_COLS: list[str] = [
    'Beta_60',
    'Alpha_60',
    'Momentum_12_1',
    'Sharpe_60',
    'Vol_Ratio',
    'Mkt_Return',
]

ALL_FEATURE_COLS  = PRICE_FEATURE_COLS + FACTOR_FEATURE_COLS
FEATURE_COLS      = ALL_FEATURE_COLS          # alias for app.py compatibility
CLOSE_IDX         = 3                         # Close index inside ALL_FEATURE_COLS
N_PRICE_FEATURES  = len(PRICE_FEATURE_COLS)   # 16
N_FACTOR_FEATURES = len(FACTOR_FEATURE_COLS)  # 6


# ── Data fetching ──────────────────────────────────────────────────────────────

@st.cache_data
def fetch_data(ticker: str, period_days: int) -> pd.DataFrame | None:
    """Download OHLCV data from Yahoo Finance."""
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=period_days)
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.dropna().asfreq('B').ffill()
        return data
    except Exception:
        return None


@st.cache_data
def fetch_market_data(period_days: int, market_ticker: str = "SPY") -> pd.DataFrame | None:
    """Download SPY for CAPM beta/alpha and market return features.

    Fetches 300 extra days of history beyond the requested period so that
    rolling 60-day windows are fully populated from the start of the
    ticker's date range.
    """
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=period_days + 300)
    try:
        data = yf.download(market_ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.dropna().asfreq('B').ffill()
        return data
    except Exception:
        return None


# ── Technical feature engineering ─────────────────────────────────────────────

def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Append 11 technical indicators → 16 price branch features total."""
    df = df.copy()

    df['SMA_10'] = df['Close'].rolling(10).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()

    ema12             = df['Close'].ewm(span=12, adjust=False).mean()
    ema26             = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD']        = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    delta         = df['Close'].diff()
    gain          = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss          = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    df['RSI']     = np.where(loss == 0, 100.0, 100.0 - (100.0 / (1.0 + gain / loss)))

    df['ROC_10']  = df['Close'].pct_change(10) * 100.0

    low14         = df['Low'].rolling(14).min()
    high14        = df['High'].rolling(14).max()
    denom         = (high14 - low14).replace(0.0, np.nan)
    df['Stoch_K'] = 100.0 * (df['Close'] - low14) / denom

    sma20          = df['Close'].rolling(20).mean()
    std20          = df['Close'].rolling(20).std()
    df['BB_Upper'] = sma20 + 2.0 * std20
    df['BB_Lower'] = sma20 - 2.0 * std20

    hl         = df['High'] - df['Low']
    hc         = (df['High'] - df['Close'].shift(1)).abs()
    lc         = (df['Low']  - df['Close'].shift(1)).abs()
    df['ATR']  = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()

    direction      = np.sign(df['Close'].diff()).fillna(0.0)
    obv            = (direction * df['Volume']).cumsum()
    obv_mu         = obv.rolling(20).mean()
    obv_sigma      = obv.rolling(20).std().replace(0.0, np.nan)
    df['OBV_norm'] = (obv - obv_mu) / obv_sigma

    return df


# ── Quantitative factor engineering ───────────────────────────────────────────

def add_quant_features(df: pd.DataFrame, market_df: pd.DataFrame) -> pd.DataFrame:
    """Append 6 quantitative factor features → 22 total features.

    Beta_60
        Rolling 60-day OLS: regress daily stock log returns on SPY log
        returns.  The slope is the CAPM beta — how much the stock amplifies
        or dampens market moves.  Beta > 1 = aggressive; < 1 = defensive.

    Alpha_60
        OLS intercept from the same regression, annualised (* 252).
        Positive alpha means the stock is generating excess return beyond
        what its beta-exposure to the market would predict.

    Momentum_12_1  (Jegadeesh & Titman, 1993)
        252-day cumulative return minus 21-day cumulative return.
        Captures medium-term price momentum while excluding the short-term
        reversal effect.  One of the most robust return predictors in
        empirical finance.

    Sharpe_60
        Rolling 60-day annualised Sharpe = mean_daily_return /
        std_daily_return * sqrt(252).  A falling Sharpe warns of
        deteriorating risk-adjusted performance before price breaks down.

    Vol_Ratio
        10-day realised volatility / 60-day realised volatility.
        Values > 1 indicate rising short-term volatility relative to the
        long-run baseline — a classic risk-off regime indicator.

    Mkt_Return
        SPY daily log return (contemporaneous).  Gives the model a
        direct read of the macro environment on each day.
    """
    df = df.copy()

    mkt_close    = market_df['Close'].reindex(df.index, method='ffill')
    stock_ret    = np.log(df['Close'] / df['Close'].shift(1))
    mkt_ret      = np.log(mkt_close  / mkt_close.shift(1))
    df['Mkt_Return'] = mkt_ret

    # Rolling CAPM beta & Jensen's alpha (vectorised rolling OLS)
    WINDOW = 60
    sr     = stock_ret.values
    mr     = mkt_ret.values
    n      = len(df)
    betas  = np.full(n, np.nan)
    alphas = np.full(n, np.nan)

    for i in range(WINDOW, n):
        y    = sr[i - WINDOW : i]
        x    = mr[i - WINDOW : i]
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 20:
            continue
        xf, yf = x[mask], y[mask]
        xm, ym = xf.mean(), yf.mean()
        xc     = xf - xm
        ss_x   = (xc * xc).sum()
        if ss_x < 1e-12:
            continue
        beta       = float((xc * (yf - ym)).sum() / ss_x)
        betas[i]   = beta
        alphas[i]  = float((ym - beta * xm) * 252)   # annualise

    df['Beta_60']  = betas
    df['Alpha_60'] = alphas

    # Jegadeesh-Titman momentum (12-month minus 1-month)
    df['Momentum_12_1'] = (
        df['Close'].pct_change(252) - df['Close'].pct_change(21)
    ) * 100.0

    # Rolling Sharpe (60-day)
    rm60         = stock_ret.rolling(WINDOW).mean()
    rs60         = stock_ret.rolling(WINDOW).std().replace(0.0, np.nan)
    df['Sharpe_60'] = (rm60 / rs60) * np.sqrt(252)

    # Volatility regime ratio
    short_vol       = stock_ret.rolling(10).std()
    long_vol        = stock_ret.rolling(WINDOW).std().replace(0.0, np.nan)
    df['Vol_Ratio'] = short_vol / long_vol

    return df.dropna()


# ── Sequence building ──────────────────────────────────────────────────────────

def build_sequences(
    scaled_data: np.ndarray,
    raw_close:   np.ndarray,
    seq_length:  int,
) -> tuple[np.ndarray, np.ndarray]:
    """Slide a window; target y = log return (stationary — prevents mean collapse).

    Returns:
        X : (N, seq_length, 22)   scaled feature windows
        y : (N,)                  log returns
    """
    log_returns = np.log(raw_close[1:] / raw_close[:-1])
    X, y = [], []
    for i in range(seq_length, len(scaled_data)):
        X.append(scaled_data[i - seq_length : i])
        y.append(log_returns[i - 1])
    return np.array(X), np.array(y)


# ── Price reconstruction ───────────────────────────────────────────────────────

def returns_to_prices(log_returns: np.ndarray, start_price: float) -> np.ndarray:
    """price[t] = start_price × exp(cumsum(log_returns[0..t]))"""
    return start_price * np.exp(np.cumsum(log_returns))


# ── Train / val / test split ───────────────────────────────────────────────────

def split_data(
    X: np.ndarray, y: np.ndarray,
    train_ratio: float = 0.70,
    val_ratio:   float = 0.15,
) -> tuple:
    n         = len(X)
    val_split = int(train_ratio * n)
    split     = int((train_ratio + val_ratio) * n)
    min_s     = 30
    if (split - val_split) < min_s:
        val_split = max(0, split - min_s)
    if (n - split) < min_s:
        split = max(val_split + min_s, n - min_s)
    return (
        (X[:val_split],      y[:val_split]),
        (X[val_split:split], y[val_split:split]),
        (X[split:],          y[split:]),
        split,
        val_split,
    )


def inverse_close(
    values: np.ndarray, scaler: MinMaxScaler, n_features: int
) -> np.ndarray:
    """Legacy: inverse-transform scaled Close values (kept for compatibility)."""
    dummy               = np.zeros((len(values), n_features))
    dummy[:, CLOSE_IDX] = values
    return scaler.inverse_transform(dummy)[:, CLOSE_IDX]