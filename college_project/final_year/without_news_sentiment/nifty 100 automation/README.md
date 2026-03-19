# 📈 NIFTY 100 Tracker

> 🔗 **GitHub Repository:**
> [nullbeing72/Projects — final_year / without_news_sentiment / type 2](https://github.com/nullbeing72/Projects/tree/main/college_project/final_year/without_news_sentiment/type%202)

---

| Mode | Entry point | Who it is for |
|---|---|---|
| **Automated Tracker** | `python3 nifty100_tracker.py` | Researchers who want daily predictions for all 100 NIFTY 100 companies written to structured Excel workbooks, running unattended for 30 days |

---

## Repository Structure

```
ticker-teller/
│
├── app.py                     ← Streamlit web application entry point
│
├── src/
│   ├── __init__.py
│   ├── data.py                ← Data fetching + 22-feature engineering
│   ├── model.py               ← HybridModel + training + MC forecast
│   ├── charts.py              ← Plotly chart builders
│   └── ui.py                  ← Streamlit CSS + sidebar + UI components
│
├── nifty100_tracker.py        ← Automated 30-day CLI pipeline (latest version)
│
├── requirements.txt           ← All pip dependencies
│
├── docs/
│   ├── README_v1.md           ← Tracker v1 documentation
│   └── README_v2.md           ← Tracker v2 documentation (Smart Retry)
│
├── workbooks/                 ← AUTO-CREATED — Excel output files
├── logs/                      ← AUTO-CREATED — daily + master logs
└── state/                     ← AUTO-CREATED — checkpoint + ticker fixes
```

---

## Quick Start

### Automated tracker (CLI, all 100 NIFTY stocks)

```bash
# 1. Clone the repository
git clone https://github.com/nullbeing72/Projects.git
cd "Projects/college_project/final_year/without_news_sentiment/type 2"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test on a few tickers first
python3 nifty100_tracker.py --once --tickers RELIANCE.NS TCS.NS HDFCBANK.NS

# 4. Run all 100 tickers once
python3 nifty100_tracker.py --once

# 5. Start the full 30-day scheduled automation (fires at 18:00 IST daily)
python3 nifty100_tracker.py
```

---

## Requirements

Python 3.10 or newer. Install all dependencies with:

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| `torch` | Neural network training and inference |
| `numpy` | Array operations and log-return math |
| `pandas` | DataFrames and date indexing |
| `scikit-learn` | `MinMaxScaler` for feature normalisation |
| `yfinance` | OHLCV + SPY market data from Yahoo Finance |
| `plotly` | Interactive charts in the Streamlit app |
| `streamlit` | Web application framework |
| `openpyxl` | Excel workbook creation and formatting (tracker only) |
| `requests` | Yahoo Finance search API for auto symbol correction (tracker v2 only) |

---

## The Two Tracker Versions

The automated tracker has two versions. Both are fully functional — v2 is a
drop-in replacement for v1 with additional resilience features.

| Feature | v1 | v2 |
|---|---|---|
| Automated 30-day scheduling | ✅ | ✅ |
| Excel workbook per company | ✅ | ✅ |
| Resumability via checkpoint | ✅ | ✅ |
| Per-ticker retry on failure | ✅ Basic (3× fixed delay) | ✅ Advanced |
| Auto symbol correction via web search | ❌ | ✅ |
| Exponential backoff (TCP-style) | ❌ | ✅ |
| New listing support (< 252 days history) | ❌ Crashes | ✅ NaN fill + seq_length reduction |
| Streamlit warning suppression | ❌ | ✅ |
| Persistent fix registry (`ticker_fixes.json`) | ❌ | ✅ |

See [`docs/README_v1.md`](docs/README_v1.md) and
[`docs/README_v2.md`](docs/README_v2.md) for full documentation of each version.

---

## Excel Output Format

Each company gets its own `.xlsx` file under `workbooks/`. One row is appended
per daily run, never overwriting previous data.

| Column | Content |
|---|---|
| Date | `YYYY-MM-DD` |
| Ticker | Yahoo Finance symbol, e.g. `RELIANCE.NS` |
| Price Features | All 16 feature values at the last bar — `key=value \| …` |
| Quant Factor Features | All 6 factor values: Beta, Alpha, Momentum, Sharpe, VolRatio, MktReturn |
| Actual Price | Last known close from Yahoo Finance |
| Predicted Price | MC-Dropout mean of 100 forward passes |
| Error (%) | `ABS(((Actual − Predicted) / Actual) × 100)` — green if model undershot, red if overshot |

After 30 days each workbook holds a full month of daily predictions — a
ready-made dataset for evaluating model accuracy over time.

---

## Known Ticker Fixes (NIFTY 100)

Several NIFTY 100 companies have changed their Yahoo Finance symbol due to
rebrands, demergers, or name changes. The tracker v2 auto-discovers and
persists these fixes. Known corrections as of March 2026:

| Old Symbol ❌ | Correct Symbol ✅ | Reason |
|---|---|---|
| `INFOSYS.NS` | `INFY.NS` | Yahoo Finance uses the short-form symbol |
| `ZOMATO.NS` | `ETERNAL.NS` | Rebranded to Eternal Limited — March 2025 |
| `ADANITRANS.NS` | `ADANIENSOL.NS` | Rebranded to Adani Energy Solutions — July 2023 |
| `TATAMOTORS.NS` | `TMPV.NS` + `TMCV.NS` | Demerged into passenger vehicles and commercial vehicles — October 2025 |

---

## Disclaimer

> **For educational and research purposes only.**
>
> Ticker-Teller's predictions are probabilistic estimates based on historical
> patterns. They are **not** financial advice and should **not** be used as the
> sole basis for investment decisions. Past model accuracy does not guarantee
> future performance.
>
> **Always consult a qualified financial advisor before making investment
> decisions.**

---

*Linked to: [github.com/nullbeing72/Projects](https://github.com/nullbeing72/Projects/tree/main/college_project/final_year/without_news_sentiment/type%202)*
