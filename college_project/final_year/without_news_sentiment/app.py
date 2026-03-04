"""
app.py — Ticker-Teller v2  |  Entry point
Run with:  streamlit run app.py

Module layout
─────────────
app.py          ← you are here (orchestration only)
src/
  data.py       ← fetch_data, feature engineering, sequencing, splits
  model.py      ← LSTMModel, StockDataset, train_model, inference helpers
  charts.py     ← Plotly figure builders
  ui.py         ← CSS injection, sidebar widgets, reusable HTML components
"""
import numpy as np
import pandas as pd
import torch
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

from src.data   import (fetch_data, add_technical_features, build_sequences,
                         split_data, inverse_close, FEATURE_COLS)
from src.model  import (make_loaders, train_model,
                         predict_test_set, monte_carlo_forecast)
from src.charts import build_price_chart
from src.ui     import (inject_css, render_header, render_sidebar,
                         section_header, signal_badge, split_pills, render_about_tab)

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="Ticker-Teller",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_header()

cfg = render_sidebar()   # returns dict with ticker, period, seq_length, …

# ── Run button ─────────────────────────────────────────────────────────────────
if st.button(f"🚀  Run Analysis for  {cfg['ticker']}", type="primary", use_container_width=True):

    ticker        = cfg["ticker"]
    period        = cfg["period"]
    seq_length    = cfg["seq_length"]
    forecast_days = cfg["forecast_days"]
    epochs        = cfg["epochs"]
    patience      = cfg["patience"]

    if not ticker:
        st.error("Please enter a ticker symbol.")
        st.stop()

    # 1 — Fetch ────────────────────────────────────────────────────────────────
    with st.spinner(f"📥  Fetching market data for {ticker}…"):
        df_raw = fetch_data(ticker, period)

    if df_raw is None or df_raw.empty:
        st.error(f"No data found for **{ticker}**. Check the symbol and try again.")
        st.stop()

    st.success(f"✅  Loaded **{len(df_raw):,}** trading days for {ticker}")

    # 2 — Feature engineering ──────────────────────────────────────────────────
    df = add_technical_features(df_raw)
    df = df.dropna(subset=FEATURE_COLS)[FEATURE_COLS]

    if len(df) < seq_length + 10:
        st.error("Not enough data. Reduce the lookback sequence or increase historical period.")
        st.stop()

    # 3 — Scale & build sequences ──────────────────────────────────────────────
    scaler      = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df)

    X, y = build_sequences(scaled_data, seq_length)

    (X_train, y_train), (X_val, y_val), (X_test, y_test), split, val_split = split_data(X, y)

    train_loader, val_loader, test_loader = make_loaders(
        X_train, y_train, X_val, y_val, X_test, y_test
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 4 — Train ────────────────────────────────────────────────────────────────
    section_header("🧠 Model Training")
    model = train_model(
        train_loader, val_loader,
        input_size = len(FEATURE_COLS),
        epochs     = epochs,
        patience   = patience,
        device     = device,
    )

    # 5 — Test-set predictions ─────────────────────────────────────────────────
    preds_scaled, actuals_scaled = predict_test_set(model, test_loader, device)
    pred_prices   = inverse_close(preds_scaled,   scaler, len(FEATURE_COLS))
    actual_prices = inverse_close(actuals_scaled, scaler, len(FEATURE_COLS))

    # 6 — Monte Carlo future forecast ──────────────────────────────────────────
    mc_raw = monte_carlo_forecast(model, scaled_data, seq_length, forecast_days, device)

    future_dates                = pd.date_range(start=df_raw.index[-1], periods=forecast_days + 1, freq="B")[1:]
    price_range                 = float(df_raw["Close"].max()) - float(df_raw["Close"].min())
    future_means, future_stds   = [], []

    for item in mc_raw:
        future_means.append(float(inverse_close(np.array([item["mean"]]), scaler, len(FEATURE_COLS))[0]))
        future_stds.append(float(item["std"] * price_range))

    # 7 — Derived metrics ──────────────────────────────────────────────────────
    last_price = float(df_raw["Close"].iloc[-1])
    next_price = float(future_means[0]) if future_means else float(pred_prices[-1])
    pct_change = (next_price - last_price) / last_price * 100
    volatility = float(df_raw["Close"].pct_change().std() * np.sqrt(252))

    correct = sum(
        1 for i in range(1, len(pred_prices))
        if (pred_prices[i] - pred_prices[i-1]) * (actual_prices[i] - actual_prices[i-1]) > 0
    )
    dir_acc = (correct / (len(pred_prices) - 1)) * 100 if len(pred_prices) > 1 else 0

    if   pct_change >  1.0: signal, badge_class = "STRONG BUY",  "badge-bull"
    elif pct_change >  0.0: signal, badge_class = "BUY",         "badge-bull"
    elif pct_change < -1.0: signal, badge_class = "STRONG SELL", "badge-bear"
    else:                   signal, badge_class = "HOLD",        "badge-neut"

    # 8 — Render summary ───────────────────────────────────────────────────────
    section_header("📊 Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CURRENT PRICE",              f"${last_price:.2f}")
    c2.metric(f"FORECAST (+{forecast_days}d)", f"${next_price:.2f}", f"{pct_change:+.2f}%")
    c3.metric("DIRECTIONAL ACCURACY",       f"{dir_acc:.1f}%")
    c4.metric("ANN. VOLATILITY",            f"{volatility:.2%}")

    signal_badge(signal, badge_class)
    split_pills(val_split, split - val_split, len(X_test))

    # 9 — Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊  PRICE CHART", "📉  MODEL PERFORMANCE", "ℹ️  ABOUT"])

    with tab1:
        test_start_idx = seq_length + split
        test_idx       = df.index[test_start_idx: test_start_idx + len(actual_prices)]

        fig = build_price_chart(
            df_raw        = df_raw,
            test_idx      = test_idx,
            actual_prices = actual_prices,
            pred_prices   = pred_prices,
            future_dates  = future_dates,
            future_means  = future_means,
            future_stds   = future_stds,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        section_header("Test Set Performance")
        c1, c2, c3 = st.columns(3)
        c1.metric("DIRECTIONAL ACCURACY", f"{dir_acc:.2f}%")
        c2.metric("TEST SAMPLES",         str(len(pred_prices)))
        c3.metric("FORECAST HORIZON",     f"{forecast_days}d")
        st.info(
            "Loss curves are shown in the training console above. "
            "Early stopping restores best-epoch weights automatically."
        )

    with tab3:
        render_about_tab()
