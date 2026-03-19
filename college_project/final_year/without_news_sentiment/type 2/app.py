"""
app.py — Ticker-Teller v5  |  Entry point
Run with:  streamlit run app.py

Module layout
─────────────
app.py          ← you are here (orchestration only)
src/
  data.py       ← fetch_data, fetch_market_data(SPY), 22-feature engineering,
                   add_quant_features (CAPM beta/alpha, momentum, Sharpe, vol regime),
                   log-return sequences
  model.py      ← QuantHybridModel (Price CNN/BiLSTM + Factor BiLSTM + CrossAttn),
                   CombinedLoss (Huber + directional penalty)
  charts.py     ← build_price_chart, build_loss_chart, build_macd_chart  [unchanged]
  ui.py         ← CSS injection, sidebar (+cnn_channels, +num_heads)     [unchanged]
"""
import numpy as np
import pandas as pd
import torch
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

from src.data   import (fetch_data, fetch_market_data,
                         add_technical_features, add_quant_features,
                         build_sequences, split_data,
                         returns_to_prices, FEATURE_COLS,
                         N_PRICE_FEATURES, N_FACTOR_FEATURES)
from src.model  import (make_loaders, train_model,
                         predict_test_set, monte_carlo_forecast)
from src.charts import build_price_chart, build_loss_chart, build_macd_chart
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
    hidden_size   = cfg["hidden_size"]
    cnn_channels  = cfg["cnn_channels"]
    num_heads     = cfg["num_heads"]
    dropout       = cfg["dropout"]

    if not ticker:
        st.error("Please enter a ticker symbol.")
        st.stop()

    # 1 — Fetch ────────────────────────────────────────────────────────────────
    with st.spinner(f"📥  Fetching market data for {ticker}…"):
        df_raw = fetch_data(ticker, period)

    if df_raw is None or df_raw.empty:
        st.error(f"No data found for **{ticker}**. Check the symbol and try again.")
        st.stop()

    with st.spinner("📥  Fetching SPY market data for quant factors…"):
        market_df = fetch_market_data(period)

    if market_df is None or market_df.empty:
        st.warning("Could not fetch SPY data — factor branch will use zeros. Check your connection.")
        # Create a dummy market_df aligned to df_raw so the pipeline still runs
        market_df = df_raw[['Close']].copy()

    st.success(f"✅  Loaded **{len(df_raw):,}** trading days for {ticker}")

    # 2 — Feature engineering ──────────────────────────────────────────────────
    df = add_technical_features(df_raw)
    df = add_quant_features(df, market_df)
    df = df.dropna(subset=FEATURE_COLS)[FEATURE_COLS]

    if len(df) < seq_length + 10:
        st.error("Not enough data. Reduce the lookback sequence or increase historical period.")
        st.stop()

    # 3 — Scale & build sequences ──────────────────────────────────────────────
    scaler      = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df)

    raw_close = df['Close'].values   # unscaled — needed for log-return targets
    X, y = build_sequences(scaled_data, raw_close, seq_length)

    (X_train, y_train), (X_val, y_val), (X_test, y_test), split, val_split = split_data(X, y)

    train_loader, val_loader, test_loader = make_loaders(
        X_train, y_train, X_val, y_val, X_test, y_test
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 4 — Train ────────────────────────────────────────────────────────────────
    section_header("🧠 Model Training")
    model, loss_history = train_model(
        train_loader, val_loader,
        input_size   = len(FEATURE_COLS),
        epochs       = epochs,
        patience     = patience,
        device       = device,
        hidden_size  = hidden_size,
        dropout      = dropout,
        cnn_channels = cnn_channels,
        num_heads    = num_heads,
    )

    # 5 — Test-set predictions ─────────────────────────────────────────────────
    pred_log_returns, actual_log_returns = predict_test_set(model, test_loader, device)

    test_start_idx   = seq_length + split
    test_start_price = float(df['Close'].iloc[test_start_idx - 1])

    # Actual prices: single anchor is fine — ground-truth returns cumulate correctly.
    actual_prices = returns_to_prices(actual_log_returns, test_start_price)

    # Predicted prices: RE-ANCHOR each step to the ACTUAL previous close.
    # Cumsum of predicted returns compounds errors → drifting gap vs actuals.
    # Per-step anchor:  pred_price[t] = actual_close[t-1] * exp(pred_return[t])
    # This removes drift entirely: only the one-step movement differs, never level.
    actual_close_arr = df['Close'].values
    anchor_idx       = np.arange(test_start_idx - 1,
                                 test_start_idx - 1 + len(pred_log_returns))
    anchor_prices    = actual_close_arr[anchor_idx]
    pred_prices      = anchor_prices * np.exp(pred_log_returns)

    # 6 — Monte Carlo future forecast ──────────────────────────────────────────
    # Anchor at the TRUE last close so forecast line has zero gap with history.
    last_actual_close = float(df_raw['Close'].iloc[-1])
    mc_raw = monte_carlo_forecast(
        model,
        scaled_data,
        raw_close_last = last_actual_close,
        scaler         = scaler,
        n_features     = len(FEATURE_COLS),
        seq_length     = seq_length,
        forecast_days  = forecast_days,
        device         = device,
    )

    future_dates = pd.date_range(
        start=df_raw.index[-1], periods=forecast_days + 1, freq="B"
    )[1:]
    future_means = [item['mean'] for item in mc_raw]
    future_stds  = [item['std']  for item in mc_raw]


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

    # MAE on test set
    mae = float(np.mean(np.abs(pred_prices - actual_prices)))

    if   pct_change >  1.0: signal, badge_class = "STRONG BUY",  "badge-bull"
    elif pct_change >  0.0: signal, badge_class = "BUY",         "badge-bull"
    elif pct_change < -1.0: signal, badge_class = "STRONG SELL", "badge-bear"
    else:                   signal, badge_class = "HOLD",        "badge-neut"

    # 8 — Render summary ───────────────────────────────────────────────────────
    section_header("📊 Summary")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("CURRENT PRICE",                 f"${last_price:.2f}")
    c2.metric(f"FORECAST (+{forecast_days}d)", f"${next_price:.2f}", f"{pct_change:+.2f}%")
    c3.metric("DIRECTIONAL ACCURACY",          f"{dir_acc:.1f}%")
    c4.metric("MAE (Test Set)",                f"${mae:.2f}")
    c5.metric("ANN. VOLATILITY",               f"{volatility:.2%}")

    signal_badge(signal, badge_class)
    split_pills(val_split, split - val_split, len(X_test))

    # 9 — Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊  PRICE CHART", "📉  MODEL PERFORMANCE", "📈  MACD", "ℹ️  ABOUT"
    ])

    with tab1:
        test_idx = df.index[test_start_idx : test_start_idx + len(actual_prices)]

        # Attach computed indicator columns to df_raw for chart overlays
        df_with_indicators = df_raw.copy()
        df_feat = add_technical_features(df_raw)
        df_feat = add_quant_features(df_feat, market_df)
        for col in ['RSI', 'BB_Upper', 'BB_Lower', 'MACD', 'MACD_Signal']:
            if col in df_feat.columns:
                df_with_indicators[col] = df_feat[col]

        fig = build_price_chart(
            df_raw        = df_with_indicators,
            test_idx      = test_idx,
            actual_prices = actual_prices,
            pred_prices   = pred_prices,
            future_dates  = future_dates,
            future_means  = future_means,
            future_stds   = future_stds,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        section_header("Training Loss Curves")
        fig_loss = build_loss_chart(loss_history)
        st.plotly_chart(fig_loss, use_container_width=True)

        section_header("Test Set Performance")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("DIRECTIONAL ACCURACY", f"{dir_acc:.2f}%")
        c2.metric("MAE (Test Set)",        f"${mae:.2f}")
        c3.metric("TEST SAMPLES",          str(len(pred_prices)))
        c4.metric("BEST VAL LOSS",         f"{min(loss_history['val']):.5f}")
        st.caption(
            f"Trained for {len(loss_history['train'])} epochs  ·  "
            f"Best epoch: {int(np.argmin(loss_history['val'])) + 1}  ·  "
            f"Hidden: {hidden_size}  ·  CNN channels: {cnn_channels}  ·  "
            f"Heads: {num_heads}  ·  Dropout: {dropout}  ·  "
            f"Features: {N_PRICE_FEATURES} price + {N_FACTOR_FEATURES} quant factors"
        )

    with tab3:
        section_header("MACD — Moving Average Convergence Divergence")
        df_feat2 = add_technical_features(df_raw)
        fig_macd = build_macd_chart(df_feat2)
        if fig_macd:
            st.plotly_chart(fig_macd, use_container_width=True)
            st.caption("MACD = EMA(12) − EMA(26)  ·  Signal = EMA(9) of MACD  ·  Histogram = MACD − Signal")
        else:
            st.info("MACD data not available.")

    with tab4:
        render_about_tab()
