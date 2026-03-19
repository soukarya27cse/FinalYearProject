# NIFTY 100 Tracker — v2 (Smart Retry)

```
nifty100_tracker.py  ·  v2.0  ·  Python 3.10+  ·  PyTorch 2.x
```

> v2 is a resilient, self-healing upgrade to v1. It adds automatic symbol
> correction via web search, TCP-style exponential backoff, new-listing support,
> and Streamlit warning suppression — while remaining a fully compatible
> drop-in replacement.

---

## Table of Contents

1. [What Changed from v1](#1-what-changed-from-v1)
2. [Overview](#2-overview)
3. [Project Layout](#3-project-layout)
4. [Requirements](#4-requirements)
5. [Installation](#5-installation)
6. [Usage](#6-usage)
7. [Smart Retry — How It Works](#7-smart-retry--how-it-works)
8. [Auto Symbol Correction — Deep Dive](#8-auto-symbol-correction--deep-dive)
9. [Exponential Backoff — Deep Dive](#9-exponential-backoff--deep-dive)
10. [New Listing Support](#10-new-listing-support)
11. [Known Ticker Fixes](#11-known-ticker-fixes)
12. [Excel Workbook Structure](#12-excel-workbook-structure)
13. [Model Architecture](#13-model-architecture)
14. [Feature Engineering](#14-feature-engineering)
15. [Logging](#15-logging)
16. [Resumability & State](#16-resumability--state)
17. [Error Handling Reference](#17-error-handling-reference)
18. [Configuration Reference](#18-configuration-reference)
19. [NIFTY 100 Ticker List](#19-nifty-100-ticker-list)
20. [Known Limitations](#20-known-limitations)
21. [Disclaimer](#21-disclaimer)

---

## 1. What Changed from v1

This is the most important section if you are upgrading from v1.

### Problem 1 — Wrong symbols fail silently

In v1, when a ticker returned HTTP 404 or "possibly delisted", the script
retried the same wrong symbol 3 times, waited 60 seconds between each, then
gave up and moved on. The user had no idea why it failed or what the correct
symbol was.

**v2 fix:** When a symbol-not-found error is detected, v2 calls the
Yahoo Finance search API, finds the current correct symbol, probes it with a
real data download, saves the fix to `state/ticker_fixes.json`, and immediately
retries with the corrected symbol. This happens automatically with no user
action required.

---

### Problem 2 — All errors get the same flat retry

v1 treated a wrong symbol (permanent failure) the same as a network timeout
(recoverable failure). Both got 3 retries with a fixed 60-second delay. This
wasted time on unfixable errors and was too aggressive for API rate limits.

**v2 fix:** Two completely separate retry strategies:
- **Symbol not found** → web search correction, single immediate retry
- **Transient network error** → exponential backoff: 30s → 60s → 120s → 240s → 480s

---

### Problem 3 — New listings crashed with 0 rows

Stocks listed within the last year (e.g. `TMPV.NS`, `TMCV.NS` which demerged
from Tata Motors in late 2025) have fewer than 252 trading days. The
`Momentum_12_1` feature requires `pct_change(252)`, which is `NaN` for every
row. When `dropna()` ran, it eliminated every single row, leaving 0 usable
data points and causing a hard failure.

**v2 fix:**
```python
# v1 — wiped everything
df = df.dropna(subset=FEATURE_COLS)[FEATURE_COLS]

# v2 — fills NaN with 0, only drops fully-empty rows
df = df[FEATURE_COLS].fillna(0)
df = df.replace([np.inf, -np.inf], 0)
df = df.dropna()
```
Plus automatic `seq_length` reduction when fewer than 200 rows of history exist.

---

### Problem 4 — Noisy Streamlit warnings

v1 printed dozens of `No runtime found` and `missing ScriptRunContext` warnings
to the console on every run. These were harmless but made the output hard to
read.

**v2 fix:**
```python
logging.getLogger("streamlit").setLevel(logging.ERROR)
```
Added at import time. Warning-level messages from Streamlit are now suppressed.

---

### Summary table

| Feature | v1 | v2 |
|---|---|---|
| Scheduled 30-day automation | ✅ | ✅ |
| Excel workbook per company | ✅ | ✅ |
| Checkpoint resumability | ✅ | ✅ |
| Per-ticker retry | ✅ 3× fixed 60s | ✅ 5× exponential backoff |
| Auto symbol correction | ❌ | ✅ Yahoo Finance search + probe |
| Persistent fix registry | ❌ | ✅ `ticker_fixes.json` |
| New listing support | ❌ Crashes | ✅ NaN fill + seq_length reduction |
| Streamlit warning suppression | ❌ | ✅ |

---

## 2. Overview

`nifty100_tracker.py` v2 runs Ticker-Teller's deep-learning prediction pipeline
against all 100 NIFTY 100 index constituents, once per day at 18:00 IST, for
30 consecutive days. Results are appended to individual Excel workbooks.

**What happens on each daily run:**

```
For each of the 100 NIFTY companies:
  1.  Apply any known fix from ticker_fixes.json
  2.  Fetch OHLCV history from Yahoo Finance
  3.  Fetch SPY market data for quant-factor computation
  4.  Engineer 22 features (16 price + 6 quant factors)
  5.  Fill NaN features with 0 (handles new listings)
  6.  Auto-reduce seq_length for short-history stocks
  7.  Train HybridModel (CNN → BiLSTM → Attention)
  8.  Run 100 Monte Carlo Dropout forward passes
  9.  Append date / features / actual / predicted / error% to .xlsx
  10. On any failure: classify error → correct symbol or backoff retry
```

---

## 3. Project Layout

```
your-project/
├── nifty100_tracker.py        ← this file (v2)
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data.py                ← feature engineering + Yahoo Finance fetch
│   ├── model.py               ← HybridModel, train_model, monte_carlo_forecast
│   ├── charts.py              ← Plotly builders (not used by tracker)
│   └── ui.py                  ← Streamlit helpers (not used by tracker)
│
├── workbooks/                 ← AUTO-CREATED
│   ├── RELIANCE_NS.xlsx
│   └── …
│
├── logs/                      ← AUTO-CREATED
│   ├── tracker_YYYY-MM-DD.log
│   └── master.log
│
└── state/                     ← AUTO-CREATED
    ├── checkpoint.json        ← daily progress
    └── ticker_fixes.json      ← auto-discovered symbol corrections
```

---

## 4. Requirements

### Python version

```bash
python --version    # 3.10 or higher required
```

### pip packages

| Package | Min Version | Purpose |
|---|---|---|
| `torch` | 2.1.0 | Neural network training and inference |
| `numpy` | 1.26.0 | Array ops, log-return math |
| `pandas` | 2.1.0 | DataFrames, date indexing |
| `scikit-learn` | 1.3.0 | `MinMaxScaler` |
| `yfinance` | 0.2.40 | OHLCV + SPY data |
| `openpyxl` | 3.1.0 | Excel workbook creation |
| `plotly` | 5.18.0 | Transitively imported by `src/charts.py` |
| `streamlit` | 1.35.0 | `@st.cache_data` — mocked in CLI, must be importable |
| `requests` | 2.31.0 | **NEW in v2** — Yahoo Finance search API for auto correction |

---

## 5. Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\Activate.ps1         # Windows PowerShell

# Install all dependencies (includes requests — new in v2)
pip install -r requirements.txt

# Verify
python -c "import torch, pandas, openpyxl, yfinance, streamlit, requests; print('OK')"
```

### GPU (optional)
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 6. Usage

### Command-line flags

| Command | What it does |
|---|---|
| `python nifty100_tracker.py` | Full 30-day automation at 18:00 IST daily |
| `python nifty100_tracker.py --once` | Run all 100 tickers immediately |
| `python nifty100_tracker.py --resume` | Resume from checkpoint |
| `python nifty100_tracker.py --tickers X Y` | Run specific tickers only |
| `python nifty100_tracker.py --once --tickers X` | Test a single ticker |

### Examples

```bash
# Single ticker test
python nifty100_tracker.py --once --tickers RELIANCE.NS

# Test the auto-correction on a known broken symbol
python nifty100_tracker.py --once --tickers ADANITRANS.NS

# Full run
python nifty100_tracker.py --once

# Background run with logging
nohup python nifty100_tracker.py > logs/nohup.log 2>&1 &
echo $! > state/pid.txt

# Resume after crash
python nifty100_tracker.py --resume
```

---

## 7. Smart Retry — How It Works

v2 classifies every exception before deciding what to do. The two failure modes
are handled by completely different code paths.

```
Exception raised
        │
        ▼
  is_symbol_not_found(exc)?
  Checks for: "not found", "404",
  "possibly delisted", "no timezone",
  "no ohlcv data"
        │
   YES ─┤─ NO
        │       │
        ▼       ▼
  Already   is_transient_error(exc)?
  searched? Checks for: "timeout",
        │   "connection", "reset",
   NO   │   "502", "503", "rate limit"
    │   │       │
    ▼   │  YES ─┤─ NO
  Query │       │       │
  Yahoo │       ▼       ▼
  Search│  Exponential  Unknown error
  API   │  backoff      → log + skip
        │  (×5 max)
        │
        ▼
  Probe candidate
  (5-day yfinance download)
        │
  OK ───┤─ FAIL
        │       │
        ▼       ▼
  Save fix    Discard
  to json     candidate
  Retry now   log + skip
        │
   YES ─┤─ STILL FAILING
  (already searched once)
        │
        ▼
  log + skip permanently
```

---

## 8. Auto Symbol Correction — Deep Dive

### When it triggers

Any error message containing: `"not found"`, `"possibly delisted"`,
`"no timezone found"`, `"404"`, `"quote not found"`, `"no data found"`,
`"delisted"`, or `"no ohlcv data"`.

### What it does

```python
# 1. Strip .NS, search Yahoo Finance
stem  = "ADANITRANS"   # from "ADANITRANS.NS"
query = stem
quotes = requests.get(
    "https://query2.finance.yahoo.com/v1/finance/search",
    params={"q": query, "quotesCount": 10}
).json()["quotes"]

# 2. Filter to NSE equities only (.NS suffix)
nse = [q for q in quotes if q["symbol"].endswith(".NS")]

# 3. Score by stem character overlap
# ADANITRANS vs ADANIENSOL → high overlap → ranked #1

# 4. Probe with real data download
probe = yf.download("ADANIENSOL.NS", period="5d")
# Returns data → confirmed ✅

# 5. Save to ticker_fixes.json
{"ADANITRANS.NS": "ADANIENSOL.NS"}

# 6. Retry immediately with ADANIENSOL.NS
```

### Persistence

Once a fix is saved to `state/ticker_fixes.json`, every subsequent run applies
it before attempting any fetch. The Yahoo Finance search API is only called
once per broken symbol — ever.

```json
{
  "ADANITRANS.NS": "ADANIENSOL.NS",
  "ZOMATO.NS":     "ETERNAL.NS"
}
```

### End-of-day fix report in logs

```
-- Current ticker fix map ------------------------------------------
   ADANITRANS.NS                  -> ADANIENSOL.NS
   ZOMATO.NS                      -> ETERNAL.NS
--------------------------------------------------------------------
```

---

## 9. Exponential Backoff — Deep Dive

### When it triggers

Any error message containing: `"connection"`, `"timeout"`, `"timed out"`,
`"reset"`, `"refused"`, `"rate limit"`, `"too many requests"`,
`"service unavailable"`, `"502"`, `"503"`, `"504"`, `"read error"`,
`"ssl"`, `"eof"`, `"remote end closed"`, `"chunkedencodingerror"`.

Also applies as the default handler for any unknown error type.

### The backoff schedule

```
Attempt 1 fails → wait  30s  → retry   (TRANSIENT_BASE_DELAY × 2⁰)
Attempt 2 fails → wait  60s  → retry   (TRANSIENT_BASE_DELAY × 2¹)
Attempt 3 fails → wait 120s  → retry   (TRANSIENT_BASE_DELAY × 2²)
Attempt 4 fails → wait 240s  → retry   (TRANSIENT_BASE_DELAY × 2³)
Attempt 5 fails → wait 480s  → retry   (TRANSIENT_BASE_DELAY × 2⁴)
Attempt 6 fails → give up, log ERROR, skip
```

Total maximum wait before giving up: **930 seconds (15.5 minutes)**.

### Why exponential backoff works

This mirrors TCP retransmission. If the Yahoo Finance API is rate-limiting
requests or temporarily overloaded, hammering it every 60 seconds makes things
worse. Doubling the delay gives the API time to recover. By attempt 5 the
cumulative wait is over 10 minutes — enough for virtually any transient outage
to resolve.

### Example log output

```
[TATAMOTORS.NS] Attempt 1/5 failed (HTTP 503 Service Unavailable) --> retrying in 30s [backoff x2 per attempt]
[TATAMOTORS.NS] Attempt 2/5 failed (HTTP 503 Service Unavailable) --> retrying in 60s [backoff x2 per attempt]
[TATAMOTORS.NS] actual=724.10  predicted=731.20  error=0.98%   ← recovered on attempt 3
```

---

## 10. New Listing Support

### The v1 problem

`Momentum_12_1` is computed as `pct_change(252) - pct_change(21)`. For stocks
with fewer than 252 trading days of history, `pct_change(252)` returns `NaN`
for every single row. When v1 called `dropna(subset=FEATURE_COLS)`, it
eliminated every row, leaving 0 usable rows and triggering:

```
[TMPV.NS] Insufficient rows (0) — skipping.
```

### The v2 fix

Two changes in `run_prediction()`:

**1. NaN fill:**
```python
df = df[FEATURE_COLS].fillna(0)        # NaN → 0 for missing long-window features
df = df.replace([np.inf, -np.inf], 0)  # also catch any inf values from division
df = df.dropna()                       # only drops rows that are truly all-NaN
```

**2. Auto seq_length reduction:**
```python
cfg = MODEL_CFG.copy()
if len(df_raw) < 200:
    cfg["seq_length"] = min(30, len(df_raw) // 3)
    logger.info(f"[{ticker}] Short history — reducing seq_length to {cfg['seq_length']}")
```

### Affected tickers

| Ticker | Company | Listed | History as of March 2026 |
|---|---|---|---|
| `TMPV.NS` | Tata Motors Passenger Vehicles | Oct 2025 | ~100 days |
| `TMCV.NS` | Tata Motors Commercial Vehicles | Nov 2025 | ~80 days |

Both now run successfully in v2. Prediction quality is lower than for
established stocks because `Momentum_12_1`, `Beta_60`, and `Alpha_60` are
`0.0` (no history to compute them). Quality improves automatically once 252+
trading days accumulate — no code changes needed.

---

## 11. Known Ticker Fixes

Confirmed corrections discovered during live testing. Already applied in the
`NIFTY100_TICKERS` list in v2.

| Old Symbol ❌ | Correct Symbol ✅ | Root Cause |
|---|---|---|
| `INFOSYS.NS` | `INFY.NS` | Yahoo Finance uses the short-form ticker |
| `ZOMATO.NS` | `ETERNAL.NS` | Rebranded to Eternal Limited — March 2025 |
| `ADANITRANS.NS` | `ADANIENSOL.NS` | Rebranded to Adani Energy Solutions — July 2023 |
| `TATAMOTORS.NS` | `TMPV.NS` + `TMCV.NS` | Demerged into two entities — October 2025 |

When v2 encounters any other broken symbol not in this list, it will
auto-discover the correct one via Yahoo Finance search and add it to
`ticker_fixes.json` permanently.

---

## 12. Excel Workbook Structure

One `.xlsx` per company in `workbooks/`. Same structure as v1 — fully
backward compatible. Existing v1 workbooks can be appended to by v2 without
any migration.

### Predictions sheet

| Col | Header | Type | Description |
|---|---|---|---|
| A | Date | Text | `YYYY-MM-DD` |
| B | Ticker | Text | Yahoo Finance symbol (corrected symbol if auto-fixed) |
| C | Price Features (16) | Text | Feature snapshot — `key=value \| …` |
| D | Quant Factor Features (6) | Text | Factor snapshot — `key=value \| …` |
| E | Actual Price | Number | Last known close |
| F | Predicted Price | Number | MC-Dropout mean (100 passes) |
| G | Error (%) | Excel formula | `=ABS(((E-F)/E)*100)` — green or red |
| H | Signed Error | Excel formula (hidden) | Raw signed error — drives colour |

### Colour coding

| Colour | Condition | Meaning |
|---|---|---|
| Dark green + green text | Actual > Predicted | Model underestimated |
| Dark red + red text | Actual < Predicted | Model overestimated |

---

## 13. Model Architecture

### Prediction target
```
y[t] = log(Close[t] / Close[t-1])
next_price = last_close × exp(y[t])
```

### Layer stack
```
Input (batch, seq_len, 22 features)
  ↓
TemporalConvBlock — dual-kernel CNN (3 & 5) + residual
  ↓
Bidirectional LSTM — 2 layers, forward + backward
  ↓
MultiHeadAttentionBlock — self-attention + residual + LayerNorm
  ↓
Temporal Attention Pooling — learnable time-step weights
  ↓
FC head — Dropout → Linear → GELU → Dropout → Linear → scalar
```

### Training settings

| Setting | Value |
|---|---|
| Loss | Huber(δ=0.01) + 0.4 × `relu(−pred × target)` |
| Optimiser | AdamW (`lr=1e-3`, `wd=1e-4`) |
| LR schedule | CosineAnnealingWarmRestarts (`T₀=10`, `T_mult=2`) |
| Gradient clip | max_norm = 1.0 |
| Early stopping | patience = 10 |
| MC samples | 100 |

---

## 14. Feature Engineering

### Price branch — 16 features

| Feature | Group |
|---|---|
| `Open`, `High`, `Low`, `Close`, `Volume` | OHLCV |
| `SMA_10`, `SMA_50`, `MACD`, `MACD_Signal` | Trend |
| `RSI`, `ROC_10`, `Stoch_K` | Momentum |
| `BB_Upper`, `BB_Lower`, `ATR` | Volatility |
| `OBV_norm` | Volume |

### Factor branch — 6 features

| Feature | Description | Min history needed |
|---|---|---|
| `Beta_60` | CAPM beta vs SPY (60-day rolling OLS) | 60 days |
| `Alpha_60` | Jensen's alpha, annualised | 60 days |
| `Momentum_12_1` | 12-month minus 1-month return | **252 days** |
| `Sharpe_60` | 60-day annualised Sharpe ratio | 60 days |
| `Vol_Ratio` | 10-day vol / 60-day vol | 60 days |
| `Mkt_Return` | SPY daily log return | 1 day |

> Features marked "252 days" will be `0.0` for new listings until sufficient
> history exists. This is handled automatically in v2 and does not cause errors.

---

## 15. Logging

```
logs/
├── tracker_YYYY-MM-DD.log    ← DEBUG level — full detail for one day
└── master.log                ← INFO level  — cumulative 30-day view
```

### Log line examples

```
# Successful prediction
2026-03-19 18:02:34 | INFO    | [RELIANCE.NS] actual=1384.80  predicted=1394.03  error=0.67%

# Auto-correction triggered
2026-03-19 18:03:11 | WARNING | [ADANITRANS.NS] Symbol not found --> searching Yahoo Finance...
2026-03-19 18:03:12 | INFO    | [ADANITRANS.NS] Top candidate: ADANIENSOL.NS  score=42
2026-03-19 18:03:14 | INFO    | [ADANITRANS.NS] Confirmed replacement: ADANIENSOL.NS
2026-03-19 18:03:14 | INFO    | [ADANITRANS.NS] Retrying with corrected symbol: ADANIENSOL.NS
2026-03-19 18:03:28 | INFO    | [ADANIENSOL.NS] actual=812.30  predicted=819.45  error=0.88%

# Transient backoff
2026-03-19 18:10:05 | WARNING | [TATAMOTORS.NS] Attempt 1/5 failed (HTTP 503) --> retrying in 30s
2026-03-19 18:10:39 | INFO    | [TATAMOTORS.NS] actual=724.10  predicted=731.20  error=0.98%

# Day summary — new auto-corrected field
2026-03-19 20:14:07 | INFO    | === Day complete 2026-03-19 ===  success=98  auto-corrected=2  skipped=0  failed=0
```

### Day summary fields

| Field | Meaning |
|---|---|
| `success` | Written to Excel |
| `auto-corrected` | Symbol was fixed by web search before succeeding |
| `skipped` | Already done today (checkpoint) |
| `failed` | All recovery attempts exhausted |

```bash
tail -f logs/master.log
```

---

## 16. Resumability & State

### checkpoint.json
```json
{
  "start_date": "2026-03-19",
  "days_completed": 5,
  "daily_records": {
    "2026-03-19": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "ADANIENSOL.NS", "..."],
    "2026-03-20": ["RELIANCE.NS", "..."]
  }
}
```

### ticker_fixes.json
```json
{
  "INFOSYS.NS":    "INFY.NS",
  "ZOMATO.NS":     "ETERNAL.NS",
  "ADANITRANS.NS": "ADANIENSOL.NS",
  "TATAMOTORS.NS": "TMPV.NS"
}
```

v2 marks **both** the original symbol and the corrected symbol as done in the
checkpoint. This prevents a corrected ticker from being re-run a second time
in the same day if the original name also appears in the ticker list.

### Resume
```bash
python nifty100_tracker.py --resume
```

---

## 17. Error Handling Reference

| Error type | Detection | Response |
|---|---|---|
| HTTP 404 / "not found" / "delisted" | `is_symbol_not_found()` | Query Yahoo Finance search → probe → save fix → retry once |
| Timeout / connection reset / 502–504 | `is_transient_error()` | Exponential backoff × 5 (30s → 480s) |
| `Insufficient rows (0)` on new listings | Caught in `run_prediction()` | NaN fill + seq_length reduction |
| SPY data unavailable | `market_df` is None or empty | Use ticker's own Close as market proxy. `WARNING` logged. |
| Excel write error | Exception in `append_prediction_row()` | `ERROR` logged. Not marked done → `--resume` retries. |
| Crash / `Ctrl+C` | — | `--resume` continues from checkpoint. No duplicates. |
| CUDA out-of-memory | GPU exception | Reduce `hidden_size`/`cnn_channels`. Falls back to CPU on retry. |

---

## 18. Configuration Reference

### Scheduler

| Constant | Default | Description |
|---|---|---|
| `TOTAL_DAYS` | `30` | Calendar days of automation |
| `RUN_HOUR` | `18` | Fire hour (IST) |
| `RUN_MINUTE` | `0` | Fire minute |

### Retry

| Constant | Default | Description |
|---|---|---|
| `TRANSIENT_MAX_RETRIES` | `5` | Max retries for transient errors |
| `TRANSIENT_BASE_DELAY` | `30` | Base delay in seconds (doubles each attempt) |

### Model (`MODEL_CFG`)

| Key | Default | Description |
|---|---|---|
| `period` | `730` | History days to fetch |
| `seq_length` | `60` | Lookback window (auto-reduced for new listings) |
| `epochs` | `50` | Max training epochs |
| `patience` | `10` | Early stopping patience |
| `hidden_size` | `128` | BiLSTM hidden size |
| `cnn_channels` | `64` | CNN channels |
| `num_heads` | `4` | Attention heads |
| `dropout` | `0.2` | Dropout rate |

### Paths

| Constant | Default |
|---|---|
| `WORKBOOK_DIR` | `./workbooks/` |
| `LOG_DIR` | `./logs/` |
| `STATE_DIR` | `./state/` |

---

## 19. NIFTY 100 Ticker List

100 symbols in Yahoo Finance `.NS` format. All known corrections already
applied in `NIFTY100_TICKERS`. Any future broken symbols will be auto-corrected
at runtime and saved to `ticker_fixes.json`.

```
RELIANCE.NS   TCS.NS        HDFCBANK.NS   BHARTIARTL.NS  ICICIBANK.NS
INFY.NS       SBIN.NS       HINDUNILVR.NS ITC.NS         LT.NS
ETERNAL.NS    ADANIENSOL.NS TMPV.NS       TMCV.NS        ...
(100 total — see NIFTY100_TICKERS in the script)
```

---

## 20. Known Limitations

**Training time** — 100 tickers × 50 epochs on CPU: 4–8+ hours per day. Use a
GPU or reduce `MODEL_CFG["epochs"]`.

**Market data freshness** — `yfinance` can be delayed up to 24 hours. The
18:00 IST fire time targets the 15:30 NSE close.

**No model persistence** — Retrained from scratch every day by design. For
production use, consider warm-starting from yesterday's weights.

**No market-holiday detection** — Fires every calendar day. On non-trading
days, `yfinance` returns the most recent close silently.

**New listings (< 252 days)** — `Momentum_12_1`, `Beta_60`, `Alpha_60` will
be `0.0` until sufficient history exists. Prediction quality is lower but the
pipeline runs without errors.

---

## 21. Disclaimer

> **For educational and research purposes only.**
>
> Predictions are probabilistic estimates based on historical patterns.
> They are not financial advice and should not be used as the sole basis for
> investment decisions. Corporate events, delistings, demergers, and
> macroeconomic shifts can invalidate any quantitative model without warning.
>
> **Always consult a qualified financial advisor before investing.**

---

*Ticker-Teller NIFTY 100 Tracker — v2.0 (Smart Retry + Auto Symbol Correction)*
