# 📈 Ticker-Teller

> **Quantitative stock forecasting powered by a dual-branch deep learning architecture —
> CNN → BiLSTM → Cross-Attention — with Monte Carlo uncertainty estimation.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Feature Engineering](#feature-engineering)
4. [Model Design](#model-design)
5. [Training Pipeline](#training-pipeline)
6. [Inference & Forecasting](#inference--forecasting)
7. [Project Structure](#project-structure)
8. [Installation](#installation)
9. [Usage](#usage)
10. [Configuration Reference](#configuration-reference)
11. [Design Decisions](#design-decisions)
12. [Limitations & Disclaimer](#limitations--disclaimer)

---

## Overview

Ticker-Teller is a Streamlit web application that downloads historical OHLCV data for any
publicly traded ticker, engineers 22 technical and quantitative features, trains a hybrid
deep learning model, and produces:

- **Test-set predictions** with per-step price reconstruction (gap-free, drift-free)
- **Multi-day Monte Carlo forecasts** with calibrated uncertainty bands
- **Interactive Plotly charts** — price, RSI, volume, MACD, and training loss curves
- **Summary metrics** — directional accuracy, MAE, annualised volatility, and a signal badge

The core insight driving the architecture is that stock price movements have **two independent
information sources** that require different inductive biases to process:

| Source | Signal type | Branch |
|---|---|---|
| OHLCV + technical indicators | Local chart patterns, momentum, volatility | Price branch (CNN → BiLSTM → Self-Attention) |
| CAPM beta, alpha, Sharpe, momentum factor | Market regime, risk-adjusted performance | Factor branch (BiLSTM → Cross-Attention) |

---

## Architecture

```
Input  (B, T, 22)
  │
  ├─── x_price  (B, T, 16) ─────────────────────────────────────────-┐
  │    TemporalConvBlock                                             │
  │      ├─ Conv1d(kernel=3)  ─┐                                     │
  │      └─ Conv1d(kernel=5)  ─┴─ Concat → Conv1d(1×1) → GELU        │
  │      └─ Residual shortcut                                        │
  │    BiLSTM(hidden=128, layers=2, bidirectional=True)              │
  │    MultiHeadSelfAttention(d=256, heads=4)                        │
  │    → (B, T, 256)                                                 │
  │                                                                  ├──► CrossAttention
  └─── x_factor (B, T, 6) ──────────────────────────────────────┐    │    (price queries
       Linear(6 → 32) → GELU                                    │    │     factor K/V)
       BiLSTM(hidden=32, layers=1, bidirectional=True)          │    │         │
       FactorSelfAttention(d=64, heads=4)                       │    │    TemporalAttnPool
       → (B, T, 64)                                             │    │    (learned weights
       ─────────────────────────────────────────────────────────┘    ┘     over time steps)
                                                                                  │
                                                                             FC Head
                                                                          Linear(256→128)
                                                                              GELU
                                                                          Linear(128→1)
                                                                                  │
                                                                        scalar log return
```

### Why this architecture?

**TemporalConvBlock (dual-kernel CNN)**
Two parallel 1-D convolutions with kernel sizes 3 and 5 scan the price window simultaneously.
Kernel-3 picks up 3-day micro-patterns (doji candles, engulfing bars); kernel-5 catches
5-day consolidations and breakouts. Their outputs are concatenated and fused via a 1×1
convolution. A residual shortcut carries raw input features forward so the LSTM never loses
the original signal.

**Bidirectional LSTM**
The CNN's enriched feature maps pass into a stacked BiLSTM. The backward pass means context
from later time steps informs earlier ones — a late-window volatility spike can retroactively
up-weight an earlier chart pattern.

**Multi-Head Self-Attention**
Applied over the time dimension after the LSTM so each time step can attend to every other.
The model learns "this day three weeks ago looks a lot like the current setup" without relying
on the LSTM's hidden state to propagate that signal across many gates.

**Temporal Attention Pooling**
A linear layer scores every time step; a softmax produces a probability distribution over
steps; the weighted sum collapses `(B, T, 2H)` to `(B, 2H)`. More expressive than always
taking the last hidden state — important events anywhere in the window get high weight.

**Factor Branch + Cross-Attention**
The six quantitative factors are projected to 32 dimensions and processed by a lightweight
BiLSTM. The price branch then queries the factor branch via cross-attention: each
price time-step asks "what does the quant regime say right now?" A high-beta stock in
a rising-vol period will receive a very different cross-attention signal than the same
chart pattern in a quiet market, even if the OHLCV looks identical.

---

## Feature Engineering

### Price Branch — 16 features

| Feature | Category | Description |
|---|---|---|
| Open, High, Low, Close, Volume | OHLCV | Raw market data |
| SMA_10, SMA_50 | Trend | 10-day and 50-day simple moving averages |
| MACD | Momentum | EMA(12) − EMA(26) |
| MACD_Signal | Momentum | EMA(9) of MACD |
| RSI | Momentum | 14-day Relative Strength Index (÷ 0 guarded) |
| ROC_10 | Momentum | 10-day Rate of Change (%) |
| Stoch_K | Momentum | 14-day Stochastic %K oscillator |
| BB_Upper, BB_Lower | Volatility | 20-day Bollinger Bands (±2σ) |
| ATR | Volatility | 14-day Average True Range |
| OBV_norm | Volume momentum | On-Balance Volume, z-score normalised (20-day rolling) |

### Factor Branch — 6 features

| Feature | Description | Why it matters |
|---|---|---|
| **Beta_60** | Rolling 60-day OLS beta vs SPY | Measures how much the stock amplifies market moves. Beta > 1 = aggressive; < 1 = defensive. |
| **Alpha_60** | Jensen's alpha, annualised | Excess return beyond what CAPM would predict. Falling alpha often precedes price breakdown. |
| **Momentum_12_1** | 252-day return minus 21-day return (Jegadeesh-Titman) | The most empirically robust return predictor in academic finance — captures medium-term momentum while excluding the short-term reversal effect. |
| **Sharpe_60** | Rolling 60-day Sharpe ratio | Risk-adjusted performance quality. A declining Sharpe warns before price follows. |
| **Vol_Ratio** | 10-day realised vol ÷ 60-day realised vol | Values > 1 signal a risk-off regime; the model learns to widen uncertainty and moderate directional confidence. |
| **Mkt_Return** | SPY daily log return | Contemporaneous macro direction — tells the model what the broad market did that day. |

### Prediction Target

The model predicts **log returns** `r[t] = log(Close[t] / Close[t-1])` rather than
scaled closing prices.

**Why this matters:** Scaled close prices are non-stationary — they drift over time with
changing mean and variance. A model minimising MSE on a non-stationary target discovers
that predicting near the running mean minimises loss, producing the classic **flat-line
collapse**. Log returns are stationary, centred near zero, and force the model to learn
actual directional movements.

---

## Model Design

### Loss Function — `CombinedLoss`

```
L = HuberLoss(δ=0.01) + 0.4 × DirectionalPenalty
```

**Huber loss (δ = 0.01)**
Behaves like L2 for `|error| < 0.01` (smooth near zero, where daily log returns
cluster) and like L1 for larger errors (robust to outlier days with extreme moves).

**Directional penalty**
```python
relu(−pred × target)
```
= 0 when predicted and actual signs agree, positive when they disagree — scaled
by how confidently wrong the prediction is. Plain MSE/Huber never penalises
wrong-direction predictions; this term makes direction an explicit training objective.

### Optimiser — AdamW

Decoupled weight decay (`weight_decay=1e-4`) regularises the larger parameter count
of the dual-branch model more effectively than L2-regularised Adam.

### Learning Rate Schedule — CosineAnnealingWarmRestarts

```
T_0=10, T_mult=2, η_min=1e-6
```

Periodically resets the learning rate to its initial value with an exponentially
growing restart interval (10 → 20 → 40 epochs). This helps the optimiser escape
local minima that `ReduceLROnPlateau` locks it into by cutting the LR too
aggressively.

### Regularisation

| Technique | Where applied | Purpose |
|---|---|---|
| Dropout (p=0.2) | CNN, LSTM inter-layer, attention, FC head | Prevent overfitting |
| Gradient clipping (norm=1.0) | All parameters | Prevent exploding gradients in deep LSTMs |
| BatchNorm | After each Conv1d | Stabilise CNN layer activations |
| LayerNorm | After each attention block | Stabilise attention layer activations |
| Early stopping | Val loss | Halt training when generalisation stops improving |

---

## Training Pipeline

```
Raw OHLCV
    │
    ├─ add_technical_features()    # +11 indicators → 16 price features
    ├─ add_quant_features(spy)     # +6 factor features → 22 total
    │
    ├─ MinMaxScaler(0,1)           # scale all 22 features
    │
    ├─ build_sequences()           # sliding window (seq_length, 22)
    │                              # target: log return (stationary)
    │
    ├─ split_data()                # 70% train / 15% val / 15% test
    │                              # minimum 30 samples per split enforced
    │
    └─ train_model()
           │
           ├─ CombinedLoss (Huber + directional penalty)
           ├─ AdamW (lr=1e-3, wd=1e-4)
           ├─ CosineAnnealingWarmRestarts (T0=10, Tmult=2)
           ├─ Gradient clipping (max_norm=1.0)
           └─ Early stopping (patience configurable)
```

### Data splits

| Split | Ratio | Minimum | Purpose |
|---|---|---|---|
| Train | 70% | 30 samples | Parameter updates |
| Validation | 15% | 30 samples | Early stopping, LR scheduling |
| Test | 15% | 30 samples | Final evaluation (never seen during training) |

---

## Inference & Forecasting

### Test-set price reconstruction (gap-free)

Predicted prices are reconstructed **per-step**, anchored to the actual previous
close at each step:

```python
pred_price[t] = actual_close[t-1] × exp(pred_log_return[t])
```

This eliminates drift entirely. With cumulative-sum reconstruction
(`returns_to_prices`), one wrong prediction shifts the anchor for every subsequent
step — by day 50 the predicted line can float $20 above actuals even if directional
accuracy is high. Per-step anchoring means only the one-step movement differs from
reality, never the price level.

### Monte Carlo Dropout Forecast

```
model.train()   # dropout stays active
for n_samples:
    sample[i] = model(window)

mean_return = mean(samples)
std_return  = std(samples)
next_price  = current_price × exp(mean_return)
price_std   = current_price × std_return      # price-space uncertainty
```

Uncertainty comes from **all dropout layers** simultaneously — CNN, LSTM
inter-layer, attention, and FC head — not just the final layer. The window
shifts forward at each step, inserting the predicted close at the Close
position (index 3) in the scaled input.

---

## Project Structure

```
project/
├── app.py                    # Entry point — orchestration only
├── src/
│   ├── __init__.py
│   ├── data.py               # Data fetching & feature engineering
│   │     fetch_data()            ← Yahoo Finance OHLCV download
│   │     fetch_market_data()     ← SPY download for quant factors
│   │     add_technical_features() ← 16 price features
│   │     add_quant_features()    ← 6 factor features (CAPM, Sharpe…)
│   │     build_sequences()       ← sliding window → log-return targets
│   │     returns_to_prices()     ← cumulative log-return reconstruction
│   │     split_data()            ← 70/15/15 temporal split
│   │
│   ├── model.py              # Neural network, loss, training, inference
│   │     TemporalConvBlock        ← dual-kernel CNN + residual
│   │     SelfAttentionBlock       ← MHA + residual + LayerNorm
│   │     CrossAttentionBlock      ← price queries factor K/V
│   │     QuantHybridModel         ← full dual-branch architecture
│   │     CombinedLoss             ← Huber + directional penalty
│   │     train_model()            ← training loop with early stopping
│   │     predict_test_set()       ← batch inference → log returns
│   │     monte_carlo_forecast()   ← recursive MC-Dropout forecast
│   │
│   ├── charts.py             # Plotly figure builders
│   │     build_price_chart()      ← price + RSI + volume (3 subplots)
│   │     build_loss_chart()       ← train vs val loss curves
│   │     build_macd_chart()       ← MACD + signal + histogram
│   │
│   └── ui.py                 # Streamlit CSS + reusable components
│         inject_css()             ← dark finance theme
│         render_header()          ← gradient title banner
│         render_sidebar()         ← all config widgets → dict
│         render_about_tab()       ← architecture documentation tab
│
└── requirements.txt
```

---

## Installation

### Prerequisites

- Python 3.10 or later
- pip

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

### `requirements.txt`

```
streamlit>=1.32.0
torch>=2.1.0
numpy>=1.26.0
pandas>=2.1.0
scikit-learn>=1.4.0
yfinance>=0.2.36
plotly>=5.19.0
```

> **GPU support:** PyTorch will automatically use CUDA if available.
> Install the CUDA-enabled build of PyTorch from [pytorch.org](https://pytorch.org/get-started/locally/)
> for significantly faster training on large epoch counts.

---

## Usage

1. Open the app in your browser (default: `http://localhost:8501`)
2. Enter a ticker symbol in the sidebar (e.g. `AAPL`, `TSLA`, `BTC-USD`)
3. Configure the model parameters (see below)
4. Click **🚀 Run Analysis**

The app will:
1. Download OHLCV data for your ticker + SPY from Yahoo Finance
2. Engineer all 22 features
3. Train the model (progress bar + live epoch loss in the UI)
4. Display the price chart with test predictions and forecast
5. Show RSI, volume, MACD, training loss curves, and summary metrics

---

## Configuration Reference

All parameters are set via the sidebar. Changes take effect on the next Run.

| Parameter | Default | Range | Description |
|---|---|---|---|
| **Ticker Symbol** | `AAPL` | Any valid Yahoo Finance symbol | Stock or ETF ticker (crypto: `BTC-USD`) |
| **Historical Data** | `730` days | 365 – 1825 | How many days of history to download |
| **Lookback Sequence** | `60` days | 10 – 120 | Length of the sliding input window fed to the model |
| **Forecast Horizon** | `5` days | 1 – 30 | How many business days ahead to forecast |
| **Max Epochs** | `50` | 10 – 200 | Upper bound on training epochs (early stopping may trigger sooner) |
| **Patience** | `10` | 3 – 20 | Early stopping patience in epochs |
| **BiLSTM Hidden Size** | `128` | 32, 64, 128, 256 | Hidden units per direction in both LSTM branches |
| **CNN Channels** | `64` | 32, 64, 128 | Output channels of the TemporalConvBlock |
| **Attention Heads** | `4` | 2, 4, 8 | Number of attention heads (must divide 2 × hidden size) |
| **Dropout Rate** | `0.2` | 0.0 – 0.5 | Applied to CNN, LSTM, attention, and FC head |

### Recommended settings by use case

| Use case | Hidden | CNN Ch. | Heads | Epochs | Notes |
|---|---|---|---|---|---|
| Quick exploration | 64 | 32 | 2 | 30 | Trains in ~1 min on CPU |
| Balanced | 128 | 64 | 4 | 50 | Default — good quality/speed trade-off |
| Best quality | 256 | 128 | 8 | 150 | GPU recommended; use patience=15 |
| High volatility stocks | 128 | 64 | 4 | 50 | Increase historical data to 1825 days |

---

## Design Decisions

### Why log returns instead of scaled prices?

Scaled close prices are non-stationary — their mean and variance drift over time.
An MSE-minimising model on non-stationary targets converges to predicting the running
mean, producing a **flat pink line** regardless of architecture sophistication. Log
returns `r[t] = log(P[t]/P[t-1])` are stationary and centred near zero. The model
must predict actual movement or incur high loss.

### Why per-step anchoring for test predictions?

Cumulative-sum price reconstruction (`price[t] = P₀ × exp(Σrᵢ)`) compresses errors
across the entire test window. One miscalibrated prediction shifts every subsequent
price. Per-step anchoring (`price[t] = actual[t-1] × exp(r̂[t])`) limits each
prediction's error to a single step — the chart tracks actuals faithfully even with
moderate directional accuracy.

### Why cross-attention instead of concatenation?

Simple concatenation of price and factor features treats both streams equally at every
time step. Cross-attention lets the price representations selectively query the factor
context — a high-beta stock in a high-vol regime gets a completely different
conditioning signal from the same chart pattern in a calm market. The asymmetric
query/key-value structure is essential: price movements need to be conditioned on
regime, not averaged with it.

### Why CosineAnnealingWarmRestarts instead of ReduceLROnPlateau?

`ReduceLROnPlateau` halves the LR whenever validation loss stagnates, which locks the
model into local minima on non-convex loss surfaces. Cosine warm restarts periodically
reset the LR to its initial value with a growing interval (10 → 20 → 40 epochs),
allowing the optimiser to escape and explore wider basins of attraction.

---

## Limitations & Disclaimer

> ⚠️ **This application is for educational and research purposes only.**
> Nothing produced by this software constitutes financial, investment, or trading advice.
> Do not make financial decisions based solely on model outputs.

### Known limitations

- **Look-ahead bias:** All features are computed using only past data, but the train/val/test
  split is not walk-forward validated. Production trading systems require expanding-window
  or rolling-window cross-validation.

- **Market regime shifts:** The model is trained on a fixed historical window. Black-swan
  events (pandemics, flash crashes, regulatory changes) can invalidate learned patterns
  overnight. The model has no mechanism to detect that it is operating out-of-distribution.

- **Factor staleness:** During MC forecasting, factor features (Beta, Sharpe, Vol_Ratio etc.)
  are held constant at their last observed values. For short horizons (1–5 days) this is
  a reasonable approximation; for longer horizons (10–30 days) these values may be stale.

- **Execution costs:** The directional accuracy metric does not account for bid-ask spreads,
  slippage, or transaction costs. A strategy that looks profitable on paper may not be
  after costs.

- **Single-asset modelling:** The model has no cross-asset information beyond SPY.
  Sector dynamics, correlations, and relative strength signals are not captured.

- **Yahoo Finance data quality:** The data source may have adjusted-price anomalies,
  survivorship bias for delisted stocks, and occasional gaps or errors.

---

*Built with PyTorch, Streamlit, and Plotly.*
