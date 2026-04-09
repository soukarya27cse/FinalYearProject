# 📈 Ticker-Teller v3.1

> **Full-stack neural stock forecasting** — FastAPI Python backend + React/Vite frontend, streaming live training progress via Server-Sent Events (SSE).

---

## Table of Contents

1. [What It Does](#1-what-it-does)
2. [Project File Structure](#2-project-file-structure)
3. [Quick Start](#3-quick-start)
4. [stock.sh — The Launcher](#4-stocksh--the-launcher)
5. [Backend — main.py](#5-backend--mainpy)
6. [Backend — src/data.py](#6-backend--srcdatapy)
7. [Backend — src/model.py](#7-backend--srcmodelpy)
8. [Frontend — App.jsx](#8-frontend--appjsx)
9. [Frontend — api.js](#9-frontend--apijs)
10. [Frontend — Sidebar.jsx](#10-frontend--sidebarjsx)
11. [Frontend — TrainingProgress.jsx](#11-frontend--trainingprogressjsx)
12. [Frontend — MetricCards.jsx](#12-frontend--metriccardsjsx)
13. [Frontend — PriceChart.jsx](#13-frontend--pricechartjsx)
14. [Frontend — LossAndMacdCharts.jsx](#14-frontend--lossandmacdchartsjsx)
15. [Frontend — CommodityPanel.jsx](#15-frontend--commoditypaneljsx)
16. [Frontend — GdpPanel.jsx](#16-frontend--gdppaneljsx)
17. [Frontend — BondPanel.jsx](#17-frontend--bondpaneljsx)
18. [Frontend — CorrelationAndAbout.jsx](#18-frontend--correlationandaboutjsx)
19. [Frontend — globals.css](#19-frontend--globalscss)
20. [The 31 Features](#20-the-31-features)
21. [Model Architecture In Depth](#21-model-architecture-in-depth)
22. [Training Pipeline](#22-training-pipeline)
23. [Monte Carlo Forecast](#23-monte-carlo-forecast)
24. [Bond Yields — Data Strategy](#24-bond-yields--data-strategy)
25. [Commodity Forecasting](#25-commodity-forecasting)
26. [GDP Proxies](#26-gdp-proxies)
27. [Mathematics Reference](#27-mathematics-reference)
28. [API Reference](#28-api-reference)
29. [Configuration Reference](#29-configuration-reference)
30. [Known Limitations and Disclaimer](#30-known-limitations-and-disclaimer)

---

## 1. What It Does

Ticker-Teller is a self-hosted, end-to-end stock analysis and forecasting system. Given any Yahoo Finance ticker symbol, it:

1. **Downloads** live OHLCV price history and syncs macro data (bonds, commodities, market index).
2. **Engineers 31 features** spanning raw price data, 12 technical indicators, and 14 quantitative/macro factors.
3. **Trains a deep hybrid neural network** (CNN → BiLSTM → Multi-Head Attention) in real time, streaming every epoch's train loss, validation loss, and learning rate to the browser via SSE.
4. **Forecasts** future prices using 80-sample Monte Carlo Dropout, producing calibrated ±1σ uncertainty bands.
5. **Presents** a rich interactive dashboard: price chart with Bollinger Bands, RSI, volume, MACD, training loss curve, feature correlations, global bond yields, commodity forecasts, and GDP proxies.

Everything runs locally. No cloud service, no API key required for core functionality.

---

## 2. Project File Structure

```
ticker-teller/
│
├── stock.sh                        # One-command launcher script
│
├── backend/
│   ├── main.py                     # FastAPI app — all endpoints + SSE streaming
│   ├── requirements.txt            # Python dependencies
│   └── src/
│       ├── __init__.py             # Package marker (version string)
│       ├── data.py                 # Data fetching, feature engineering, forecasting helpers
│       └── model.py                # PyTorch model definition, training loop, MC inference
│
└── frontend/
    ├── index.html                  # Single HTML entry point (loads /src/main.jsx)
    ├── package.json                # Node dependencies and npm scripts
    ├── vite.config.js              # Vite dev server config + /api proxy
    └── src/
        ├── main.jsx                # React DOM entry point
        ├── App.jsx                 # Root component — all state, SSE handling, routing
        ├── api.js                  # Frontend HTTP/SSE client functions
        ├── styles/
        │   └── globals.css         # All CSS: design tokens, layout, every component style
        └── components/
            ├── Sidebar.jsx                 # Left panel: ticker input + all config sliders
            ├── TrainingProgress.jsx        # Live epoch progress bar + sparkline
            ├── MetricCards.jsx             # KPI summary cards (price, forecast, MAE, etc.)
            ├── PriceChart.jsx              # Main chart: price, BB, RSI, volume, forecast
            ├── LossAndMacdCharts.jsx       # Training loss curve + MACD oscillator chart
            ├── CommodityPanel.jsx          # Commodity prices + Holt-Winters forecast
            ├── GdpPanel.jsx                # Country GDP proxies + 30-day forecast
            ├── BondPanel.jsx               # Global bond yields + US yield-curve spread
            └── CorrelationAndAbout.jsx     # Feature correlation chart + About modal
```

---

## 3. Quick Start

### Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

### First-time setup (recommended)

```bash
chmod +x stock.sh
./stock.sh deps      # Creates Python venv, installs all Python + Node packages
./stock.sh install   # (Optional) installs 'stock' as a global shell command
```

### Start the application

```bash
./stock.sh           # Starts backend (port 8000) + frontend (port 5173), opens browser
# OR, if installed globally:
stock
```

### Manual start (without stock.sh)

```bash
# Terminal 1 — Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.
Swagger API docs: **http://localhost:8000/docs**

### Example ticker symbols

| Symbol | Exchange |
|--------|----------|
| `AAPL`, `TSLA`, `NVDA`, `MSFT`, `GOOGL` | NASDAQ / NYSE |
| `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `HDFCBANK.NS` | NSE India |
| `HSBA.L`, `BP.L`, `GSK.L` | London Stock Exchange |
| `^NSEI`, `^GSPC`, `^DJI`, `^FTSE` | Indices |
| `BTC-USD`, `ETH-USD` | Crypto |
| `GC=F`, `CL=F` | Commodities (futures) |

---

## 4. stock.sh — The Launcher

`stock.sh` is a self-contained Bash script that manages the full lifecycle of both services. It auto-detects the project root by looking for sibling `backend/` and `frontend/` directories.

### Commands

| Command | What it does |
|---------|-------------|
| `./stock.sh` | Starts backend + frontend, waits for both ports, opens browser |
| `./stock.sh restart` | Kills ports 8000/5173/5174, then starts fresh |
| `./stock.sh stop` | Kills all services cleanly |
| `./stock.sh deps` | Creates Python venv, installs `requirements.txt`, runs `npm ci` or `npm install` |
| `./stock.sh backend` | Starts backend only |
| `./stock.sh frontend` | Starts frontend only |
| `./stock.sh install` | Symlinks `stock.sh` to `/usr/local/bin/stock` for global use |
| `./stock.sh uninstall` | Removes the `/usr/local/bin/stock` symlink |
| `./stock.sh --help` | Prints full usage |

### How it works internally

- Uses `lsof` / `ss` to check if ports are already in use before starting.
- Polls ports with `wait_for_port` (every 0.5s, 30s timeout) to confirm each service is up before printing the success banner.
- Registers `trap cleanup EXIT INT TERM` so Ctrl+C always kills both child processes cleanly.
- Writes uvicorn output to `.backend.log` and Vite output to `.frontend.log` in the project root.
- Attempts `xdg-open` (Linux) or `open` (macOS) to auto-launch the browser.

---

## 5. Backend — `main.py`

The FastAPI application, running on **port 8000**. All blocking CPU/IO work runs inside a `ThreadPoolExecutor` (10 workers) so the async event loop is never blocked.

### CORS

Allows origins: `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:5174`, `http://127.0.0.1:5174`.

### Helper functions

| Function | Purpose |
|----------|---------|
| `_json(obj)` | JSON serialiser with encoder for `np.integer`, `np.floating`, `np.ndarray`, `pd.Timestamp` |
| `_sse(event_type, data)` | Formats a dict as an SSE frame: `data: {"type": "...", ...}\n\n` |
| `_currency(ticker)` | Returns `₹`, `£`, `HK$`, `€`, or `$` from ticker suffix |
| `_signal_badge(signal)` | Maps `"BUY"` → `"bull"`, `"SELL"` → `"bear"`, else `"neutral"` |

### Request schema — `AnalyzeConfig`

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `ticker` | str | `"AAPL"` | 1–20 chars | Yahoo Finance symbol |
| `period` | int | `730` | 180–1825 | Calendar days of price history to download |
| `seq_length` | int | `60` | 10–120 | Past trading days the model sees per prediction |
| `forecast_days` | int | `5` | 1–30 | Future business days to forecast |
| `epochs` | int | `50` | 5–200 | Maximum training epochs |
| `patience` | int | `10` | 3–30 | Early-stopping patience |
| `hidden_size` | int | `128` | — | BiLSTM hidden units per direction |
| `cnn_channels` | int | `64` | — | CNN output channels |
| `num_heads` | int | `4` | — | Attention heads |
| `dropout` | float | `0.2` | 0.0–0.5 | Dropout rate (also controls MC uncertainty width) |

### `/api/analyze` — POST (SSE stream)

Runs the entire pipeline in a thread, pushing events into an `asyncio.Queue` drained by an async generator.

**Full pipeline:**

1. Validate ticker, determine currency symbol.
2. `fetch_data` — download OHLCV history.
3. `fetch_market_data`, `fetch_bond_yields`, `fetch_commodities` — sync macro data.
4. `add_technical_features` + `add_quant_features` — build the 31-feature DataFrame.
5. Fill missing columns with `0.0`, forward-fill, drop NaN rows.
6. `MinMaxScaler` fit + transform to `[0, 1]`.
7. `build_sequences` — create overlapping windows; targets = log-returns.
8. `split_data` — 70% train / 15% val / 15% test (chronological).
9. `make_loaders` — wrap in PyTorch `DataLoader` objects.
10. `train_model` — train with epoch callbacks that push SSE `epoch` events.
11. `predict_test_set` — run inference on held-out test set.
12. Reconstruct actual and predicted price series (cumulative for metrics; per-step-anchored for chart display).
13. `monte_carlo_forecast` — 80-sample MC dropout, `forecast_days` steps ahead.
14. Build `hist_rows` (historical chart data with BB/RSI/MACD/volume).
15. Push final SSE `result` event with full payload.

**SSE event types:**

| `type` | Additional fields | When emitted |
|--------|------------------|--------------|
| `status` | `message: str` | Before each pipeline stage |
| `epoch` | `epoch, total, train_loss, val_loss, lr` | After every training epoch |
| `result` | Full result object (see below) | Training complete |
| `error` | `message: str, traceback: str` | Any unhandled exception |

**Result object structure:**

```json
{
  "ticker":   "AAPL",
  "currency": "$",
  "device":   "cpu",
  "features": { "total": 31, "price": 17, "macro": 14 },
  "splits":   { "n_train": 780, "n_val": 168, "n_test": 111 },
  "model":    { "total_params": 385346, "trainable_params": 385346 },
  "summary": {
    "last_price": 213.49,
    "next_price": 218.10,
    "pct_change": 2.16,
    "volatility": 0.28,
    "signal":     "BUY",
    "badge":      "bull"
  },
  "metrics": {
    "mae":  4.21,
    "rmse": 5.88,
    "mape": 1.94,
    "directional_accuracy": 54.1
  },
  "charts": {
    "historical": [
      { "date": "2024-01-15", "close": 185.92, "bb_upper": 191.3,
        "bb_lower": 179.1, "rsi": 58.4, "macd": 0.412,
        "macd_sig": 0.388, "volume": 54200000 }
    ],
    "test":     [{ "date": "2024-11-01", "actual": 222.50, "predicted": 219.80 }],
    "forecast": [{ "date": "2025-04-01", "mean": 218.10, "upper": 221.40, "lower": 214.80 }],
    "loss":     [{ "epoch": 1, "train": 0.000412, "val": 0.000531 }],
    "correlations": [{ "feature": "Bond_10Y", "correlation": -0.412 }]
  }
}
```

### `/api/bonds` — GET

Query params: `period` (int, default 730).

```json
{
  "rows": [{ "date": "2024-02-01", "US_5Y": 4.07, "US_10Y": 4.44, "India_10Y": 6.81 }],
  "columns": ["US_5Y", "US_10Y", "India_10Y", "Germany_10Y", "UK_10Y", "Japan_10Y"],
  "latest": { "US_5Y": 4.07, "US_10Y": 4.44, "spread": 0.37, "inverted": false },
  "countries": {
    "United States": { "5Y": 4.07, "10Y": 4.44 },
    "India":         { "10Y": 6.81 },
    "Germany":       { "10Y": 2.45 },
    "UK":            { "10Y": 4.40 },
    "Japan":         { "10Y": 1.10 }
  }
}
```

### `/api/commodities` — GET

Query params: `period` (default 730), `forecast_days` (default 10). Returns prices, Holt-Winters forecasts, and last 90 sessions of history per commodity.

### `/api/gdp` — GET

Query params: `period` (default 730), `forecast_days` (default 30). Returns ETF-derived GDP proxies and 30-day forward forecasts per country.

### `/api/ticker-info` — GET

Query param: `ticker` (required). Returns `{ name, sector, industry, currency }`.

### `/api/health` — GET

Returns `{ status, version, device, features }`.

---

## 6. Backend — `src/data.py`

### Feature column registries

```python
PRICE_FEATURE_COLS  = 17 columns   # OHLCV + technical indicators
FACTOR_FEATURE_COLS = 14 columns   # quant/macro factors
FEATURE_COLS        = 31 total     # PRICE + FACTOR (order matters for model input)
CLOSE_IDX           = 3            # index of "Close" in PRICE_FEATURE_COLS
```

### In-memory cache

All fetch functions share `_CACHE: dict[str, tuple[float, object]]` with TTL of 3600 seconds. Lookups always use explicit `is not None` checks — never a bare `if cached:` on a DataFrame, which would raise pandas' ambiguous truth value error.

### `_normalize_columns(df, tickers=None)`

Handles yfinance's inconsistent column structure across versions and download modes:
- **Flat columns:** renames `Adj Close` → `Close` if needed.
- **MultiIndex with `tickers` provided:** extracts the `Close` field, returning a DataFrame with ticker symbols as columns.
- **MultiIndex without `tickers`:** flattens to level-0 field names (single-ticker download on newer yfinance).

### Data fetching functions

**`fetch_data(ticker, period_days)`** — Downloads `period_days + 100` days of OHLCV (extra days ensure the business-day resampling has enough history). Normalises columns, selects `Open/High/Low/Close/Volume`, resamples to `asfreq("B")`, forward-fills gaps.

**`fetch_market_data(period_days, ticker="SPY")`** — Downloads SPY as the market benchmark. Requests `period_days + 400` extra days to ensure sufficient overlap for the 60-day Beta/Alpha rolling window.

**`fetch_bond_yields(period_days)`** — 3-tier strategy (see [Section 24](#24-bond-yields--data-strategy)).

**`fetch_commodities(period_days)`** — Downloads all 5 commodity futures in a single `yf.download` call. Normalises the MultiIndex, maps Yahoo tickers back to human-readable names.

| Name | Yahoo Ticker |
|------|-------------|
| Gold | GC=F |
| Silver | SI=F |
| Copper | HG=F |
| Aluminium | ALI=F |
| Brent Oil | BZ=F |

### Feature engineering

**`add_technical_features(df)`** — Computes 12 indicators in-place:

| Feature | Computation |
|---------|------------|
| `SMA_10` | Rolling 10-day simple moving average of Close |
| `SMA_50` | Rolling 50-day simple moving average of Close |
| `MACD` | EMA(12) − EMA(26) of Close |
| `MACD_Signal` | EMA(9) of MACD |
| `RSI` | 14-period: 100 − 100/(1 + avg_gain/avg_loss); NaN → 50 |
| `ROC_10` | (Close / Close_10d_ago − 1) × 100 |
| `Stoch_K` | 100 × (Close − Low_14) / (High_14 − Low_14) |
| `BB_Upper` | SMA_20 + 2 × StdDev_20 |
| `BB_Lower` | SMA_20 − 2 × StdDev_20 |
| `ATR` | Rolling 14-period mean of True Range |
| `OBV_norm` | On-Balance Volume, 20-period z-score normalised |
| `RVI` | RSI applied to the High−Low range (not to Close) |

**`add_quant_features(df, market_df, bond_df, comm_df)`** — Adds 14 macro/quant features:

| Feature | Computation |
|---------|------------|
| `Mkt_Return` | Daily log-return of SPY, index-aligned to stock |
| `Beta_60` | 60-day rolling OLS Beta: Cov(stock, mkt) / Var(mkt) |
| `Alpha_60` | 60-day rolling Jensen's Alpha × 252 (annualised) |
| `Momentum_12_1` | pct_change(252) − pct_change(21), × 100 |
| `Sharpe_60` | Mean log-return / Std × √252, 60-day rolling |
| `Vol_Ratio` | StdDev_10 / StdDev_60 |
| `Bond_5Y` | US 5Y yield (remapped from `US_5Y` in bond_df) |
| `Bond_10Y` | US 10Y yield (remapped from `US_10Y` in bond_df) |
| `Gold` | Gold futures close, aligned to stock index |
| `Silver` | Silver futures close |
| `Copper` | Copper futures close |
| `Aluminium` | Aluminium futures close |
| `Brent_Oil` | Brent crude close |
| `Buffett_Proxy` | SPY / SMA_252(SPY) × 100 |

Beta and Alpha use a manual rolling loop with NaN masking (minimum 20 valid observations per window).

### Sequence building and splitting

**`build_sequences(scaled_data, raw_close, seq_length)`**

```
X[i] = scaled_data[i - seq_length : i]     shape: (seq_length, 31)
y[i] = log(raw_close[i] / raw_close[i-1])  scalar log-return
```

**`split_data(X, y)`** — Chronological 70/15/15 split. No shuffling (would cause data leakage).

**`returns_to_prices(log_returns, start_price)`** — Cumulative compounding: `price[i] = price[i-1] × exp(r[i])`.

### Forecasting helpers

**`_holt_forecast(series, alpha=0.3, beta=0.1, steps)`** — Holt's Linear (Double) Exponential Smoothing. See [Section 27](#27-mathematics-reference) for formulae.

**`forecast_commodity_prices(period_days, forecast_days)`** — Applies Holt smoothing to each commodity's 2-year price history. Returns `means`, `upper`, `lower`, `pct_change_1d`, `dates`, `alpha`, `beta` per commodity.

**`forecast_gdp_growth(period_days, forecast_days)`** — For each of 7 countries, downloads the country ETF, computes the rolling 252-day annualised return as a GDP proxy, applies Holt smoothing. Falls back to consensus estimates if ETF history is too short.

**`compute_macro_correlations(df)`** — Pearson correlations between Close and: `Bond_10Y`, `Gold`, `Brent_Oil`, `Buffett_Proxy`, `RSI`, `Beta_60`, `MACD`, `Silver`, `Copper`. Sorted descending.

---

## 7. Backend — `src/model.py`

### `StockDataset`

`torch.utils.data.Dataset` wrapper converting numpy arrays to `float32` tensors. Targets shaped `(-1, 1)`.

### `make_loaders(..., batch_size=32)`

Three `DataLoader` objects. `shuffle=False` (time series order must be preserved). `num_workers=0` (avoids multiprocessing conflicts inside `ThreadPoolExecutor`). `pin_memory=True` if CUDA available.

### `CombinedLoss`

```
L = Huber(δ=0.01)(ŷ, y) + 0.4 × mean(ReLU(−ŷ × y))
```

Huber is robust to large daily moves. The directional penalty is 0 when `ŷ` and `y` share the same sign, positive when they disagree — biasing the model toward correct direction calls.

### `TemporalConvBlock`

Inception-style dual-kernel 1-D CNN with residual connection:

```
Input [B, C_in, T]
  ├── Conv1d(k=3) → BN → GELU ─┐
  └── Conv1d(k=5) → BN → GELU ─┘→ cat → Conv1d(1×1) → BN → GELU → Dropout
                                                                         │
                                         + residual (1×1 Conv or Identity)
Output [B, C_out, T]
```

### `MultiHeadAttentionBlock`

```
x → MHA(Q=K=V=x) → Dropout → + x → LayerNorm → output
```

Uses `nn.MultiheadAttention` with `batch_first=True`. Auto-reduces `num_heads` if `hidden_size × 2` is not divisible.

### `HybridModel` — full forward pass

```
[B, SeqLen, 31]
    → permute → TemporalConvBlock → permute
    → [B, SeqLen, cnn_channels]
    → BiLSTM(layers=2, bidirectional)
    → [B, SeqLen, hidden×2]
    → MultiHeadAttentionBlock
    → [B, SeqLen, hidden×2]
    → Linear(hidden×2→1) + softmax → weighted sum (temporal pooling)
    → [B, hidden×2]
    → Dropout → Linear(hidden×2→hidden) → GELU → Dropout → Linear(hidden→1)
    → scalar (predicted log-return)
```

Default: `hidden=128` → BiLSTM output = 256 → ~385K parameters.

### `train_model(...)`

| Component | Setting |
|-----------|---------|
| Optimiser | AdamW, lr=1e-3, weight_decay=1e-4 |
| Scheduler | CosineAnnealingWarmRestarts, T₀=10, T_mult=2, η_min=1e-6 |
| Gradient clipping | max_norm=1.0 |
| Early stopping | Tracks best val_loss; restores best weights on stop |
| Epoch callback | Called after every epoch; returning `False` halts training |

### `predict_test_set(model, test_loader, device)`

Runs in `eval()` mode (dropout disabled). Returns `pred_log_returns` and `actual_log_returns` as numpy arrays.

### `monte_carlo_forecast(..., n_samples=80)`

Multi-step autoregressive MC forecast:
1. Switch to `train()` mode (dropout active).
2. For each step: run 80 forward passes → `μ = mean`, `σ = std`.
3. `next_price = cur_price × exp(μ)`, `band = cur_price × σ`.
4. Roll window forward (update Close column only; all other features stay at last known values).

### `compute_metrics(pred_prices, actual_prices)`

| Metric | Formula |
|--------|---------|
| MAE | `mean(|p − a|)` |
| RMSE | `sqrt(mean((p − a)²))` |
| MAPE | `mean(|p − a| / |a|) × 100` |
| Directional Accuracy | `sum(sign(Δp) == sign(Δa)) / (n−1) × 100` |

Both series reconstructed cumulatively from the same start price for a fair comparison.

---

## 8. Frontend — `App.jsx`

Root React component. Manages all global state and the SSE connection lifecycle.

### Key state

| State | Type | Description |
|-------|------|-------------|
| `config` | object | Mirrors `AnalyzeConfig` — all sidebar settings |
| `running` | bool | True while SSE stream is active |
| `result` | object | Final result event payload |
| `error` | string | Error message |
| `statusMsgs` | string[] | Accumulated status messages |
| `epochInfo` | object | Latest epoch event |
| `lossHistory` | number[] | All val_loss values for sparkline |
| `activeTab` | string | `'price'`, `'model'`, or `'macd'` |
| `extraView` | string | Which extra panel is open |
| `hamOpen` | bool | "More Analysis" dropdown visibility |
| `showAbout` | bool | About modal visibility |

### `handleRun`

Cancels any in-flight request. Bumps a generation counter (`runGenRef`) so stale SSE events from previous runs are discarded. Resets all result state. Calls `streamAnalyze`.

### `HamPortal`

Renders the "More Analysis" dropdown via `createPortal` on `document.body`. Uses both `anchorRef` (the ☰ button) and `menuRef` (the portal div) in the `mousedown` outside-click handler — preventing the handler from swallowing menu-item clicks before `onClick` can fire.

### Sub-components defined in App.jsx

- **`LandingView`** — shown before any run; displays feature highlights and quick-start tickers.
- **`ModelExpander`** — collapsible panel showing total params + RMSE/MAPE. Uses `overflow: visible` so card content is never clipped.
- **`TestMetricsTable`** — table inside "Model Performance" tab: MAE, RMSE, MAPE, Directional Accuracy.

---

## 9. Frontend — `api.js`

### `streamAnalyze(config, onEvent)`

POSTs directly to `http://127.0.0.1:8000/api/analyze` (bypasses Vite proxy for SSE stability). Uses the Fetch `ReadableStream` API. Parses SSE frames: splits on `\n\n`, finds `data:` lines, JSON-parses, calls `onEvent`. Returns an `AbortController`-based cancel function.

### Other functions

| Function | Endpoint |
|----------|----------|
| `fetchTickerInfo(ticker)` | GET `/api/ticker-info` |
| `fetchCommodities(period, forecastDays)` | GET `/api/commodities` |
| `fetchGdp(period, forecastDays)` | GET `/api/gdp` |
| `fetchBonds(period)` | GET `/api/bonds` |
| `fetchHealth()` | GET `/api/health` |

---

## 10. Frontend — `Sidebar.jsx`

264px wide, scrollable left panel. All controls map directly to `AnalyzeConfig` fields.

| Control | Field | Range |
|---------|-------|-------|
| Text input | `ticker` | Auto-uppercased |
| Slider | `period` | 365–1825 days |
| Slider | `seq_length` | 10–120 days |
| Slider | `forecast_days` | 1–30 days |
| Select | `hidden_size` | 32 / 64 / 128 / 256 |
| Select | `cnn_channels` | 32 / 64 / 128 |
| Select | `num_heads` | 2 / 4 / 8 |
| Slider | `dropout` | 0.0–0.5, step 0.05 |
| Slider | `epochs` | 5–200 |
| Slider | `patience` | 3–30 |

The "Model Architecture" section is collapsible. The Run button is disabled while `running` or when `ticker` is empty.

---

## 11. Frontend — `TrainingProgress.jsx`

Shown during training (when `running` is true and `result` is null).

- **Status log:** Last 3 messages; oldest at 45% opacity, newest with pulsing green dot.
- **Progress bar:** `(epoch / totalEpochs) × 100%` amber fill.
- **Epoch stats:** `EPOCH / total`, `TRAIN LOSS`, `VAL LOSS` (6 decimal places), `LR` (scientific notation).
- **Sparkline:** Last 50 val_loss values as a tiny recharts `LineChart`. Shown when > 4 points available.

---

## 12. Frontend — `MetricCards.jsx`

Five `MetricCard` components in a responsive grid after training completes.

| Card | Icon | Colour logic |
|------|------|-------------|
| Current Price | ◎ | None |
| Forecast +Nd | ◈ | Green if pct_change ≥ 0, red if < 0 |
| Directional Accuracy | ◐ | Green ≥60%, amber ≥50%, red <50% |
| MAE (Test) | ◑ | None |
| Ann. Volatility | ◒ | Green <20%, amber <40%, red ≥40% |

---

## 13. Frontend — `PriceChart.jsx`

Three vertically stacked charts sharing the same x-axis.

**Range filter:** 1M / 3M / 6M / 1Y / 2Y / ALL buttons slice the merged dataset by date.

**Data assembly:** Three sources merged on date key — `historical` (close, BB, RSI, MACD, volume), `test` (actual, predicted), `forecast` (mean, upper, lower). Sorted by date string.

**Panel 1 — Price & Bollinger Bands (270px):**
- Area fills for BB bands (purple) and forecast bands (green)
- Lines: historical (cyan), actual test (light blue), predicted test (pink dashed), MC forecast mean (green with dots)
- ReferenceLine at first forecast date

**Panel 2 — RSI (80px):**
- Area for RSI fill; reference lines at 70 (overbought) and 30 (oversold)

**Panel 3 — Volume (50px):**
- Bar chart in dark navy

---

## 14. Frontend — `LossAndMacdCharts.jsx`

**`LossChart`:** Training (cyan) and validation (purple dashed) loss curves. Amber `ReferenceLine` at the best epoch. Custom dark tooltip with 6 decimal place formatting.

**`MacdChart`:** Composed chart with MACD histogram (green/red bars at 50% opacity), MACD line (cyan), signal line (pink dashed). Derived from `charts.historical` rows where both `macd` and `macd_sig` are non-null.

---

## 15. Frontend — `CommodityPanel.jsx`

Fetches `/api/commodities` on mount.

**`CommCard`:** Name, last price, 1-day change with ▲/▼ direction and colour (green/red).

**Charts:**
1. Historical prices (last 90 sessions) — one Line per commodity.
2. Forward forecast with ±1σ bands — Area fills + Line per commodity.

**Summary table:** Commodity, Last Price, 1d Forecast, Δ%, α, β.

---

## 16. Frontend — `GdpPanel.jsx`

Fetches `/api/gdp` on mount (or accepts `inlineData` prop).

**`GdpCard`:** Country name, current annualised % (green ≥3%, amber ≥1.5%, red otherwise), 30-day delta, data source label.

**Charts:**
1. Bar chart of current annualised GDP growth % per country.
2. 30-day forward forecast with ±1σ bands per country.

**Summary table:** Country, Current %, 30-Day Forecast, Δ, Source.

---

## 17. Frontend — `BondPanel.jsx`

Fetches `/api/bonds` on mount.

**`YieldCard`:** Flag emoji, country name, 10Y yield (large, cyan), 5Y yield if available, 5Y→10Y spread with `⚠ inv.` if negative.

**US curve inversion banner:** Green for normal curve, red for inverted, with spread value and historical context message.

**Charts:**
1. Global historical yields — one Line per available country series. 5Y rendered dashed.
2. US Yield Curve Spread (10Y − 5Y) — Area chart with amber fill and inversion threshold ReferenceLine.

**Summary table:** Instrument (colour-coded), Latest Yield, Country (with flag).

---

## 18. Frontend — `CorrelationAndAbout.jsx`

**`CorrelationPanel`:** Horizontal BarChart (layout="vertical") with Pearson correlations. Bars coloured by strength: strong positive → green, strong negative → red, weak → grey. Domain `[-1, 1]`. Summary table below with strength labels (Very strong / Strong / Moderate / Weak / Negligible) and direction.

**`AboutModal`:** Fixed overlay with backdrop blur. Contains app version, feature list, model architecture, loss function, training strategy, and a red disclaimer box. Closes on outside click or ✕ button.

---

## 19. Frontend — `globals.css`

All CSS in one file using CSS custom properties throughout.

### Core design tokens

```css
/* Backgrounds */
--bg:          #0b0e14   /* page */
--bg-surface:  #0f1420   /* sidebar, panels */
--bg-card:     #141927   /* metric cards */
--bg-card-alt: #111722   /* expander background (darker than card) */
--bg-raised:   #1a2236   /* hover states */

/* Accent colours */
--amber:   #fbb03b   /* primary accent */
--cyan:    #38bdf8   /* historical price, train loss */
--green:   #4ade80   /* positive, forecast */
--red:     #f87171   /* negative, errors */
--purple:  #a78bfa   /* val loss, model controls */
--pink:    #f472b6   /* predicted test, signal line */

/* Typography */
--font-display: 'Instrument Serif'   /* italic headings */
--font-heading: 'Space Grotesk'      /* buttons, values */
--font-mono:    'IBM Plex Mono'      /* labels, tables, axes */
```

### Layout

`.app-shell` — `display: flex; height: 100vh; overflow: hidden`. Sidebar is fixed at 264px. `.main-content` fills the remainder with `overflow-y: auto; padding: 1.5rem`.

### Notable rules

- **Dot-grid background:** `body::before` with `radial-gradient` at 28px grid, 4% amber opacity.
- **Custom scrollbar:** 4px wide, amber on hover.
- **`.expander`:** `overflow: visible` + `expandFadeIn` (opacity only) — ensures metric cards are never clipped by the container.
- **`.ham-menu`:** Positioned via JS-computed `top`/`right`. z-index 9999.
- **Responsive breakpoints:** 1200px, 900px, 640px — progressively collapse grid columns.

---

## 20. The 31 Features

### Price / Technical (17)

| # | Feature | Window | Description |
|---|---------|--------|-------------|
| 1 | Open | — | Opening price |
| 2 | High | — | Session high |
| 3 | Low | — | Session low |
| 4 | Close | — | Closing price |
| 5 | Volume | — | Shares/contracts traded |
| 6 | SMA_10 | 10d | Simple moving average |
| 7 | SMA_50 | 50d | Simple moving average |
| 8 | MACD | 12/26 EMA | EMA(12) − EMA(26) |
| 9 | MACD_Signal | 9 EMA | EMA(9) of MACD |
| 10 | RSI | 14d | Relative Strength Index |
| 11 | ROC_10 | 10d | Rate of change % |
| 12 | Stoch_K | 14d | Stochastic oscillator %K |
| 13 | BB_Upper | 20d | SMA_20 + 2σ |
| 14 | BB_Lower | 20d | SMA_20 − 2σ |
| 15 | ATR | 14d | Average True Range |
| 16 | OBV_norm | 20d | On-Balance Volume z-score |
| 17 | RVI | 14d | Relative Volatility Index |

### Quantitative / Macro (14)

| # | Feature | Window | Description |
|---|---------|--------|-------------|
| 18 | Beta_60 | 60d | CAPM Beta vs SPY |
| 19 | Alpha_60 | 60d | Jensen's Alpha (annualised) |
| 20 | Momentum_12_1 | 252/21d | 12-month minus 1-month momentum |
| 21 | Sharpe_60 | 60d | Annualised Sharpe ratio |
| 22 | Vol_Ratio | 10/60d | Short/long volatility ratio |
| 23 | Mkt_Return | — | Daily SPY log-return |
| 24 | Bond_5Y | — | US 5Y Treasury yield (^FVX) |
| 25 | Bond_10Y | — | US 10Y Treasury yield (^TNX) |
| 26 | Gold | — | Gold futures (GC=F) |
| 27 | Silver | — | Silver futures (SI=F) |
| 28 | Copper | — | Copper futures (HG=F) |
| 29 | Aluminium | — | Aluminium futures (ALI=F) |
| 30 | Brent_Oil | — | Brent crude futures (BZ=F) |
| 31 | Buffett_Proxy | 252d | SPY / SMA_252(SPY) × 100 |

---

## 21. Model Architecture In Depth

```
Input: [Batch × SeqLen × 31]
         │
         ▼ permute to [B × 31 × SeqLen]
┌─────────────────────────────────────┐
│         TemporalConvBlock           │
│  Conv1d(k=3, pad=1) → BN → GELU ─┐ │
│  Conv1d(k=5, pad=2) → BN → GELU ─┘ │→ concat channels
│  Conv1d(1×1)        → BN → GELU     │
│  + Residual (1×1 conv or Identity)  │
│  + Dropout                          │
└─────────────────────────────────────┘
         │ permute to [B × SeqLen × cnn_channels]
         ▼
┌─────────────────────────────────────┐
│   Bidirectional LSTM (2 layers)     │
│   Input:  cnn_channels              │
│   Hidden: H (per direction)         │
│   Output: [B × SeqLen × H×2]       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   MultiHeadAttentionBlock           │
│   MHA(Q=K=V) → Dropout             │
│   + Residual → LayerNorm           │
│   Output: [B × SeqLen × H×2]       │
└─────────────────────────────────────┘
         │
         ▼ Temporal Weighted Pooling
   Linear(H×2 → 1) → softmax over SeqLen
   → weighted sum → [B × H×2]
         │
         ▼
┌─────────────────────────────────────┐
│   MLP Head                          │
│   Dropout(p) → Linear(H×2 → H)     │
│   → GELU → Dropout(p/2)            │
│   → Linear(H → 1)                  │
└─────────────────────────────────────┘
         │
         ▼
   Scalar: predicted log-return
```

Default config (`H=128`): BiLSTM output = 256 → approximately **385,000 parameters**.

---

## 22. Training Pipeline

```
OHLCV + Macro data
         │
         ▼ MinMaxScaler [0,1]
    scaled_data [N × 31]
         │
         ▼ build_sequences(seq_length)
    X [M × SeqLen × 31]   y [M]  (log-returns)
         │
         ▼ split_data (70/15/15 chronological)
    train / val / test splits
         │
         ▼ make_loaders (batch_size=32)
    DataLoader objects
         │
         ▼ train_model()
    ┌──────────────────────┐
    │  for epoch in range: │
    │    forward + loss    │
    │    AdamW.step()      │
    │    clip_grad(1.0)    │
    │    CosineAnnealLR    │
    │    val eval          │──► SSE epoch event
    │    early stop check  │
    └──────────────────────┘
         │ best weights restored
         ▼
    Trained HybridModel
         │
    ┌────┴────────────────────────────────┐
    │                                     │
predict_test_set()              monte_carlo_forecast()
    │                                     │
pred_log_returns            {mean, std} × forecast_days
actual_log_returns                        │
    │                              price series + bands
    ▼                                     │
returns_to_prices()               ────► forecast chart
    │
    ├── pred_prices (cumulative)   ──► compute_metrics()
    └── pred_prices_chart (anchored) ──► test chart display
```

---

## 23. Monte Carlo Forecast

```python
model.train()  # dropout active

window = scaled_data[-seq_length:]   # rolling input
cur_price = last_known_close

for step in range(forecast_days):
    # 80 stochastic forward passes
    samples = [model(window) for _ in range(80)]

    mu    = mean(samples)          # expected log-return
    sigma = std(samples)           # epistemic uncertainty

    next_price = cur_price * exp(mu)
    band       = cur_price * sigma

    # Update window: only Close column changes
    window = roll(window, next_feat_with_updated_close)
    cur_price = next_price
```

The spread of 80 dropout-randomised samples captures how uncertain the model is — wider bands signal lower confidence at that horizon.

---

## 24. Bond Yields — Data Strategy

Yahoo Finance does not reliably publish non-US sovereign bond yields. Ticker-Teller uses a 3-tier approach:

**Tier 1 — Real data (US only):**
- `^FVX` → US 5Y Treasury yield
- `^TNX` → US 10Y Treasury yield
- Validation: median yield must be between 0.01% and 20%

**Tier 2 — ETF-movement-shaped synthetic proxy (foreign):**

```
yield(t) = anchor + normalised_etf_drift(t) × 0.5 + ΔUS10Y(t) × sensitivity
```

| Country | ETF | Anchor | US Sensitivity |
|---------|-----|--------|---------------|
| India | INDA | 6.80% | 0.30 |
| Germany | EZU | 2.45% | 0.70 |
| UK | EWU | 4.40% | 0.85 |
| Japan | EWJ | 1.10% | 0.10 |

**Tier 3 — Flat fallback:** Flat series at the anchor yield ± Gaussian noise (σ=0.04%, deterministic seed 42). Always succeeds.

---

## 25. Commodity Forecasting

Holt's Linear Exponential Smoothing with `α=0.3`, `β=0.1`:

```
L₀ = prices[0],  T₀ = prices[1] − prices[0]

for t in 1..n:
    L_t = α × y_t + (1−α)(L_{t-1} + T_{t-1})
    T_t = β(L_t − L_{t-1}) + (1−β)T_{t-1}

forecast[h] = L_n + h × T_n
band[h]     = σ_residuals × √h
```

Uncertainty bands widen with forecast horizon, reflecting compounding uncertainty.

---

## 26. GDP Proxies

Rolling 252-day annualised ETF return used as GDP momentum proxy:

```
annual_return[t] = (ETF[t] / ETF[t−252] − 1) × 100%
```

Fed into `_holt_forecast` for a 30-day forward projection. Consensus estimates used as fallback when ETF history is insufficient.

| Country | ETF | Consensus Fallback |
|---------|-----|-------------------|
| US | SPY | 2.5% |
| India | INDA | 6.8% |
| China | FXI | 4.8% |
| EU | EZU | 1.2% |
| Japan | EWJ | 1.0% |
| UK | EWU | 0.8% |
| Brazil | EWZ | 2.2% |

---

## 27. Mathematics Reference

### Log-return target

```
y[i] = log(close[i] / close[i−1])
```

More stationary than raw prices; approximately normally distributed.

### Combined loss

```
L = Huber(δ=0.01) + 0.4 × E[ReLU(−ŷ × y)]

Huber(δ, ŷ, y) = ½(ŷ−y)²           if |ŷ−y| ≤ δ
                 δ(|ŷ−y| − δ/2)     otherwise
```

### CAPM Beta and Alpha (rolling 60-day)

```
β = Cov(R_stock, R_mkt) / Var(R_mkt)
α = (μ_stock − β × μ_mkt) × 252
```

### Sharpe Ratio (rolling 60-day, annualised)

```
Sharpe = (μ_log_return / σ_log_return) × √252
```

### Bollinger Bands (20-day)

```
BB_Upper = SMA_20 + 2 × σ_20
BB_Lower = SMA_20 − 2 × σ_20
```

### Holt's Linear Smoothing

```
L_t = α × y_t + (1−α)(L_{t-1} + T_{t-1})
T_t = β(L_t − L_{t-1}) + (1−β)T_{t-1}
ŷ_{t+h} = L_t + h × T_t
σ_h = σ_Δy × √h
```

### Monte Carlo Dropout Uncertainty

```
{f_θ^(k)(x)}_{k=1}^{80}      (80 stochastic forward passes)
μ = (1/80) Σ f_θ^(k)(x)
σ = std({f_θ^(k)(x)})

price_forecast = price_prev × exp(μ)
uncertainty    = price_prev × σ
```

---

## 28. API Reference

| Method | Path | Query Params | Body | Returns |
|--------|------|-------------|------|---------|
| POST | `/api/analyze` | — | `AnalyzeConfig` JSON | `text/event-stream` SSE |
| GET | `/api/bonds` | `period` (default 730) | — | JSON |
| GET | `/api/commodities` | `period`, `forecast_days` | — | JSON |
| GET | `/api/gdp` | `period`, `forecast_days` | — | JSON |
| GET | `/api/ticker-info` | `ticker` (required) | — | JSON |
| GET | `/api/health` | — | — | JSON |

SSE response headers: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`.

---

## 29. Configuration Reference

### `vite.config.js` proxy

Proxies `/api/*` to `http://127.0.0.1:8000`. Sets `cache-control: no-cache` and `connection: keep-alive` on `/analyze` responses to prevent SSE buffering.

Note: `api.js` connects directly to `127.0.0.1:8000` (bypassing the proxy) for SSE stability on the streaming endpoint.

### `requirements.txt`

```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
yfinance>=0.2.40
pandas>=2.2.0
numpy>=1.26.0
scikit-learn>=1.5.0
torch>=2.3.0
pydantic>=2.7.0
```

### `package.json` key dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.3.1 | UI framework |
| react-dom | ^18.3.1 | DOM rendering |
| recharts | ^2.12.7 | All charts |
| lucide-react | ^0.383.0 | Icons |
| axios | ^1.7.2 | HTTP client (available; SSE uses Fetch API directly) |
| vite | ^5.3.1 | Build tool + dev server |

---

## 30. Known Limitations and Disclaimer

### Data limitations

- **Non-US bond yields** are ETF-derived proxies anchored to known levels, not authoritative real-time yield data. Useful for trend visualisation; not suitable as exact yield quotes.
- **Commodity data** from Yahoo Finance futures tickers may have gaps near contract expiry or rollover dates.
- **GDP proxies** reflect equity market performance, not official GDP statistics. They can diverge sharply during market dislocations.

### Model limitations

- The model predicts **one-step log-returns** chained auto-regressively for multi-step forecasts. Errors compound: a 5-day forecast is inherently less reliable than a 1-day forecast.
- **No awareness of news, earnings, or macro releases.** The model sees only historical price patterns and the macro features described above.
- **Directional accuracy of 50–60%** is typical for well-trained models on liquid stocks. Anything consistently above 60% warrants scepticism.
- All features are scaled with `MinMaxScaler` fit on training data only — the test and forecast sets use training-set statistics (correct practice, but means extreme out-of-distribution values may be clipped).

### ⚠ Disclaimer

**Ticker-Teller is built for educational and research purposes only.** All forecasts, signals, and analyses carry inherent model risk and uncertainty. Past price patterns do not guarantee future results. Nothing produced by this application constitutes financial advice. Do not make investment decisions based solely or primarily on the output of this tool. Always conduct your own due diligence and consult a qualified financial adviser before trading or investing.
