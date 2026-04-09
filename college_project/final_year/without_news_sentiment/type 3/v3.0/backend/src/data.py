"""
backend/src/data.py — Fixed version
Fixes: MultiIndex normalization, missing returns_to_prices, GDP now uses real ETF data.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

# ── Feature column registry ───────────────────────────────────────────────────
PRICE_FEATURE_COLS: list[str] = [
    "Open", "High", "Low", "Close", "Volume",
    "SMA_10", "SMA_50", "MACD", "MACD_Signal",
    "RSI", "ROC_10", "Stoch_K",
    "BB_Upper", "BB_Lower", "ATR",
    "OBV_norm", "RVI",
]

FACTOR_FEATURE_COLS: list[str] = [
    "Beta_60", "Alpha_60", "Momentum_12_1", "Sharpe_60", "Vol_Ratio", "Mkt_Return",
    "Bond_5Y", "Bond_10Y",
    "Gold", "Silver", "Copper", "Aluminium", "Brent_Oil",
    "Buffett_Proxy",
]

FEATURE_COLS      = PRICE_FEATURE_COLS + FACTOR_FEATURE_COLS
CLOSE_IDX         = PRICE_FEATURE_COLS.index("Close")   # 3
N_PRICE_FEATURES  = len(PRICE_FEATURE_COLS)
N_FACTOR_FEATURES = len(FACTOR_FEATURE_COLS)

_GDP_ETFS: dict[str, str] = {
    "US":     "SPY",
    "India":  "INDA",
    "China":  "FXI",
    "EU":     "EZU",
    "Japan":  "EWJ",
    "UK":     "EWU",
    "Brazil": "EWZ",
}

_COMMODITY_TICKERS: dict[str, str] = {
    "Gold":      "GC=F",
    "Silver":    "SI=F",
    "Copper":    "HG=F",
    "Aluminium": "ALI=F",
    "Brent_Oil": "BZ=F",
}

# ── In-memory cache ───────────────────────────────────────────────────────────
_CACHE: dict[str, tuple[float, object]] = {}
_TTL   = 3600.0

def _cache_get(key: str):
    entry = _CACHE.get(key)
    if entry and (time.time() - entry[0]) < _TTL:
        return entry[1]
    return None

def _cache_set(key: str, value):
    _CACHE[key] = (time.time(), value)
    return value

# ── Robust yfinance column normalizer ─────────────────────────────────────────
def _normalize_columns(df: pd.DataFrame, tickers: list[str] | None = None) -> pd.DataFrame:
    """
    Flatten MultiIndex columns produced by yf.download(multiple_tickers).
    When tickers is provided, returns a DataFrame with those tickers as columns
    (each column = the Close price for that ticker).
    When tickers is None, returns a normal OHLCV DataFrame for a single ticker.
    """
    if df is None or df.empty:
        return df

    if not isinstance(df.columns, pd.MultiIndex):
        # Single ticker — just rename Adj Close if needed
        if "Adj Close" in df.columns and "Close" not in df.columns:
            df = df.rename(columns={"Adj Close": "Close"})
        return df

    # MultiIndex from multi-ticker download.
    # yfinance 0.2+ produces (field, ticker) at levels (0, 1).
    # Example: df["Close"]["AAPL"] or df[("Close", "AAPL")]
    level_0 = list(df.columns.get_level_values(0).unique())
    level_1 = list(df.columns.get_level_values(1).unique())

    if tickers is not None:
        # Caller wants per-ticker Close prices
        close_field = "Close" if "Close" in level_0 else ("Adj Close" if "Adj Close" in level_0 else None)
        if close_field:
            try:
                result = df[close_field]
                # Rename ^FVX → Bond_5Y style if a mapping was passed
                return result
            except Exception:
                pass

        # Fallback: flatten and pick ticker-named columns
        df.columns = [
            str(col[1]) if col[1] else str(col[0])
            for col in df.columns
        ]
        return df

    # Single-ticker multi-index — just take level 0 (field names)
    try:
        df.columns = df.columns.get_level_values(0)
    except Exception:
        df.columns = ["_".join(str(c) for c in col).strip("_") for col in df.columns]

    if "Adj Close" in df.columns and "Close" not in df.columns:
        df = df.rename(columns={"Adj Close": "Close"})

    return df

# ── Data fetching ─────────────────────────────────────────────────────────────
def fetch_data(ticker: str, period_days: int) -> Optional[pd.DataFrame]:
    key = f"price:{ticker}:{period_days}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        end   = datetime.today()
        start = end - timedelta(days=period_days + 100)
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None
        df = _normalize_columns(df)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        df = df.asfreq("B").ffill()
        return _cache_set(key, df)
    except Exception as e:
        print(f"[fetch_data] {e}")
        return None

def fetch_market_data(period_days: int, ticker: str = "SPY") -> Optional[pd.DataFrame]:
    key = f"market:{ticker}:{period_days}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        end   = datetime.today()
        start = end - timedelta(days=period_days + 400)
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None
        df = _normalize_columns(df)
        df = df.dropna().asfreq("B").ffill()
        return _cache_set(key, df)
    except Exception as e:
        print(f"[fetch_market_data] {e}")
        return None


# ── Global bond yield sources ─────────────────────────────────────────────────
# Tier 1 — Yahoo Finance direct yield tickers (US only, reliable).
# Tier 2 — ETF-based synthetic yield proxy anchored to known levels.
# Tier 3 — Flat series at consensus anchor (if ETF download also fails).

_YAHOO_BOND_TICKERS: dict[str, str] = {
    "US_5Y":  "^FVX",
    "US_10Y": "^TNX",
}

# For foreign sovereigns: use a country equity ETF to capture macro movement shape,
# then anchor that shape to a known realistic yield level.
# anchor  = approximate current 10Y yield in % (as of early 2025)
# sensitivity = how strongly this country's yield tracks the US 10Y (0=independent, 1=fully correlated)
_ETF_YIELD_PROXIES: dict[str, dict] = {
    "India_10Y":   {"etf": "INDA", "anchor": 6.80, "sensitivity": 0.30},
    "Germany_10Y": {"etf": "EZU",  "anchor": 2.45, "sensitivity": 0.70},
    "UK_10Y":      {"etf": "EWU",  "anchor": 4.40, "sensitivity": 0.85},
    "Japan_10Y":   {"etf": "EWJ",  "anchor": 1.10, "sensitivity": 0.10},
}

_YIELD_MIN, _YIELD_MAX = 0.01, 20.0   # plausible sovereign yield range (%)

def _validate_yield_series(s: pd.Series) -> bool:
    """True only if series looks like a real yield, not a price."""
    if s is None or len(s) < 5:
        return False
    return _YIELD_MIN <= float(s.median()) <= _YIELD_MAX

def _fetch_yahoo_yield(ticker: str, start, end) -> Optional[pd.Series]:
    """Fetch a real yield series from Yahoo Finance with sanity validation."""
    try:
        raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if raw is None or raw.empty:
            return None
        raw = _normalize_columns(raw)
        for col in ("Close", "Adj Close"):
            if col in raw.columns:
                s = pd.to_numeric(raw[col], errors="coerce").dropna()
                if _validate_yield_series(s):
                    return s
        return None
    except Exception as e:
        print(f"[_fetch_yahoo_yield] {ticker}: {e}")
        return None

def _build_synthetic_yield(
    etf: str,
    anchor: float,
    sensitivity: float,
    us10y_series: Optional[pd.Series],
    start, end,
) -> pd.Series:
    """
    Build a realistic foreign bond yield proxy:
      1. Download country ETF to get a macro-movement shape.
      2. Smooth log-returns into a normalised drift signal (±0.5 yield pts).
      3. Add US 10Y co-movement scaled by sensitivity.
      4. Anchor the whole series to known recent yield level.
      5. If ETF fails, fall back to a flat series at the anchor with tiny noise.
    """
    try:
        raw = yf.download(etf, start=start, end=end, progress=False, auto_adjust=True)
        if raw is None or raw.empty:
            raise ValueError("empty ETF download")
        raw = _normalize_columns(raw)
        if "Close" not in raw.columns:
            raise ValueError("no Close column")

        prices    = raw["Close"].dropna()
        log_ret   = np.log(prices / prices.shift(1)).dropna()
        cum_drift = log_ret.rolling(20).mean().cumsum().fillna(0)

        rng = cum_drift.max() - cum_drift.min()
        normalised = ((cum_drift - cum_drift.mean()) / rng) if rng > 1e-6 else cum_drift * 0

        # US co-movement component
        if us10y_series is not None:
            us_aligned = us10y_series.reindex(normalised.index, method="ffill").fillna(method="bfill")
            us_delta   = (us_aligned - float(us_aligned.mean())).fillna(0)
            yield_s    = anchor + normalised * 0.5 + us_delta * sensitivity
        else:
            yield_s = anchor + normalised * 0.5

        yield_s = yield_s.clip(_YIELD_MIN, _YIELD_MAX)
        yield_s = yield_s[(yield_s.index >= pd.Timestamp(start)) &
                          (yield_s.index <= pd.Timestamp(end))]
        if len(yield_s) < 5:
            raise ValueError("too short after filtering")

        print(f"[bond_proxy] {etf} → range [{float(yield_s.min()):.2f}–{float(yield_s.max()):.2f}]%")
        return yield_s

    except Exception as e:
        print(f"[bond_proxy] {etf}: {e} — using flat anchor {anchor}%")
        bday_range = pd.bdate_range(start=start, end=end)
        rng_obj    = np.random.default_rng(42)
        noise      = rng_obj.normal(0, 0.04, len(bday_range))
        return pd.Series(
            np.clip(anchor + noise, _YIELD_MIN, _YIELD_MAX), index=bday_range
        )

def fetch_bond_yields(period_days: int) -> Optional[pd.DataFrame]:
    """
    Fetch sovereign bond yields using a 3-tier strategy:
      Tier 1 — Yahoo Finance direct tickers (US 5Y + 10Y, reliable).
      Tier 2 — ETF-movement-shaped synthetic yield anchored to real levels.
      Tier 3 — Flat anchor with minor noise (always succeeds).
    """
    key = f"bonds_v4:{period_days}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        end   = datetime.today()
        start = end - timedelta(days=period_days + 50)
        frames: dict[str, pd.Series] = {}

        # Tier 1 — real US yields
        for col_name, ticker in _YAHOO_BOND_TICKERS.items():
            s = _fetch_yahoo_yield(ticker, start, end)
            if s is not None:
                frames[col_name] = s
                print(f"[fetch_bond_yields] {col_name} ← yahoo ({len(s)} rows, "
                      f"latest {float(s.iloc[-1]):.2f}%)")
            else:
                print(f"[fetch_bond_yields] {col_name}: Yahoo failed")

        # Tier 2/3 — synthetic proxies for foreign yields
        us10y = frames.get("US_10Y")
        for col_name, cfg in _ETF_YIELD_PROXIES.items():
            s = _build_synthetic_yield(
                etf=cfg["etf"], anchor=cfg["anchor"],
                sensitivity=cfg["sensitivity"],
                us10y_series=us10y, start=start, end=end,
            )
            frames[col_name] = s

        if not frames:
            return None

        bonds = pd.DataFrame(frames)
        bonds = bonds.sort_index().asfreq("B").ffill().bfill()
        bonds = bonds.dropna(how="all")
        return _cache_set(key, bonds)
    except Exception as e:
        print(f"[fetch_bond_yields] {e}")
        return None

def fetch_commodities(period_days: int) -> Optional[pd.DataFrame]:
    key = f"comm:{period_days}"
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        end     = datetime.today()
        start   = end - timedelta(days=period_days + 50)
        tickers = list(_COMMODITY_TICKERS.values())
        names   = list(_COMMODITY_TICKERS.keys())

        raw = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
        if raw.empty:
            return None

        close_df = _normalize_columns(raw, tickers=tickers)
        data = pd.DataFrame(index=close_df.index)

        for tkr, name in zip(tickers, names):
            if tkr in close_df.columns:
                data[name] = close_df[tkr]

        data = data.asfreq("B").ffill().dropna(how="all")
        return _cache_set(key, data)
    except Exception as e:
        print(f"[fetch_commodities] {e}")
        return None

# ── Feature engineering ───────────────────────────────────────────────────────
def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["SMA_10"] = df["Close"].rolling(10).mean()
    df["SMA_50"] = df["Close"].rolling(50).mean()

    ema12         = df["Close"].ewm(span=12, adjust=False).mean()
    ema26         = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]    = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    delta  = df["Close"].diff()
    gain   = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss   = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs     = gain / loss.replace(0, np.nan)
    df["RSI"] = (100.0 - (100.0 / (1.0 + rs))).fillna(50.0)

    df["ROC_10"]  = df["Close"].pct_change(10) * 100.0
    low14, high14 = df["Low"].rolling(14).min(), df["High"].rolling(14).max()
    df["Stoch_K"] = 100.0 * (df["Close"] - low14) / (high14 - low14).replace(0.0, np.nan)

    sma20, std20    = df["Close"].rolling(20).mean(), df["Close"].rolling(20).std()
    df["BB_Upper"]  = sma20 + 2.0 * std20
    df["BB_Lower"]  = sma20 - 2.0 * std20

    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift(1)).abs(),
        (df["Low"]  - df["Close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    direction     = np.sign(df["Close"].diff()).fillna(0.0)
    obv           = (direction * df["Volume"]).cumsum()
    obv_std       = obv.rolling(20).std().replace(0.0, np.nan)
    df["OBV_norm"] = (obv - obv.rolling(20).mean()) / obv_std

    d_vol         = (df["High"] - df["Low"]).diff()
    g_vol         = d_vol.where(d_vol > 0, 0.0).rolling(14).mean()
    l_vol         = (-d_vol.where(d_vol < 0, 0.0)).rolling(14).mean()
    df["RVI"]     = 100.0 - (100.0 / (1.0 + (g_vol / l_vol.replace(0, np.nan))))

    return df

def add_quant_features(
    df: pd.DataFrame,
    market_df: pd.DataFrame,
    bond_df: Optional[pd.DataFrame] = None,
    comm_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    df        = df.copy()
    mkt_close = market_df["Close"].reindex(df.index, method="ffill")
    stock_ret = np.log(df["Close"] / df["Close"].shift(1))
    mkt_ret   = np.log(mkt_close  / mkt_close.shift(1))
    df["Mkt_Return"] = mkt_ret

    WINDOW = 60
    betas  = np.full(len(df), np.nan)
    alphas = np.full(len(df), np.nan)
    sr, mr = stock_ret.values, mkt_ret.values

    for i in range(WINDOW, len(df)):
        y, x = sr[i - WINDOW:i], mr[i - WINDOW:i]
        mask  = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() > 20:
            xf, yf = x[mask], y[mask]
            cov    = np.cov(xf, yf)[0, 1]
            var    = np.var(xf)
            if var > 1e-9:
                beta       = cov / var
                betas[i]   = beta
                alphas[i]  = (yf.mean() - beta * xf.mean()) * 252

    df["Beta_60"]       = betas
    df["Alpha_60"]      = alphas
    df["Momentum_12_1"] = (df["Close"].pct_change(252) - df["Close"].pct_change(21)) * 100.0
    df["Sharpe_60"]     = (
        stock_ret.rolling(WINDOW).mean()
        / stock_ret.rolling(WINDOW).std().replace(0, np.nan)
    ) * np.sqrt(252)
    df["Vol_Ratio"] = (
        stock_ret.rolling(10).std()
        / stock_ret.rolling(WINDOW).std().replace(0, np.nan)
    )

    # ── Bond yields ──────────────────────────────────────────────────────────
    # fetch_bond_yields returns columns named US_5Y / US_10Y (matching _STOOQ_SYMBOLS keys).
    # FEATURE_COLS expects Bond_5Y / Bond_10Y, so we rename on the fly.
    _BOND_COL_MAP = {"US_5Y": "Bond_5Y", "US_10Y": "Bond_10Y"}
    if bond_df is not None and not bond_df.empty:
        aligned_bonds = bond_df.reindex(df.index, method="ffill")
        for src_col, dst_col in _BOND_COL_MAP.items():
            df[dst_col] = aligned_bonds[src_col] if src_col in aligned_bonds.columns else np.nan
    else:
        df["Bond_5Y"]  = np.nan
        df["Bond_10Y"] = np.nan

    # ── Commodities ───────────────────────────────────────────────────────────
    if comm_df is not None and not comm_df.empty:
        aligned_comm = comm_df.reindex(df.index, method="ffill")
        for col in list(_COMMODITY_TICKERS.keys()):
            df[col] = aligned_comm[col] if col in aligned_comm.columns else np.nan
    else:
        for col in list(_COMMODITY_TICKERS.keys()):
            df[col] = np.nan

    spy_sma = mkt_close.rolling(252).mean().replace(0, np.nan)
    df["Buffett_Proxy"] = (mkt_close / spy_sma) * 100.0

    return df

# ── Forecasting logic ─────────────────────────────────────────────────────────
def _holt_forecast(series: np.ndarray, alpha: float = 0.3, beta: float = 0.1, steps: int = 30):
    """Holt's Linear (Double) Exponential Smoothing."""
    s = series[~np.isnan(series)]
    if len(s) < 5:
        val = s[-1] if len(s) else 0.0
        return np.full(steps, val), np.zeros(steps)

    level, trend = float(s[0]), float(s[1] - s[0])
    for t in range(1, len(s)):
        last_l = level
        level  = alpha * s[t] + (1 - alpha) * (level + trend)
        trend  = beta  * (level - last_l) + (1 - beta) * trend

    fcast          = level + np.arange(1, steps + 1) * trend
    residue_sigma  = np.std(np.diff(s))
    bands          = residue_sigma * np.sqrt(np.arange(1, steps + 1))
    return fcast, bands

def forecast_commodity_prices(period_days: int = 730, forecast_days: int = 10) -> dict:
    key = f"comm_fcst:{period_days}:{forecast_days}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    results: dict = {}
    for name, ticker in _COMMODITY_TICKERS.items():
        try:
            raw = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
            if raw.empty:
                continue
            raw    = _normalize_columns(raw)
            prices = raw["Close"].dropna().values
            means, sigma = _holt_forecast(prices, steps=forecast_days)
            results[name] = {
                "last_price":     float(prices[-1]),
                "means":          means.tolist(),
                "upper":          (means + sigma).tolist(),
                "lower":          (means - sigma).tolist(),
                "pct_change_1d":  round(((means[0] - prices[-1]) / prices[-1]) * 100, 2),
                "dates": [
                    str((datetime.today() + timedelta(days=i)).date())
                    for i in range(1, forecast_days + 1)
                ],
                "alpha": 0.3,
                "beta":  0.1,
            }
        except Exception as e:
            print(f"[forecast_commodity_prices] {name}: {e}")

    return _cache_set(key, results)

def forecast_gdp_growth(period_days: int = 730, forecast_days: int = 30) -> dict:
    """
    Uses annualised 252-day ETF return as a GDP growth proxy, then applies
    Holt smoothing to produce a forecast with ±1σ bands.
    Falls back to consensus estimates when ETF data is unavailable.
    """
    consensus = {
        "US": 2.5, "India": 6.8, "China": 4.8,
        "EU": 1.2, "Japan": 1.0, "UK": 0.8, "Brazil": 2.2,
    }
    results: dict = {}

    for country, etf in _GDP_ETFS.items():
        base_rate = consensus[country]
        try:
            end   = datetime.today()
            start = end - timedelta(days=period_days + 50)
            raw   = yf.download(etf, start=start, end=end, progress=False, auto_adjust=True)
            if raw.empty:
                raise ValueError("empty")
            raw    = _normalize_columns(raw)
            prices = raw["Close"].dropna()

            # Compute rolling 252-day annualised return as GDP proxy
            annual_ret = (prices / prices.shift(252) - 1) * 100.0
            annual_ret = annual_ret.dropna()

            if len(annual_ret) < 30:
                raise ValueError("insufficient return history")

            current_pct = float(annual_ret.iloc[-1])
            fcst, sigma = _holt_forecast(annual_ret.values, steps=forecast_days)

            results[country] = {
                "current_annual_pct": current_pct,
                "forecast_pct":       fcst.tolist(),
                "upper_pct":          (fcst + sigma).tolist(),
                "lower_pct":          (fcst - sigma).tolist(),
                "source":             f"{etf} ETF Proxy",
            }
        except Exception:
            # Graceful fallback to consensus
            drift = np.linspace(base_rate, base_rate + np.random.uniform(-0.2, 0.2), forecast_days)
            results[country] = {
                "current_annual_pct": base_rate,
                "forecast_pct":       drift.tolist(),
                "upper_pct":          (drift + 0.3).tolist(),
                "lower_pct":          (drift - 0.3).tolist(),
                "source":             "Consensus Estimate",
            }

    return results

def compute_macro_correlations(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Close", "Bond_10Y", "Gold", "Brent_Oil",
        "Buffett_Proxy", "RSI", "Beta_60", "MACD",
        "Silver", "Copper",
    ]
    available = [c for c in cols if c in df.columns]
    if len(available) < 2:
        return pd.DataFrame()
    corr = df[available].dropna().corr()[["Close"]].drop("Close")
    corr.columns = ["correlation"]
    return corr.sort_values("correlation", ascending=False)

# ── ML helpers ────────────────────────────────────────────────────────────────
def build_sequences(scaled_data: np.ndarray, raw_close: np.ndarray, seq_length: int):
    """Predict log-returns — more stationary than raw prices."""
    log_returns = np.log(raw_close[1:] / np.where(raw_close[:-1] == 0, 1e-9, raw_close[:-1]))
    X, y = [], []
    for i in range(seq_length, len(scaled_data)):
        X.append(scaled_data[i - seq_length:i])
        y.append(log_returns[i - 1])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

def split_data(X, y, train_ratio: float = 0.7, val_ratio: float = 0.15):
    n         = len(X)
    train_end = int(n * train_ratio)
    val_end   = int(n * (train_ratio + val_ratio))
    return (
        (X[:train_end],   y[:train_end]),
        (X[train_end:val_end], y[train_end:val_end]),
        (X[val_end:],     y[val_end:]),
        val_end,
        train_end,
    )

def returns_to_prices(log_returns: np.ndarray, start_price: float) -> np.ndarray:
    """Convert log-return sequence back to a price series."""
    prices = np.empty(len(log_returns))
    price  = start_price
    for i, r in enumerate(log_returns):
        price     = price * np.exp(r)
        prices[i] = price
    return prices
