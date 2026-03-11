# 📈 Ticker-Teller

> LSTM time-series forecasting × Monte Carlo uncertainty estimation

A professional stock prediction dashboard built with PyTorch and Streamlit, styled with the Ticker-Teller dark finance theme.

---

## Features

- **Multi-variate LSTM** — trains on OHLCV data enriched with SMA(10), SMA(50), RSI(14), MACD, MACD Signal, and Bollinger Bands (12 features total)
- **Monte Carlo Dropout** — runs 100 stochastic forward passes per forecast step to produce calibrated uncertainty bands
- **Gradient clipping** — caps gradients at `max_norm=1.0` to prevent exploding gradients in deep LSTM layers
- **Early stopping** — halts training when validation loss plateaus and restores the best-epoch weights automatically
- **ReduceLROnPlateau** — halves the learning rate when progress stalls
- **Loss curves** — train vs. val MSE visualised per epoch in the Model Performance tab, with best-epoch marker
- **Interactive chart** — price history, Bollinger Band overlay, RSI subplot, test-set predictions, future forecast, uncertainty band, and volume bars in a single Plotly figure
- **Range selector & rangeslider** — 1M / 3M / 6M / 1Y / 2Y / ALL buttons plus a draggable scrubber for zooming into any section; hover tooltip shows the full date
- **MACD chart** — dedicated tab with MACD histogram, signal line, and zero-line
- **AI signal badge** — Strong Buy / Buy / Hold / Sell / Strong Sell derived from the forecast direction

---

## Project Structure

```
ticker-teller/
├── app.py               # Entry point — orchestration only, no ML logic
├── requirements.txt
└── src/
    ├── __init__.py      # Package marker (version string)
    ├── data.py          # Data fetching, feature engineering, sequencing, splits
    ├── model.py         # LSTMModel, StockDataset, training loop, inference helpers
    ├── charts.py        # Plotly figure builders
    └── ui.py            # CSS injection, sidebar widgets, reusable HTML components
```

---

### Module responsibilities

| File | What lives here |
|---|---|
| `app.py` | Streamlit page config, button handler, pipeline orchestration |
| `src/data.py` | `fetch_data`, `add_technical_features`, `build_sequences`, `split_data`, `inverse_close` |
| `src/model.py` | `LSTMModel`, `StockDataset`, `make_loaders`, `train_model`, `predict_test_set`, `monte_carlo_forecast` |
| `src/charts.py` | `build_price_chart`, `build_loss_chart`, `build_macd_chart` — returns Plotly `Figure` objects, knows nothing about Streamlit |
| `src/ui.py` | `inject_css`, `render_header`, `render_sidebar`, `section_header`, `signal_badge`, `split_pills`, `render_about_tab` |

---

## Requirements

- Python 3.10+
- See `requirements.txt` for pinned package versions

```
streamlit>=1.35
yfinance>=0.2
pandas>=2.0
numpy>=1.26
torch>=2.0
scikit-learn>=1.4
plotly>=5.20
```

---

## Setup

**1. Create and activate a virtual environment**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run the app**

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Usage

| Sidebar control | What it does |
|---|---|
| **Ticker Symbol** | Any valid Yahoo Finance ticker, e.g. `AAPL`, `TSLA`, `MSFT` |
| **Historical Data (Days)** | How far back to fetch OHLCV data. Minimum recommended: **1460 days (4 years)** |
| **Lookback Sequence (Days)** | Number of past trading days the LSTM sees at each step (default 60) |
| **Forecast Horizon (Days)** | How many business days ahead to forecast (default 5) |
| **Max Training Epochs** | Upper bound on training iterations (early stopping may halt before this) |
| **Early Stopping Patience** | Epochs to wait for validation loss improvement before halting (default 10) |
| **LSTM Hidden Size** | Number of memory units per LSTM layer — choose 32 / 64 / 128 / 256 (default 128) |
| **Dropout Rate** | Regularisation strength, also controls MC uncertainty band width (default 0.2) |

### Tips for best results

- Use at least **3–5 years** of history. Short histories produce tiny val/test sets that cause premature early stopping.
- If early stopping fires before epoch 20, increase the historical data period before tuning patience.
- The Monte Carlo uncertainty band widens with longer forecast horizons — treat multi-week forecasts as directional guidance only.
- Increase **Hidden Size** to 256 for large-cap, high-volume tickers with long histories. Use 64 or 32 for faster experimentation.
- Higher **Dropout Rate** → wider uncertainty bands and stronger regularisation. Lower → tighter bands but more overfitting risk.

---

## Output Metrics

| Metric | Description |
|---|---|
| **Current Price** | Last closing price fetched from Yahoo Finance |
| **Forecast (+Nd)** | LSTM mean prediction N business days ahead |
| **Directional Accuracy** | % of test-set days where the model correctly predicted up vs. down |
| **MAE (Test Set)** | Mean Absolute Error in dollars on the held-out test set |
| **Ann. Volatility** | Daily return std × √252, annualised — how "jumpy" the stock is |
| **Best Val Loss** | Lowest MSE achieved on the validation set during training |
| **AI Signal** | STRONG BUY / BUY / HOLD / STRONG SELL — derived from forecast % change |

---

## Data Split

The dataset is divided into three non-overlapping, temporally ordered sets:

```
|── 70% Train ──|── 15% Val ──|── 15% Test ──|
```

A minimum of 30 samples is enforced for both val and test regardless of dataset size. Data is never shuffled — temporal order is preserved throughout.

---

## Model Architecture

```
Input  (batch, seq_length, 12 features)
  └─ LSTM  ×2 layers, hidden_size=128 (configurable), dropout=0.2
       └─ Dropout(0.2)
            └─ Linear(128 → 1)
Output (batch, 1)  — scaled Close price
```

| Component | Detail |
|---|---|
| Loss function | `MSELoss` |
| Optimiser | `Adam(lr=0.001)` |
| LR scheduler | `ReduceLROnPlateau(factor=0.5, patience=5)` |
| Gradient clipping | `clip_grad_norm_(max_norm=1.0)` |
| MC Dropout samples | 100 per forecast step |

---

## Features Engineered

| Feature | Description |
|---|---|
| `Open`, `High`, `Low`, `Close`, `Volume` | Raw OHLCV from Yahoo Finance |
| `SMA_10` | 10-day Simple Moving Average of Close |
| `SMA_50` | 50-day Simple Moving Average of Close |
| `RSI` | 14-day Relative Strength Index (division-by-zero guarded) |
| `MACD` | EMA(12) − EMA(26) |
| `MACD_Signal` | 9-day EMA of MACD |
| `BB_Upper` | 20-day SMA + 2× standard deviation |
| `BB_Lower` | 20-day SMA − 2× standard deviation |

---

## Tabs

| Tab | Content |
|---|---|
| 📊 Price Chart | Price history, BB overlay, RSI panel, volume, test predictions, future forecast + uncertainty band. Range selector buttons (1M / 3M / 6M / 1Y / 2Y / ALL) and a rangeslider for zooming. Hover shows the full date. |
| 📉 Model Performance | Train vs. val loss curves with best-epoch marker, plus directional accuracy, MAE, test sample count, and best val loss metric cards |
| 📈 MACD | MACD histogram, MACD line, and Signal line with zero-line reference |
| ℹ️ About | Feature summary and disclaimer |

---

## Disclaimer

> This tool is for **educational purposes only**. Stock market predictions are inherently uncertain. Do not use Ticker-Teller as sole financial advice.
