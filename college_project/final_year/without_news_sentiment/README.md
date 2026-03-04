# 📈 Ticket-Teller

> LSTM time-series forecasting × Monte Carlo uncertainty estimation

A professional stock prediction dashboard built with PyTorch and Streamlit, styled with the Ticker-Teller dark finance theme.

---

## Features

- **Multi-variate LSTM** — trains on OHLCV data enriched with SMA(10), SMA(50), and RSI(14)
- **Monte Carlo Dropout** — runs 50 stochastic forward passes per forecast step to produce calibrated uncertainty bands
- **Early stopping** — halts training when validation loss plateaus and restores the best-epoch weights automatically
- **ReduceLROnPlateau** — halves the learning rate when progress stalls
- **Interactive chart** — price history, test-set predictions, future forecast, and volume bars in a single Plotly figure
- **AI signal badge** — Strong Buy / Buy / Hold / Sell / Strong Sell derived from the forecast direction

---

## Project Structure

```
ticket-teller/
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

<table>
  <thead>
    <tr>
      <th>File</th>
      <th>What lives here</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>app.py</code></td>
      <td>Streamlit page config, button handler, pipeline orchestration</td>
    </tr>
    <tr>
      <td><code><u>src/</u>data.py</code></td>
      <td><code>fetch_data</code>, <code>add_technical_features</code>, <code>build_sequences</code>, <code>split_data</code>, <code>inverse_close</code></td>
    </tr>
    <tr>
      <td><code><u>src/</u>model.py</code></td>
      <td><code>LSTMModel</code>, <code>StockDataset</code>, <code>make_loaders</code>, <code>train_model</code>, <code>predict_test_set</code>, <code>monte_carlo_forecast</code></td>
    </tr>
    <tr>
      <td><code><u>src/</u>charts.py</code></td>
      <td><code>build_price_chart</code> — returns a Plotly <code>Figure</code>, knows nothing about Streamlit</td>
    </tr>
    <tr>
      <td><code><u>src/</u>ui.py</code></td>
      <td><code>inject_css</code>, <code>render_header</code>, <code>render_sidebar</code>, <code>section_header</code>, <code>signal_badge</code>, <code>split_pills</code>, <code>render_about_tab</code></td>
    </tr>
  </tbody>
</table>

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

**1. Clone the repository**

```bash
git clone https://github.com/your-username/ticket-teller.git
cd ticket-teller
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the app**

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Usage

<table>
  <thead>
    <tr>
      <th>Sidebar control</th>
      <th>What it does</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Ticker Symbol</strong></td>
      <td>Any valid Yahoo Finance ticker, e.g. <code>AAPL</code>, <code>TSLA</code>, <code>MSFT</code></td>
    </tr>
    <tr>
      <td><strong>Historical Data (Days)</strong></td>
      <td>How far back to fetch OHLCV data. Minimum recommended: <strong>1460 days (4 years)</strong></td>
    </tr>
    <tr>
      <td><strong>Lookback Sequence (Days)</strong></td>
      <td>Number of past trading days the LSTM sees at each step (default 60)</td>
    </tr>
    <tr>
      <td><strong>Forecast Horizon (Days)</strong></td>
      <td>How many business days ahead to forecast (default 5)</td>
    </tr>
    <tr>
      <td><strong>Max Training Epochs</strong></td>
      <td>Upper bound on training iterations (early stopping may halt before this)</td>
    </tr>
    <tr>
      <td><strong>Early Stopping Patience</strong></td>
      <td>Epochs to wait for validation loss improvement before halting (default 10)</td>
    </tr>
  </tbody>
</table>

### Tips for best results

- Use at least **3–5 years** of history. Short histories produce tiny val/test sets that cause premature early stopping.
- If early stopping fires before epoch 20, increase the historical data period first before tuning patience.
- The Monte Carlo uncertainty band widens with longer forecast horizons — treat multi-week forecasts as directional guidance only.

---

## Data Split

The dataset is divided into three non-overlapping, temporally ordered sets:

```
|── 70% Train ──|── 15% Val ──|── 15% Test ──|
```

A minimum of 30 samples is enforced for both val and test regardless of dataset size.

---

## Model Architecture

```
Input  (batch, seq_length, 8 features)
  └─ LSTM  ×2 layers, hidden_size=64, dropout=0.2
       └─ Dropout(0.2)
            └─ Linear(64 → 1)
Output (batch, 1)  — scaled Close price
```

Loss function: `MSELoss`  
Optimiser: `Adam(lr=0.001)`  
LR scheduler: `ReduceLROnPlateau(factor=0.5, patience=5)`

---

## Disclaimer

> This tool is for **educational purposes only**. Stock market predictions are inherently uncertain. Do not use ticket-teller AI as sole financial advice.
