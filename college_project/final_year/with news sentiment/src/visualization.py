"""
visualization.py — all charts + dashboard rendering
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import joblib, os

# ── Shared Plotly theme ───────────────────────────────────────────────────────
DARK_BG    = "#080f1a"
PANEL_BG   = "#0f1923"
GRID_COLOR = "#1e3a5f"
TEXT_COLOR = "#94a3b8"
BLUE       = "#38bdf8"
PURPLE     = "#818cf8"
GREEN      = "#4ade80"
RED        = "#f87171"
ORANGE     = "#fb923c"
YELLOW     = "#fbbf24"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=PANEL_BG,
    font=dict(family="DM Mono, monospace", color=TEXT_COLOR, size=11),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, showgrid=True),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, showgrid=True, tickformat="$.2f"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID_COLOR, borderwidth=1,
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    margin=dict(l=10, r=10, t=50, b=10),
)


def _section(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def _next_trading_day(last_date: pd.Timestamp) -> pd.Timestamp:
    """Skip Saturday (+2) and Sunday (+2) to land on Monday."""
    next_d = last_date + timedelta(days=1)
    if next_d.weekday() == 5:   # Saturday
        next_d += timedelta(days=2)
    elif next_d.weekday() == 6:  # Sunday
        next_d += timedelta(days=1)
    return next_d


# ── Chart 1: Full history + forecast ─────────────────────────────────────────
def _chart_history_forecast(price_data, lstm_price, final_price, ticker):
    last_date  = pd.Timestamp(price_data.index[-1])
    # BUG FIX: advance to next *trading* day, not just +1 calendar day
    next_date  = _next_trading_day(last_date)
    last_close = float(price_data["Close"].iloc[-1])
    pred_color = GREEN if final_price >= last_close else RED

    fig = go.Figure()

    # Full history
    fig.add_trace(go.Scatter(
        x=price_data.index, y=price_data["Close"],
        name="Historical Close", line=dict(color=BLUE, width=1.5),
        hovertemplate="%{x|%b %d %Y}  $%{y:.2f}<extra></extra>",
    ))

    # LSTM raw bridge
    fig.add_trace(go.Scatter(
        x=[last_date, next_date], y=[last_close, lstm_price],
        name="LSTM Raw", line=dict(color="#475569", width=2, dash="dot"),
        hovertemplate="%{x|%b %d %Y}  LSTM $%{y:.2f}<extra></extra>",
    ))

    # Sentiment-adjusted bridge
    fig.add_trace(go.Scatter(
        x=[last_date, next_date], y=[last_close, final_price],
        name="Ensemble Forecast", line=dict(color=pred_color, width=3, dash="dash"),
        hovertemplate="%{x|%b %d %Y}  Forecast $%{y:.2f}<extra></extra>",
    ))

    # Prediction diamond
    fig.add_trace(go.Scatter(
        x=[next_date], y=[final_price], mode="markers+text",
        name="Tomorrow", marker=dict(size=14, color=pred_color, symbol="diamond",
                                     line=dict(width=2, color="#ffffff")),
        text=[f"  ${final_price:.2f}"], textposition="middle right",
        textfont=dict(family="DM Mono", size=13, color=pred_color),
        hovertemplate=f"Tomorrow  ${final_price:.2f}<extra></extra>",
    ))

    # ±2% uncertainty band
    fig.add_hrect(y0=final_price*0.98, y1=final_price*1.02,
                  fillcolor=pred_color, opacity=0.06, layer="below", line_width=0)

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(text=f"<b>{ticker}</b> — Full Price History + 1-Day Forecast",
                   font=dict(family="Syne", size=16, color="#e2e8f0")),
        height=460,
        xaxis=dict(**PLOTLY_LAYOUT["xaxis"], rangeslider=dict(visible=True, thickness=0.04)),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


# ── Chart 2: True test-set predictions vs actual ─────────────────────────────
def _chart_test_backtest(ticker):
    splits_path = os.path.join("models", f"{ticker}_splits.pkl")
    if not os.path.exists(splits_path):
        st.info("No saved test data — tick **Force Retrain** and run again.")
        return

    saved   = joblib.load(splits_path)
    dates   = [pd.Timestamp(d) for d in saved["test_dates"]]
    actual  = list(saved["test_actual"])
    pred    = list(saved["test_pred"])
    mae     = saved["mae"]
    mape    = saved["mape"]
    rmse    = saved["rmse"]

    if not dates:
        st.info("Test set is empty.")
        return

    fig = go.Figure()

    # Actual
    fig.add_trace(go.Scatter(
        x=dates, y=actual, name="Actual Close",
        line=dict(color=BLUE, width=2),
        hovertemplate="%{x|%b %d %Y}  Actual $%{y:.2f}<extra></extra>",
    ))

    # Predicted
    fig.add_trace(go.Scatter(
        x=dates, y=pred, name="LSTM Predicted",
        line=dict(color=ORANGE, width=2, dash="dash"),
        hovertemplate="%{x|%b %d %Y}  Pred $%{y:.2f}<extra></extra>",
    ))

    # Error band: ±MAE around predictions (correct visual for forecast uncertainty)
    pred_upper = [p + mae for p in pred]
    pred_lower = [p - mae for p in pred]
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=pred_upper + pred_lower[::-1],
        fill="toself",
        fillcolor="rgba(251,146,60,0.10)",
        line=dict(color="rgba(0,0,0,0)"),
        name=f"±MAE Band (${mae:.2f})", hoverinfo="skip",
    ))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(
            text=f"<b>{ticker}</b> — Test Set: LSTM Predicted vs Actual"
                 f"   |   MAE ${mae:.2f}   RMSE ${rmse:.2f}   MAPE {mape:.2f}%",
            font=dict(family="Syne", size=15, color="#e2e8f0"),
        ),
        height=380,
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Held-out 10% test set — the model never saw this data during training or validation.")


# ── Chart 3: Training & validation loss curves ────────────────────────────────
def _chart_loss_curves(metrics):
    tl = metrics.get("train_losses", [])
    vl = metrics.get("val_losses", [])
    if not tl:
        return

    epochs = list(range(1, len(tl) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=epochs, y=tl, name="Train Loss",
                             line=dict(color=BLUE, width=2)))
    fig.add_trace(go.Scatter(x=epochs, y=vl, name="Val Loss",
                             line=dict(color=PURPLE, width=2, dash="dash")))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(text="Training & Validation Loss (MSE)",
                   font=dict(family="Syne", size=15, color="#e2e8f0")),
        yaxis=dict(**{k:v for k,v in PLOTLY_LAYOUT["yaxis"].items() if k != "tickformat"},
                   title="MSE Loss", tickformat=".6f"),
        xaxis=dict(**PLOTLY_LAYOUT["xaxis"], title="Epoch"),
        height=300,
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


# ── Chart 4: Sentiment gauge ──────────────────────────────────────────────────
def _chart_sentiment_gauge(score):
    # Round to avoid floating-point noise like 0.22000000000000003
    score = round(float(score), 3)
    color = GREEN if score > 0.1 else RED if score < -0.1 else "#94a3b8"
    label = "BULLISH" if score > 0.1 else "BEARISH" if score < -0.1 else "NEUTRAL"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",          # remove delta — it was showing the raw float noise
        value=score,
        number=dict(
            valueformat="+.3f",
            font=dict(family="Syne", size=40, color=color),
            suffix="  " + label,
        ),
        gauge=dict(
            axis=dict(
                range=[-1, 1],
                tickmode="array",
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=["-1", "-0.5", "0", "+0.5", "+1"],   # explicit labels fix mirror bug
                tickcolor=TEXT_COLOR,
                tickfont=dict(family="DM Mono", size=10, color=TEXT_COLOR),
            ),
            bar=dict(color=color, thickness=0.25),
            bgcolor=PANEL_BG,
            bordercolor=GRID_COLOR,
            borderwidth=1,
            steps=[
                dict(range=[-1.0, -0.1], color="#2d0a0a"),
                dict(range=[-0.1,  0.1], color="#1e293b"),
                dict(range=[ 0.1,  1.0], color="#052e16"),
            ],
            threshold=dict(
                line=dict(color="#ffffff", width=3),
                thickness=0.75,
                value=score,
            ),
        ),
        title=dict(
            text="AGGREGATE SENTIMENT SCORE",
            font=dict(family="DM Mono", size=10, color=TEXT_COLOR),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=PANEL_BG,
        height=230,
        margin=dict(l=30, r=30, t=50, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── News evidence cards ───────────────────────────────────────────────────────
def _render_news(evidence: list[dict]):
    if not evidence:
        st.info("No news articles analysed.")
        return

    for item in evidence:
        score  = item["score"]
        label  = item["label"]
        badge  = (f'<span class="badge-bull">▲ {label} {score:+.2f}</span>' if label == "Bullish" else
                  f'<span class="badge-bear">▼ {label} {score:+.2f}</span>' if label == "Bearish" else
                  f'<span class="badge-neut">— {label} {score:+.2f}</span>')
        horizon_color = {"short-term": "#38bdf8", "medium-term": "#a78bfa",
                         "long-term": "#4ade80"}.get(item.get("horizon",""), "#64748b")

        pub = f' &nbsp;·&nbsp; {item["published"]}' if item.get("published") else ""
        url_tag = (f' &nbsp;·&nbsp; <a href="{item["url"]}" target="_blank" '
                   f'style="color:#38bdf8;font-size:0.65rem">↗ source</a>') if item.get("url") else ""

        st.markdown(f"""
<div class="news-card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span class="news-source">{item['source']}{pub}</span>
    <span style="display:flex;gap:6px;align-items:center">
      <span style="font-family:'DM Mono',monospace;font-size:0.65rem;color:{horizon_color}">{item.get('horizon','')}</span>
      {badge}
    </span>
  </div>
  <div class="news-title">{item['title']}</div>
  <div class="news-summary">"{item['quote']}"</div>
  <div class="news-summary" style="margin-top:4px">{item['summary']}</div>
  <div class="news-reasoning">{item['reasoning']}{url_tag}</div>
</div>
""", unsafe_allow_html=True)


# ── Raw price data table ──────────────────────────────────────────────────────
def _render_raw_data(price_data: pd.DataFrame):
    with st.expander("📄  View raw price data"):
        available_years = sorted(price_data.index.year.unique(), reverse=True)
        selected_years  = st.multiselect(
            "Filter by year", options=available_years,
            default=[available_years[0]],
            help="Select years — results stay visible while you filter"
        )
        filtered = (price_data[price_data.index.year.isin(selected_years)].copy()
                    if selected_years else price_data.copy())
        filtered.index = filtered.index.date
        st.caption(f"Showing **{len(filtered):,}** trading days across "
                   f"**{len(selected_years) if selected_years else 'all'}** year(s)")
        st.dataframe(
            filtered[["Open","High","Low","Close","Volume"]]
              .sort_index(ascending=False)
              .style.format({"Open":"${:.2f}","High":"${:.2f}",
                             "Low":"${:.2f}","Close":"${:.2f}",
                             "Volume":"{:,.0f}"}),
            use_container_width=True, height=420,
        )


# ── Master render function ────────────────────────────────────────────────────
def render_dashboard(
    price_data, lstm_price, final_price,
    sentiment_score, evidence, metrics, ticker, sentiment_weight,
    ensemble_details=None,
):
    last_close = float(price_data["Close"].iloc[-1])
    delta      = final_price - last_close
    pct        = delta / last_close * 100

    # ── KPI row ───────────────────────────────────────────────────────────────
    st.divider()
    _section("Prediction Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last Close",                  f"${last_close:.2f}")
    c2.metric("LSTM Raw Forecast",            f"${lstm_price:.2f}",
              delta=f"{lstm_price - last_close:+.2f}")
    c3.metric("Ensemble Forecast (Tomorrow)", f"${final_price:.2f}",
              delta=f"{delta:+.2f}  ({pct:+.1f}%)")
    impact = (ensemble_details or {}).get("impact_score", sentiment_score)
    used_meta = (ensemble_details or {}).get("used_meta", False)
    c4.metric("Impact Score (weighted)",
              f"{impact:+.3f}",
              delta=("Bullish" if impact > 0.05 else "Bearish" if impact < -0.05 else "Neutral")
              + (" · Meta-learner ✓" if used_meta else " · Multiplier"))

    # ── Model evaluation ──────────────────────────────────────────────────────
    if metrics:
        st.divider()
        _section("Model Evaluation  —  80 / 10 / 10 Chronological Split")
        n         = metrics.get("n_total", 0)
        train_end = metrics.get("train_end", 0)
        val_end   = metrics.get("val_end", 0)

        st.markdown(
            f'<span class="split-pill pill-train">Train  {train_end:,} days  (80%)</span>'
            f'<span class="split-pill pill-val">Val  {val_end-train_end:,} days  (10%)</span>'
            f'<span class="split-pill pill-test">Test  {n-val_end:,} days  (10%)</span>',
            unsafe_allow_html=True
        )
        st.markdown("")

        e1, e2, e3, e4, e5 = st.columns(5)
        e1.metric("Test MAE",        f"${metrics.get('mae',  0):.2f}")
        e2.metric("Test RMSE",       f"${metrics.get('rmse', 0):.2f}")
        e3.metric("Test MAPE",       f"{metrics.get('mape',  0):.2f}%")
        e4.metric("Test R²",         f"{metrics.get('r2',    0):.4f}")
        e5.metric("Best Val Loss",   f"{metrics.get('best_val_loss', 0):.6f}")

    # ── Charts ────────────────────────────────────────────────────────────────
    st.divider()
    _section("Price History + Forecast")
    _chart_history_forecast(price_data, lstm_price, final_price, ticker)

    st.divider()
    _section("Test Set: LSTM Predicted vs Actual  (held-out 10%)")
    _chart_test_backtest(ticker)

    if metrics and metrics.get("train_losses"):
        st.divider()
        _section("Training Diagnostics")
        col_loss, col_gauge = st.columns([2, 1])
        with col_loss:
            _chart_loss_curves(metrics)
        with col_gauge:
            _chart_sentiment_gauge(sentiment_score)

    # ── News ──────────────────────────────────────────────────────────────────
    st.divider()
    _section("News Sentiment Analysis  —  " + str(len(evidence)) + " articles")
    if evidence:
        bull   = sum(1 for e in evidence if e["label"] == "Bullish")
        bear   = sum(1 for e in evidence if e["label"] == "Bearish")
        neut   = sum(1 for e in evidence if e["label"] == "Neutral")
        impact = (ensemble_details or {}).get("impact_score", sentiment_score)
        raw    = (ensemble_details or {}).get("raw_sentiment", sentiment_score)
        html   = (
            '<span class="badge-bull">&#x25B2; Bullish ' + str(bull) + '</span>&nbsp;&nbsp;'
            '<span class="badge-bear">&#x25BC; Bearish ' + str(bear) + '</span>&nbsp;&nbsp;'
            '<span class="badge-neut">&#x2014; Neutral ' + str(neut) + '</span>'
            '&nbsp;&nbsp;&nbsp;'
            '<span style="font-family:monospace;font-size:0.7rem;color:#94a3b8">'
            'Raw: ' + f'{raw:+.3f}' + ' &rarr; Impact: ' + f'{impact:+.3f}' +
            ' (credibility + recency weighted)'
            '</span>'
        )
        st.markdown(html, unsafe_allow_html=True)
        st.markdown("")
    _render_news(evidence)

    # ── Raw data ──────────────────────────────────────────────────────────────
    st.divider()
    _render_raw_data(price_data)