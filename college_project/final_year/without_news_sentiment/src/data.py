"""
src/data.py — Data fetching & feature engineering
"""
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler


FEATURE_COLS = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_10', 'SMA_50', 'RSI']
CLOSE_IDX = 3   # index of 'Close' inside FEATURE_COLS


@st.cache_data
def fetch_data(ticker: str, period_days: int) -> pd.DataFrame | None:
    """Download OHLCV data from Yahoo Finance.

    Returns a clean DataFrame indexed by business-day dates,
    or None if the ticker is invalid / the request fails.
    """
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=period_days)
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None
        # yfinance sometimes returns MultiIndex columns — flatten them
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.dropna()
        data = data.asfreq('B').ffill()
        return data
    except Exception:
        return None


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Append SMA(10), SMA(50) and RSI(14) columns, then drop NaN rows."""
    df = df.copy()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    delta        = df['Close'].diff()
    gain         = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss         = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI']    = 100 - (100 / (1 + gain / loss))
    return df.dropna()


def build_sequences(scaled_data: np.ndarray, seq_length: int):
    """Slide a window of `seq_length` steps over scaled_data.

    Returns:
        X : (N, seq_length, n_features)
        y : (N,)   — scaled Close values (index 3)
    """
    X, y = [], []
    for i in range(seq_length, len(scaled_data)):
        X.append(scaled_data[i - seq_length:i])
        y.append(scaled_data[i, CLOSE_IDX])
    return np.array(X), np.array(y)


def split_data(X: np.ndarray, y: np.ndarray,
               train_ratio: float = 0.70,
               val_ratio:   float = 0.15):
    """Split (X, y) into train / val / test sets using absolute ratios.

    Default proportions:  70 % train | 15 % val | 15 % test
    Both train_ratio and val_ratio are fractions of the *total* dataset,
    so the splits are predictable regardless of dataset size.

    A minimum of 30 samples is enforced for val and test so that early
    stopping and evaluation are meaningful even on short histories.

    Returns:
        (X_train, y_train), (X_val, y_val), (X_test, y_test), split, val_split
        where `split`     = start index of test set
              `val_split` = start index of val set
    """
    n = len(X)
    val_split = int(train_ratio * n)
    split     = int((train_ratio + val_ratio) * n)

    # Enforce minimums so val/test are never too small to be useful
    min_samples = 30
    if (split - val_split) < min_samples:
        val_split = max(0, split - min_samples)
    if (n - split) < min_samples:
        split = max(val_split + min_samples, n - min_samples)

    X_train, y_train = X[:val_split],      y[:val_split]
    X_val,   y_val   = X[val_split:split], y[val_split:split]
    X_test,  y_test  = X[split:],          y[split:]

    return (X_train, y_train), (X_val, y_val), (X_test, y_test), split, val_split


def inverse_close(values: np.ndarray, scaler: MinMaxScaler, n_features: int) -> np.ndarray:
    """Inverse-transform a 1-D array of scaled Close values back to real prices."""
    dummy          = np.zeros((len(values), n_features))
    dummy[:, CLOSE_IDX] = values
    return scaler.inverse_transform(dummy)[:, CLOSE_IDX]
