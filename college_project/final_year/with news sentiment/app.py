"""
app.py — Ticker-Teller v2  |  Professional Stock Prediction Dashboard
Ensemble of LSTM time-series forecasting + LLM news sentiment analysis
"""
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv("keys.env")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ticker-Teller",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — professional light finance theme ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

/* ── Force dark background on the whole app ── */
.stApp {
    background-color: #0b1120 !important;
}
section[data-testid="stSidebar"] {
    background-color: #060d18 !important;
}
/* Main content area */
.block-container {
    background-color: #0b1120 !important;
}

/* ── All text defaults ── */
html, body, [class*="css"], p, span, div, label {
    font-family: 'Inter', sans-serif;
    color: #e2e8f0;
}

/* ── Header ── */
.tt-header {
    background: linear-gradient(135deg, #0f1923 0%, #1a2942 50%, #0f2744 100%);
    border: 1px solid #1e3a5f;
    padding: 2rem 2.5rem 1.5rem;
    margin-bottom: 2rem;
    border-radius: 16px;
}
.tt-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #e879f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.5px;
}
.tt-subtitle {
    font-family: 'DM Mono', monospace;
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 0.3rem;
    letter-spacing: 0.05em;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] p {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #94a3b8 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] > div,
[data-testid="stMetricValue"] p {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
}
[data-testid="stMetricDelta"] > div,
[data-testid="stMetricDelta"] p {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    color: #94a3b8 !important;
}

/* ── Section headers ── */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #f1f5f9;
    border-left: 3px solid #38bdf8;
    padding-left: 0.8rem;
    margin: 1.5rem 0 1rem 0;
    letter-spacing: -0.2px;
}

/* ── News cards ── */
.news-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s, transform 0.15s;
}
.news-card:hover {
    border-color: #38bdf8;
    transform: translateX(2px);
}
.news-source {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.news-title {
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0.3rem 0;
}
.news-summary {
    font-size: 0.8rem;
    color: #cbd5e1;
    line-height: 1.5;
}
.news-reasoning {
    font-size: 0.75rem;
    color: #94a3b8;
    font-style: italic;
    margin-top: 0.3rem;
}

/* ── Badges ── */
.badge-bull { background:#052e16; color:#4ade80; border:1px solid #166534; border-radius:6px; padding:2px 8px; font-family:'DM Mono',monospace; font-size:0.7rem; }
.badge-bear { background:#450a0a; color:#fca5a5; border:1px solid #991b1b; border-radius:6px; padding:2px 8px; font-family:'DM Mono',monospace; font-size:0.7rem; }
.badge-neut { background:#1e293b; color:#cbd5e1; border:1px solid #475569; border-radius:6px; padding:2px 8px; font-family:'DM Mono',monospace; font-size:0.7rem; }

/* ── Sidebar labels ── */
.sidebar-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
}
.key-status {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 4px 10px;
    border-radius: 6px;
    margin: 2px 0;
    display: inline-block;
}
.key-ok   { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.key-fail { background: #450a0a; color: #fca5a5; border: 1px solid #991b1b; }

/* ── Split pills ── */
.split-pill {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin-right: 6px;
}
.pill-train { background: #1e3a5f; color: #7dd3fc; }
.pill-val   { background: #2d1f52; color: #c4b5fd; }
.pill-test  { background: #14532d; color: #86efac; }

/* ── Streamlit widget text ── */
.stTextInput label, .stSelectbox label, .stSlider label,
.stCheckbox label, p, li, span {
    color: #e2e8f0 !important;
}
.stTextInput input {
    background: #111827 !important;
    color: #f1f5f9 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
}
.stSelectbox > div > div {
    background: #111827 !important;
    color: #f1f5f9 !important;
    border: 1px solid #1e3a5f !important;
}
/* Slider track */
[data-testid="stSlider"] > div > div > div {
    background: #1e3a5f !important;
}

/* ── Dividers ── */
hr { border-color: #1e3a5f !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary p {
    color: #e2e8f0 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
}

/* ── Captions ── */
[data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
}

/* ── Success / warning / error boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tt-header">
  <div class="tt-title">📈 Ticker-Teller</div>
  <div class="tt-subtitle">LSTM TIME-SERIES FORECASTING &nbsp;×&nbsp; LLM NEWS SENTIMENT ENSEMBLE</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-label">Ticker Symbol</div>', unsafe_allow_html=True)
    TICKER = st.text_input("", value="AAPL", label_visibility="collapsed").upper().strip()

    st.markdown('<div class="sidebar-label" style="margin-top:1rem">Training History</div>', unsafe_allow_html=True)
    period_mode = st.radio("", ["Preset", "Custom"], horizontal=True, label_visibility="collapsed")

    if period_mode == "Preset":
        period = st.selectbox("", ["1y", "2y", "5y", "10y"], index=3, label_visibility="collapsed")
    else:
        col_y, col_m = st.columns(2)
        with col_y:
            st.markdown('<div class="sidebar-label">Years</div>', unsafe_allow_html=True)
            custom_years = st.number_input("", min_value=0, max_value=20, value=5,
                                           step=1, label_visibility="collapsed")
        with col_m:
            st.markdown('<div class="sidebar-label">Months</div>', unsafe_allow_html=True)
            custom_months = st.number_input("", min_value=0, max_value=11, value=0,
                                            step=1, label_visibility="collapsed")
        total_months = int(custom_years) * 12 + int(custom_months)
        total_months = max(total_months, 6)   # minimum 6 months
        # Convert to yfinance period string
        if total_months % 12 == 0:
            period = f"{total_months // 12}y"
        else:
            period = f"{total_months}mo"
        st.caption(f"Selected: {custom_years}y {custom_months}mo → `{period}`")
    
    st.markdown('<div class="sidebar-label" style="margin-top:1rem">News Lookback (days)</div>', unsafe_allow_html=True)
    news_days = st.slider("", 7, 29, 14, label_visibility="collapsed")

    st.markdown('<div class="sidebar-label" style="margin-top:1rem">Ensemble Weight — Sentiment</div>', unsafe_allow_html=True)
    sentiment_weight = st.slider("", 0.01, 0.15, 0.05, 0.01, label_visibility="collapsed",
                                  help="How much sentiment nudges the LSTM price (0.05 = ±5% max)")

    retrain = st.checkbox("⚡ Force Retrain LSTM", value=False)

    st.divider()
    groq_ok    = bool(os.getenv("GROQ_API_KEY"))
    newsapi_ok = bool(os.getenv("NEWSAPI_KEY"))
    st.markdown(
        f'<span class="key-status {"key-ok" if groq_ok else "key-fail"}">{"✓" if groq_ok else "✗"} GROQ_API_KEY</span><br>'
        f'<span class="key-status {"key-ok" if newsapi_ok else "key-fail"}" style="margin-top:4px">{"✓" if newsapi_ok else "✗"} NEWSAPI_KEY</span>',
        unsafe_allow_html=True
    )
    st.caption("Keys loaded from `keys.env`")

# ── Session state ──────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None

# ── Run button ─────────────────────────────────────────────────────────────────
if st.button(f"🚀  Run Prediction for  {TICKER}", type="primary", use_container_width=True):

    if not groq_ok or not newsapi_ok:
        st.error("One or more API keys are missing. Add them to `keys.env`.")
        st.stop()

    from src.data_fetch     import fetch_price_data, fetch_news
    from src.llm_sentiment  import get_sentiment_and_summary
    from src.lstm_predictor import predict_next_price
    from src.ensemble       import ensemble_predict, train_meta_learner, compute_impact_score

    # 1 — Price data
    with st.spinner("📥  Fetching price data… (may retry up to 80s if rate-limited)"):
        try:
            price_data = fetch_price_data(TICKER, period=period)
        except Exception as e:
            st.error(
                f"**Price data failed:** {e}\n\n"
                "💡 **Fix:** Yahoo Finance rate-limits frequent requests. "
                "Wait 1–2 minutes then click Run again."
            )
            st.stop()

    if price_data.empty:
        st.error(f"No data for **{TICKER}**. Check the symbol.")
        st.stop()

    st.success(f"✅  Loaded **{len(price_data):,}** trading days for {TICKER}")

    # 2 — Sentiment
    with st.spinner("🗞️  Analysing news with LLM…"):
        try:
            articles = fetch_news(TICKER, days=news_days)
            sentiment_score, evidence = get_sentiment_and_summary(articles, TICKER)
            if not articles:
                st.warning("No news articles found — using neutral sentiment.")
        except Exception as e:
            st.warning(f"News failed ({e}) — neutral sentiment.")
            sentiment_score, evidence = 0.0, []

    # 3 — LSTM
    with st.spinner("🧠  Running LSTM forecast…"):
        try:
            lstm_price, metrics = predict_next_price(
                price_data, ticker=TICKER, force_retrain=retrain
            )
        except Exception as e:
            st.error(f"LSTM failed: {e}")
            st.stop()

    # 4 — Train meta-learner on val set (fast, uses saved splits)
    if metrics:
        import os, joblib
        splits_path = os.path.join("models", f"{TICKER}_splits.pkl")
        meta_path   = os.path.join("models", f"{TICKER}_meta.pkl")
        if os.path.exists(splits_path) and (retrain or not os.path.exists(meta_path)):
            with st.spinner("⚙️  Training ensemble meta-learner…"):
                splits_info = joblib.load(splits_path)
                train_meta_learner(TICKER, price_data, splits_info)

    # 5 — Ensemble prediction with ImpactScore
    final_price, ensemble_details = ensemble_predict(
        lstm_price, sentiment_score, sentiment_weight,
        evidence=evidence, ticker=TICKER, price_data=price_data,
    )

    # Save to session state
    st.session_state.results = dict(
        ticker=TICKER, price_data=price_data,
        lstm_price=lstm_price, final_price=final_price,
        sentiment_score=sentiment_score, evidence=evidence,
        metrics=metrics, sentiment_weight=sentiment_weight,
        ensemble_details=ensemble_details,
    )

# ── Render (survives widget reruns via session state) ──────────────────────────
if st.session_state.results:
    from src.visualization import render_dashboard

    r = st.session_state.results
    render_dashboard(
        price_data       = r["price_data"],
        lstm_price       = r["lstm_price"],
        final_price      = r["final_price"],
        sentiment_score  = r["sentiment_score"],
        evidence         = r["evidence"],
        metrics          = r["metrics"],
        ticker           = r["ticker"],
        sentiment_weight = r["sentiment_weight"],
        ensemble_details = r.get("ensemble_details", {}),
    )