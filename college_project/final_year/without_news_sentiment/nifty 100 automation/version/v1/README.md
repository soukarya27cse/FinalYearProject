# 📈 NIFTY 100 Tracker — v1

```
nifty100_tracker.py  ·  v1.0  ·  Python 3.10+  ·  PyTorch 2.x
```

> The first version of the automated daily prediction pipeline.
> Runs the Ticker-Teller model against all 100 NIFTY 100 companies once per day,
> appends results to individual Excel workbooks, and repeats for 30 consecutive days.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Layout](#2-project-layout)
3. [Requirements](#3-requirements)
4. [Installation](#4-installation)
5. [Usage](#5-usage)
6. [How It Works — Step by Step](#6-how-it-works--step-by-step)
7. [Excel Workbook Structure](#7-excel-workbook-structure)
8. [Model Architecture](#8-model-architecture)
9. [Feature Engineering](#9-feature-engineering)
10. [Logging](#10-logging)
11. [Resumability & State](#11-resumability--state)
12. [Error Handling](#12-error-handling)
13. [Configuration Reference](#13-configuration-reference)
14. [NIFTY 100 Ticker List](#14-nifty-100-ticker-list)
15. [Known Issues & Limitations](#15-known-issues--limitations)
16. [Upgrade to v2](#16-upgrade-to-v2)
17. [Disclaimer](#17-disclaimer)

---

## 1. Overview

`nifty100_tracker.py` v1 is a headless CLI automation script. It wraps the
Ticker-Teller v5 deep-learning prediction pipeline and applies it to every
company in the NIFTY 100 index, once per day, for 30 days.

There is no Streamlit UI. No browser opens. It runs entirely in the terminal
and produces one Excel file per company under `workbooks/`.

**What happens on each daily run:**

```
For each of the 100 NIFTY companies:
  1.  Fetch OHLCV history from Yahoo Finance (730 days)
  2.  Fetch SPY market data for quant-factor computation
  3.  Engineer 22 features (16 price + 6 quant factors)
  4.  Scale features with MinMaxScaler
  5.  Build 60-day sliding-window sequences
  6.  Train HybridModel (CNN → BiLSTM → Attention)
  7.  Run 100 Monte Carlo Dropout forward passes
  8.  Append date / features / actual / predicted / error% to .xlsx
```

The scheduler waits until **18:00 IST** (after NSE closes at 15:30 IST) then
fires. This repeats every calendar day for 30 days.

---

## 2. Project Layout

```
your-project/
├── nifty100_tracker.py        ← this file (v1)
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
│   ├── TCS_NS.xlsx
│   └── …
│
├── logs/                      ← AUTO-CREATED
│   ├── tracker_2026-03-19.log
│   └── master.log
│
└── state/                     ← AUTO-CREATED
    └── checkpoint.json
```

---

## 3. Requirements

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
| `yfinance` | 0.2.40 | OHLCV + SPY data from Yahoo Finance |
| `openpyxl` | 3.1.0 | Excel workbook creation and formatting |
| `plotly` | 5.18.0 | Imported transitively by `src/charts.py` |
| `streamlit` | 1.35.0 | `@st.cache_data` in `src/data.py` — mocked in CLI |

> **Why `streamlit` in a CLI tool?** `src/data.py` and `src/model.py` were
> originally written for the Streamlit web app and use `@st.cache_data` and
> `st.progress()`. The tracker wraps these calls with `unittest.mock` so no
> browser opens, but `streamlit` must be importable or the `src/` package
> fails to load.

---

## 4. Installation

### Virtual environment (recommended)

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install
pip install -r requirements.txt
```

### Verify

```bash
python -c "import torch, pandas, openpyxl, yfinance, streamlit; print('OK')"
```

### GPU (optional)

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

The tracker auto-detects CUDA via `torch.cuda.is_available()` and falls back
to CPU.

---

## 5. Usage

### Command-line flags

| Command | What it does |
|---|---|
| `python nifty100_tracker.py` | Full 30-day automation. Waits for 18:00 IST, runs daily. |
| `python nifty100_tracker.py --once` | Run all tickers immediately, no scheduler. |
| `python nifty100_tracker.py --resume` | Resume from last checkpoint after interruption. |
| `python nifty100_tracker.py --tickers X Y` | Run only specific tickers. |
| `python nifty100_tracker.py --once --tickers X` | Test a single ticker immediately. |

### Examples

```bash
# Smoke test — one ticker
python nifty100_tracker.py --once --tickers RELIANCE.NS

# Small subset test
python nifty100_tracker.py --once --tickers RELIANCE.NS TCS.NS INFY.NS

# Full run of all 100 tickers right now
python nifty100_tracker.py --once

# Start 30-day scheduled automation
python nifty100_tracker.py

# Run in background (Linux/macOS)
nohup python nifty100_tracker.py > logs/nohup.log 2>&1 &
echo $! > state/pid.txt

# Resume after interruption
python nifty100_tracker.py --resume
```

---

## 6. How It Works — Step by Step

### Step 1 — Fetch data
`fetch_data(ticker, 730)` downloads up to 730 trading days of OHLCV from
Yahoo Finance. `fetch_market_data(730)` downloads SPY with an extra 300 days
of buffer so rolling 60-day windows are fully populated from day one.

### Step 2 — Feature engineering
`add_technical_features()` computes 11 indicators on top of OHLCV.
`add_quant_features()` computes 6 rolling quantitative factor features using
vectorised OLS regression (no loops per row — runs fast).

### Step 3 — Scale and sequence
`MinMaxScaler` scales all 22 features to `[0, 1]`. `build_sequences()` slides
a 60-day window across the scaled data, with the target being the log return at
each step.

### Step 4 — Split and load
Data is split 70% train / 15% validation / 15% test. Each split is wrapped in
a `DataLoader` with `batch_size=32`.

### Step 5 — Train
`train_model()` trains the `HybridModel` with `AdamW`, `CombinedLoss` (Huber +
directional penalty), `CosineAnnealingWarmRestarts`, and early stopping.
Streamlit's `st.progress()` and `st.empty()` calls are mocked so the training
loop runs silently.

### Step 6 — Monte Carlo forecast
`monte_carlo_forecast()` keeps the model in `train` mode and runs 100 forward
passes. The mean is the predicted price. The standard deviation is the
uncertainty estimate.

### Step 7 — Write Excel
`append_prediction_row()` opens the existing `.xlsx` for this ticker (creating
it first if needed), finds `max_row + 1`, writes the new row, applies
green/red colour to the error cell based on the sign of the prediction error,
and saves.

### Step 8 — Checkpoint
`mark_ticker_done()` writes the ticker to `state/checkpoint.json` so if the
run is interrupted it can be resumed from exactly where it left off.

---

## 7. Excel Workbook Structure

One `.xlsx` per company in `workbooks/`. Filename format: `RELIANCE_NS.xlsx`,
`BAJAJ_AUTO_NS.xlsx`, `MANDM_NS.xlsx`.

### Predictions sheet

Two frozen header rows. One data row appended per daily run.

| Col | Header | Type | Description |
|---|---|---|---|
| A | Date | Text | `YYYY-MM-DD` |
| B | Ticker | Text | Yahoo Finance symbol |
| C | Price Features (16) | Text | Feature snapshot — `key=value \| …` |
| D | Quant Factor Features (6) | Text | Factor snapshot — `key=value \| …` |
| E | Actual Price | Number | Last known close from Yahoo Finance |
| F | Predicted Price | Number | MC-Dropout mean of 100 forward passes |
| G | Error (%) | Excel formula | `=ABS(((E-F)/E)*100)` |
| H | Signed Error | Excel formula (hidden) | Raw signed error — drives colour logic |

### Colour coding

| Colour | Condition | Meaning |
|---|---|---|
| Dark green + green text | Actual > Predicted | Model underestimated the price |
| Dark red + red text | Actual < Predicted | Model overestimated the price |

### Growth over 30 days

```
RELIANCE_NS.xlsx

Row 1-2  → Frozen headers (written once)
Row 3    → 2026-03-19   actual=1384.80   predicted=1394.03   error=0.67%
Row 4    → 2026-03-20   actual=1391.20   predicted=1388.45   error=0.20%
...
Row 32   → 2026-04-17   actual=...       predicted=...       error=...%
```

---

## 8. Model Architecture

### Prediction target
```
y[t] = log(Close[t] / Close[t-1])   ← stationary log return
next_price = last_close × exp(y[t])
```

### Layer stack
```
Input (batch, seq_len=60, features=22)
  │
  ▼
TemporalConvBlock
  Dual-kernel CNN (sizes 3 & 5) + residual projection
  │
  ▼
Bidirectional LSTM (2 layers, variational dropout)
  │
  ▼
MultiHeadAttentionBlock (self-attention + residual + LayerNorm)
  │
  ▼
Temporal Attention Pooling (learnable time-step weights)
  │
  ▼
FC head → Dropout → Linear → GELU → Dropout → Linear → scalar
```

### Training
| Setting | Value |
|---|---|
| Loss | Huber(δ=0.01) + 0.4 × directional penalty |
| Optimiser | AdamW (`lr=1e-3`, `wd=1e-4`) |
| LR schedule | CosineAnnealingWarmRestarts (`T₀=10`, `T_mult=2`) |
| Gradient clip | max_norm = 1.0 |
| Early stopping | patience = 10 epochs |
| MC samples | 100 forward passes |

---

## 9. Feature Engineering

### Price branch — 16 features

| Feature | Group |
|---|---|
| `Open`, `High`, `Low`, `Close`, `Volume` | OHLCV |
| `SMA_10`, `SMA_50` | Trend |
| `MACD`, `MACD_Signal` | Trend |
| `RSI` | Momentum |
| `ROC_10` | Momentum |
| `Stoch_K` | Momentum |
| `BB_Upper`, `BB_Lower` | Volatility |
| `ATR` | Volatility |
| `OBV_norm` | Volume |

### Factor branch — 6 features

| Feature | Description |
|---|---|
| `Beta_60` | Rolling 60-day CAPM beta vs SPY |
| `Alpha_60` | Rolling Jensen's alpha, annualised |
| `Momentum_12_1` | Jegadeesh-Titman 12-month minus 1-month return |
| `Sharpe_60` | Rolling 60-day annualised Sharpe ratio |
| `Vol_Ratio` | 10-day vol / 60-day vol — regime indicator |
| `Mkt_Return` | SPY daily log return |

---

## 10. Logging

```
logs/
├── tracker_YYYY-MM-DD.log    ← DEBUG — full detail per day
└── master.log                ← INFO  — cumulative 30-day summary
```

**Format:**
```
2026-03-19 18:02:34 | INFO    | nifty100_tracker | [RELIANCE.NS] actual=1384.80  predicted=1394.03  error=0.67%
2026-03-19 20:14:07 | INFO    | nifty100_tracker | === Day complete 2026-03-19 ===  success=97  skipped=0  failed=3
```

**Live tail:**
```bash
tail -f logs/master.log
```

---

## 11. Resumability & State

`state/checkpoint.json` is written after every successfully saved ticker:

```json
{
  "start_date": "2026-03-19",
  "days_completed": 3,
  "daily_records": {
    "2026-03-19": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "..."]
  }
}
```

After any interruption:
```bash
python nifty100_tracker.py --resume
```

The script reads the checkpoint, skips already-completed tickers, and continues
from exactly where it stopped. No duplicate rows are ever written.

---

## 12. Error Handling

| Failure | Response in v1 |
|---|---|
| HTTP 404 / symbol not found | Logs `WARNING` + `ERROR`. Tries up to 3 times with 60s delay. Then skips. **No auto-correction.** |
| Transient network error | Same 3-retry fixed-delay loop. |
| Insufficient data rows | Logs warning, skips ticker. |
| SPY unavailable | Uses ticker's own Close as proxy. |
| Excel write error | Logs error. Ticker not marked done — retry possible via `--resume`. |
| Crash / interruption | Resume with `--resume`. No duplicate rows. |

> **v1 limitation:** When a ticker fails because its Yahoo Finance symbol has
> changed (e.g. rebrands, demergers), v1 has no mechanism to find the correct
> symbol. It will fail 3 times and skip. You must manually update
> `NIFTY100_TICKERS` in the source file.
>
> v2 fixes this with automatic web search and symbol correction.
> See [Section 16](#16-upgrade-to-v2).

---

## 13. Configuration Reference

### Scheduler

| Constant | Default | Description |
|---|---|---|
| `TOTAL_DAYS` | `30` | Calendar days of automation |
| `RUN_HOUR` | `18` | Fire hour (24h IST) |
| `RUN_MINUTE` | `0` | Fire minute |
| `RETRY_ATTEMPTS` | `3` | Retries per ticker |
| `RETRY_DELAY` | `60` | Seconds between retries (fixed) |

### Model (`MODEL_CFG`)

| Key | Default | Description |
|---|---|---|
| `period` | `730` | History days to fetch |
| `seq_length` | `60` | Lookback window |
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

## 14. NIFTY 100 Ticker List

All 100 symbols in Yahoo Finance `.NS` format. Corrections already applied:
`INFY.NS` (not `INFOSYS.NS`), `ETERNAL.NS` (not `ZOMATO.NS`),
`ADANIENSOL.NS` (not `ADANITRANS.NS`), `TMPV.NS` + `TMCV.NS` (not `TATAMOTORS.NS`).

```
RELIANCE.NS  TCS.NS  HDFCBANK.NS  BHARTIARTL.NS  ICICIBANK.NS
INFY.NS  SBIN.NS  HINDUNILVR.NS  ITC.NS  LT.NS
... (100 total, see NIFTY100_TICKERS in the script)
```

---

## 15. Known Issues & Limitations

**No auto symbol correction** — When a company rebrands or demerges, Yahoo
Finance changes the ticker symbol. v1 has no mechanism to detect this. The
ticker will fail all 3 retry attempts and be skipped. You must manually edit
`NIFTY100_TICKERS` each time this happens.

**Fixed retry delay** — All errors (wrong symbol, network timeout, rate limit)
get the same 3 retries with a fixed 60-second delay. This is suboptimal: a
wrong symbol will never succeed no matter how many times you retry it, and a
network timeout might need longer to recover.

**New listings fail** — Stocks with fewer than 252 trading days of history
(e.g. recently demerged companies like `TMPV.NS`, `TMCV.NS`) will hit
`Insufficient rows (0)` because `dropna()` wipes all rows where the
`Momentum_12_1` feature is `NaN`. v1 cannot handle these.

**Streamlit warnings** — Running v1 will print many `No runtime found` and
`missing ScriptRunContext` warnings to the console. These are harmless but
noisy.

**Training time** — 100 tickers × 50 epochs on CPU takes 4–8+ hours per day.

---

## 16. Upgrade to v2

v2 is a drop-in replacement for v1. Replace your `nifty100_tracker.py` with
the v2 file. All existing workbooks, checkpoint, and state files remain valid.

**What v2 adds:**

| Problem in v1 | Solution in v2 |
|---|---|
| Wrong symbol → fails silently after 3 retries | Queries Yahoo Finance search API → probes candidate → auto-corrects → saves fix to `ticker_fixes.json` |
| All errors get same flat retry | Exponential backoff for transient errors (30s → 60s → 120s → 240s → 480s) |
| New listings crash with 0 rows | `NaN` fill + auto `seq_length` reduction |
| Streamlit warnings fill the console | Suppressed via `logging.getLogger("streamlit").setLevel(logging.ERROR)` |

```bash
# After replacing the file, verify with:
python nifty100_tracker.py --once --tickers RELIANCE.NS
```

---

## 17. Disclaimer

> **For educational and research purposes only.**
>
> Predictions are probabilistic estimates based on historical patterns.
> They are not financial advice and should not be used as the sole basis for
> investment decisions.
>
> **Always consult a qualified financial advisor before investing.**

---

*Ticker-Teller NIFTY 100 Tracker — v1.0*
