"""
src/data.py — Data fetching & feature engineering
"""
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler


FEATURE_COLS = [
    'Open', 'High', 'Low', 'Close', 'Volume',
    'SMA_10', 'SMA_50', 'RSI',
    'MACD', 'MACD_Signal',
    'BB_Upper', 'BB_Lower',
]
CLOSE_IDX = 3   # index of 'Close' inside FEATURE_COLS


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
        data = data.dropna()
        data = data.asfreq('B').ffill()
        return data
    except Exception:
        return None


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Append SMA(10/50), RSI(14), MACD+Signal, and Bollinger Bands(20).

    RSI is guarded against division-by-zero: when avg loss == 0, RSI = 100.
    """
    df = df.copy()

    # Moving Averages
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # RSI(14) — guarded against division by zero
    delta = df['Close'].diff()
    gain  = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    df['RSI'] = np.where(loss == 0, 100.0, 100.0 - (100.0 / (1.0 + gain / loss)))

    # MACD (12/26 EMA) + Signal line (9 EMA of MACD)
    ema12             = df['Close'].ewm(span=12, adjust=False).mean()
    ema26             = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD']        = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands (20-day, ±2 std)
    sma20          = df['Close'].rolling(window=20).mean()
    std20          = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = sma20 + 2 * std20
    df['BB_Lower'] = sma20 - 2 * std20

    return df.dropna()


def build_sequences(scaled_data: np.ndarray, seq_length: int):
    """Slide a window of seq_length steps over scaled_data.

    Returns:
        X : (N, seq_length, n_features)
        y : (N,)  — scaled Close values
    """
    X, y = [], []
    for i in range(seq_length, len(scaled_data)):
        X.append(scaled_data[i - seq_length:i])
        y.append(scaled_data[i, CLOSE_IDX])
    return np.array(X), np.array(y)


def split_data(X: np.ndarray, y: np.ndarray,
               train_ratio: float = 0.70,
               val_ratio:   float = 0.15):
    """Split into train / val / test. Enforces min 30 samples per split."""
    n         = len(X)
    val_split = int(train_ratio * n)
    split     = int((train_ratio + val_ratio) * n)

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
    """Inverse-transform scaled Close values back to real prices."""
    dummy               = np.zeros((len(values), n_features))
    dummy[:, CLOSE_IDX] = values
    return scaler.inverse_transform(dummy)[:, CLOSE_IDX]
