# 📈 Ticker-Teller

**Ensemble stock price forecasting — LSTM time-series × LLM news sentiment**

Ticker-Teller predicts the next trading day's closing price for any stock ticker by combining a multi-feature LSTM neural network with real-time news sentiment scored by a large language model. The two signals are blended through a Ridge Regression meta-learner trained on held-out validation data.

---

## Features

- **Multi-feature LSTM** — trained on 6 technical inputs: close price, volume, 10-day ROC, RSI-14, SMA-20 ratio, and 10-day volatility
- **LLM sentiment scoring** — Groq (`llama-3.3-70b-versatile`) analyses recent news headlines and returns structured bullish/bearish scores with source credibility and recency weighting (ImpactScore)
- **Ensemble meta-learner** — Ridge Regression combines LSTM predictions with momentum and volatility features; falls back to a weighted multiplier when insufficient validation data exists
- **80 / 10 / 10 chronological split** — strict train/val/test separation with no data leakage; early stopping on validation loss with best-weights restoration
- **Interactive Streamlit dashboard** — price history chart, test-set backtest, training loss curves, sentiment gauge, and per-article evidence cards
- **Robust data fetching** — two-strategy Yahoo Finance fallback with exponential backoff (up to 80s retry window)

---

## Project Structure

```
ticker-teller/
├── app.py                  # Streamlit entry point, UI layout, and orchestration
├── keys.env                # API keys (not committed — see Setup)
├── src/
│   ├── data_fetch.py       # yfinance price data + NewsAPI article retrieval
│   ├── lstm_predictor.py   # Feature engineering, LSTM model, training, inference
│   ├── llm_sentiment.py    # Groq LLM sentiment scoring and evidence extraction
│   ├── ensemble.py         # ImpactScore, meta-learner training, ensemble blending
│   └── visualization.py    # All Plotly charts and Streamlit dashboard rendering
└── models/                 # Saved LSTM weights, scalers, and splits (auto-created)
    ├── {TICKER}_lstm.pth
    ├── {TICKER}_scalers.pkl
    ├── {TICKER}_splits.pkl
    └── {TICKER}_meta.pkl
```

---

## Requirements

- Python 3.10+
- A [Groq API key](https://console.groq.com/) (free tier available)
- A [NewsAPI key](https://newsapi.org/) (free tier: 100 requests/day)

---

## Setup

**1. Create `keys.env` in the project root**

```env
GROQ_API_KEY=your_groq_key_here
NEWSAPI_KEY=your_newsapi_key_here
```

> `keys.env` is loaded by `python-dotenv` at startup. Never commit this file.

**2. Run the app**

```bash
streamlit run app.py
```

---

## Dependencies

```
streamlit
yfinance
newsapi-python
groq
torch
scikit-learn
pandas
numpy
plotly
joblib
python-dotenv
```

Install all at once:

```bash
pip install streamlit yfinance newsapi-python groq torch scikit-learn pandas numpy plotly joblib python-dotenv
```

---

## How It Works

### 1. Price Data (`data_fetch.py`)
Historical OHLCV data is fetched from Yahoo Finance using `yf.download()` with a `Ticker.history()` fallback. Retries up to 5 times across two strategies to handle rate limiting.

### 2. Feature Engineering (`lstm_predictor.py`)
Six features are computed from the raw close and volume series:

| Feature | Description |
|---|---|
| Close | Raw closing price |
| Volume | Daily traded volume |
| ROC-10 | 10-day rate of change (momentum) |
| RSI-14 | Relative Strength Index (overbought/oversold) |
| SMA-20 ratio | Distance from 20-day moving average (mean reversion) |
| Volatility-10 | 10-day rolling std of log returns |

Each feature is scaled with its own `MinMaxScaler` fitted **only on training data**.

### 3. LSTM Training (`lstm_predictor.py`)
A 2-layer LSTM (128 hidden units, 0.3 dropout) is trained on 60-day rolling windows to predict the next day's close. Training uses AdamW with cosine annealing LR decay and early stopping (patience=15). The best validation checkpoint is restored before inference.

Data is split **chronologically** — no shuffling across time boundaries:

```
|←────── 80% Train ──────→|←─ 10% Val ─→|←─ 10% Test ─→|
```

### 4. News Sentiment (`llm_sentiment.py`)
Up to 5 recent articles are retrieved from NewsAPI (WSJ → major financial outlets → any source, in priority order). Each article is sent individually to Groq's LLaMA model, which returns a structured JSON score from -1.0 (very bearish) to +1.0 (very bullish) with a one-sentence summary and key quote.

### 5. ImpactScore (`ensemble.py`)
Raw sentiment scores are weighted by two factors before aggregation:

- **Source credibility** — WSJ (1.0), Bloomberg/Reuters (0.95), CNBC (0.80), blogs (~0.45–0.55)
- **Recency decay** — exponential decay: `weight = exp(-age_days / (news_days / 2))`

This produces a single `impact_score ∈ [-1, 1]`.

### 6. Ensemble Blending (`ensemble.py`)
If sufficient validation data exists, a Ridge Regression meta-learner is trained on `[lstm_proxy, momentum, volatility] → actual_close` using the validation set. At inference:

```
final_price = 0.70 × meta_price + 0.30 × (lstm_price × (1 + impact × sentiment_weight))
```

If no meta-learner is available, a simpler multiplier is used:

```
final_price = lstm_price × (1 + impact × sentiment_weight)
```

The result is clipped to ±15% of the LSTM raw prediction.

---

## Sidebar Controls

| Control | Description |
|---|---|
| Ticker Symbol | Any valid Yahoo Finance ticker (e.g. `AAPL`, `TSLA`, `NVDA`) |
| Training History | Preset (1y/2y/5y/10y) or custom years + months |
| News Lookback | How many days of news to fetch (7–29) |
| Ensemble Weight | How much sentiment nudges the LSTM price (default 0.05 = ±5% max) |
| Force Retrain | Discard cached model and retrain from scratch |

---

## Dashboard Sections

- **Prediction Results** — Last close, LSTM raw forecast, ensemble forecast, and ImpactScore KPIs
- **Model Evaluation** — MAE, RMSE, MAPE, R², and best validation loss across the 80/10/10 split
- **Price History + Forecast** — Full price history with the next-day prediction projected forward, with a ±2% uncertainty band
- **Test Set Backtest** — LSTM predictions vs actual closes on the held-out 10% test period, with a ±MAE confidence band
- **Training Diagnostics** — Train/val MSE loss curves and the aggregate sentiment gauge
- **News Sentiment** — Per-article evidence cards showing score, label, summary, reasoning, and source link
- **Raw Price Data** — Filterable OHLCV table with year selector

---

## Caveats

- **Not financial advice.** This is a research and learning project. Stock prices are influenced by countless factors no model can fully capture.
- **Yahoo Finance rate limits.** If the price fetch fails, wait 1–2 minutes and retry.
- **NewsAPI free tier** is limited to articles from the past 30 days and 100 requests/day.
- Cached models are tied to a specific ticker. If the underlying data range changes significantly, tick **Force Retrain**.
