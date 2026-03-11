"""
data_fetch.py — price & news data retrieval with robust retry logic
"""
import time
import os
import yfinance as yf
import pandas as pd
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("keys.env")

_newsapi: NewsApiClient | None = None


def _get_newsapi() -> NewsApiClient:
    global _newsapi
    if _newsapi is None:
        key = os.getenv("NEWSAPI_KEY")
        if not key:
            raise EnvironmentError("NEWSAPI_KEY not set in keys.env")
        _newsapi = NewsApiClient(api_key=key)
    return _newsapi


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten columns, normalise index, drop NaN closes."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df.dropna(subset=["Close"])


def fetch_price_data(ticker: str = "AAPL", period: str = "10y") -> pd.DataFrame:
    """
    Fetch OHLCV data with aggressive retry + two download strategies.

    Strategy A: yf.download()         — fast, sometimes rate-limited
    Strategy B: yf.Ticker().history() — separate session, often bypasses limits

    Waits: 5s, 15s, 30s for strategy A then 10s, 20s for strategy B.
    """
    last_err = None

    # ── Strategy A: yf.download with exponential backoff ─────────────────────
    for attempt, wait in enumerate([5, 15, 30]):
        try:
            df = yf.download(ticker, period=period, progress=False,
                             auto_adjust=True, threads=False)
            if not df.empty:
                return _clean_df(df)
        except Exception as e:
            last_err = e
        print(f"yfinance download attempt {attempt + 1} failed — waiting {wait}s…")
        time.sleep(wait)

    # ── Strategy B: Ticker.history() uses a different internal session ────────
    print("Switching to Ticker.history() fallback…")
    for attempt, wait in enumerate([10, 20]):
        try:
            df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
            if not df.empty:
                return _clean_df(df)
        except Exception as e:
            last_err = e
        print(f"Ticker.history attempt {attempt + 1} failed — waiting {wait}s…")
        time.sleep(wait)

    raise ValueError(
        f"Could not fetch data for '{ticker}' after 5 attempts. "
        f"Yahoo Finance is rate-limiting — wait 1-2 minutes and try again. "
        f"Last error: {last_err}"
    )


def fetch_news(ticker: str = "AAPL", days: int = 14) -> list[dict]:
    """Fetch recent news with 3-tier fallback."""
    newsapi   = _get_newsapi()
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    def _query(sources, q):
        kwargs = dict(
            q=q,
            from_param=from_date,      # keyword arg — avoids positional deprecation warning
            language="en",
            sort_by="relevancy",
            page_size=10,
        )
        if sources:
            kwargs["sources"] = sources
        resp = newsapi.get_everything(**kwargs)
        return resp.get("articles", [])

    # Tier 1: WSJ only
    articles = _query("the-wall-street-journal", ticker)
    # Tier 2: Major financial sources
    if not articles:
        articles = _query(
            "bloomberg,reuters,financial-times,the-wall-street-journal",
            f"{ticker} stock"
        )
    # Tier 3: Any source
    if not articles:
        articles = _query(None, f"{ticker} stock market")

    return articles