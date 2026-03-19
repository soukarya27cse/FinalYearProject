"""
src/ui.py — Streamlit CSS injection & reusable UI helpers
"""
import streamlit as st


# ── CSS ────────────────────────────────────────────────────────────────────────

def inject_css() -> None:
    """Inject the full Ticker-Teller dark finance CSS into the page."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

.stApp { background-color: #0b1120 !important; }
section[data-testid="stSidebar"] { background-color: #060d18 !important; }
.block-container { background-color: #0b1120 !important; }

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

/* ── Signal badges ── */
.badge-bull { background:#052e16; color:#4ade80; border:1px solid #166534; border-radius:6px; padding:2px 8px; font-family:'DM Mono',monospace; font-size:0.7rem; }
.badge-bear { background:#450a0a; color:#fca5a5; border:1px solid #991b1b; border-radius:6px; padding:2px 8px; font-family:'DM Mono',monospace; font-size:0.7rem; }
.badge-neut { background:#1e293b; color:#cbd5e1; border:1px solid #475569; border-radius:6px; padding:2px 8px; font-family:'DM Mono',monospace; font-size:0.7rem; }

/* ── Split pills ── */
.split-pill { display:inline-block; font-family:'DM Mono',monospace; font-size:0.7rem; padding:3px 10px; border-radius:20px; margin-right:6px; }
.pill-train { background:#1e3a5f; color:#7dd3fc; }
.pill-val   { background:#2d1f52; color:#c4b5fd; }
.pill-test  { background:#14532d; color:#86efac; }

/* ── Sidebar ── */
.sidebar-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
}

/* ── Widget overrides ── */
.stTextInput label, .stSelectbox label, .stSlider label,
.stCheckbox label, p, li, span { color: #e2e8f0 !important; }
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
[data-testid="stSlider"] > div > div > div { background: #1e3a5f !important; }

/* ── Primary button ── */
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #0ea5e9, #6366f1) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
    padding: 0.6rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
div.stButton > button[kind="primary"]:hover { opacity: 0.85 !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #94a3b8 !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom-color: #38bdf8 !important;
}

/* ── Misc ── */
[data-testid="stExpander"] { background:#111827 !important; border:1px solid #1e3a5f !important; border-radius:12px !important; }
[data-testid="stExpander"] summary p { color:#e2e8f0 !important; }
hr { border-color: #1e3a5f !important; }
[data-testid="stCaptionContainer"] p { color:#64748b !important; font-family:'DM Mono',monospace !important; font-size:0.72rem !important; }
[data-testid="stAlert"] { border-radius:10px !important; }
</style>
""", unsafe_allow_html=True)


# ── Reusable components ────────────────────────────────────────────────────────

def render_header() -> None:
    st.markdown("""
<div class="tt-header">
  <div class="tt-title">📈 Ticker-Teller</div>
  <div class="tt-subtitle">CNN → BILSTM → ATTENTION &nbsp;×&nbsp; MONTE CARLO UNCERTAINTY ESTIMATION</div>
</div>
""", unsafe_allow_html=True)


def section_header(text: str) -> None:
    """Render a left-bordered section title."""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def signal_badge(signal: str, badge_class: str) -> None:
    st.markdown(
        f'<div style="margin:0.5rem 0 0.5rem">'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:0.72rem;color:#94a3b8;margin-right:8px">AI SIGNAL</span>'
        f'<span class="{badge_class}">{signal}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def split_pills(n_train: int, n_val: int, n_test: int) -> None:
    st.markdown(
        f'<div style="margin-bottom:1.5rem">'
        f'<span class="split-pill pill-train">TRAIN {n_train}</span>'
        f'<span class="split-pill pill-val">VAL {n_val}</span>'
        f'<span class="split-pill pill-test">TEST {n_test}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict:
    """Render all sidebar widgets and return their values as a dict."""
    with st.sidebar:
        st.markdown('<div class="sidebar-label">Ticker Symbol</div>', unsafe_allow_html=True)
        ticker = st.text_input("", value="AAPL", label_visibility="collapsed").upper().strip()

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Historical Data (Days)</div>', unsafe_allow_html=True)
        period = st.slider("", 365, 1825, 730, label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Lookback Sequence (Days)</div>', unsafe_allow_html=True)
        seq_length = st.slider("", 10, 120, 60, label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Forecast Horizon (Days)</div>', unsafe_allow_html=True)
        forecast_days = st.slider("", 1, 30, 5, label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Max Training Epochs</div>', unsafe_allow_html=True)
        epochs = st.slider("", 10, 200, 50, label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Early Stopping Patience</div>', unsafe_allow_html=True)
        patience = st.slider("", 3, 20, 10, label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">BiLSTM Hidden Size</div>', unsafe_allow_html=True)
        hidden_size = st.select_slider("", options=[32, 64, 128, 256], value=128, label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">CNN Channels</div>', unsafe_allow_html=True)
        cnn_channels = st.select_slider("", options=[32, 64, 128], value=64,
                                        key="cnn_channels", label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Attention Heads</div>', unsafe_allow_html=True)
        num_heads = st.select_slider("", options=[2, 4, 8], value=4,
                                     key="num_heads", label_visibility="collapsed")

        st.markdown('<div class="sidebar-label" style="margin-top:1rem">Dropout Rate</div>', unsafe_allow_html=True)
        dropout = st.slider("", 0.0, 0.5, 0.2, step=0.05, label_visibility="collapsed")

        st.divider()
        st.markdown("""
<div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#94a3b8;line-height:2">
  <span style="color:#38bdf8">●</span> OHLCV + Volume inputs<br>
  <span style="color:#818cf8">●</span> SMA / RSI / MACD / BB features<br>
  <span style="color:#e879f9">●</span> CNN → BiLSTM → Attention<br>
  <span style="color:#4ade80">●</span> Monte Carlo uncertainty bands<br>
  <span style="color:#fbbf24">●</span> AdamW + Cosine LR warm restarts
</div>
""", unsafe_allow_html=True)

    return dict(
        ticker        = ticker,
        period        = period,
        seq_length    = seq_length,
        forecast_days = forecast_days,
        epochs        = epochs,
        patience      = patience,
        hidden_size   = hidden_size,
        cnn_channels  = cnn_channels,
        num_heads     = num_heads,
        dropout       = dropout,
    )


def render_about_tab() -> None:
    st.markdown("""
<div style="font-family:'Inter',sans-serif;color:#e2e8f0;line-height:1.8">
<div class="section-header">🤖 About Ticker-Teller</div>
<p>Uses a <strong style="color:#38bdf8">Hybrid CNN → Bidirectional LSTM → Multi-Head Attention</strong>
neural network to forecast stock closing prices from multi-variate technical inputs.</p>
<p><strong style="color:#818cf8">Architecture</strong></p>
<ul>
  <li><strong>Temporal Conv Block</strong> — dual-kernel (3 &amp; 5) 1-D CNN with residual projection; detects local chart patterns at different time scales</li>
  <li><strong>Bidirectional LSTM</strong> — processes the CNN's features both forward and backward, capturing long-range dependencies from both directions</li>
  <li><strong>Multi-Head Self-Attention</strong> — explicitly scores which time steps matter most, with residual + LayerNorm for stability</li>
  <li><strong>MC Dropout Uncertainty</strong> — 100-sample Monte Carlo forward passes produce calibrated confidence bands</li>
</ul>
<p><strong style="color:#818cf8">Training</strong></p>
<ul>
  <li><strong>AdamW</strong> — decoupled weight decay handles the hybrid model's larger parameter count</li>
  <li><strong>Cosine Annealing Warm Restarts</strong> — periodic LR resets help escape local minima</li>
  <li><strong>Gradient Clipping</strong> — max norm 1.0 prevents exploding gradients</li>
  <li><strong>Early Stopping</strong> — halts when val loss plateaus, restores best weights</li>
</ul>
<p><strong style="color:#818cf8">Inputs (12 features)</strong></p>
<ul>
  <li><strong>Multi-Variate</strong> — OHLCV + RSI, SMA(10/50), MACD, Bollinger Bands</li>
</ul>
<p style="margin-top:1.2rem;padding:0.8rem 1rem;background:#450a0a;border:1px solid #991b1b;
   border-radius:8px;font-size:0.82rem;color:#fca5a5">
⚠️ <strong>Disclaimer:</strong> Educational purposes only.
Stock predictions are inherently uncertain. Do not use as sole financial advice.
</p>
</div>
""", unsafe_allow_html=True)