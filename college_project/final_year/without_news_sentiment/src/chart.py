"""
src/charts.py — Plotly figure builders
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Shared Plotly theme ────────────────────────────────────────────────────────
_LAYOUT_BASE = dict(
    template       = "plotly_dark",
    paper_bgcolor  = "#0b1120",
    plot_bgcolor   = "#0b1120",
    hovermode      = "x unified",
    # Use a light colour so all axis labels, tick text, and subplot
    # titles are clearly visible against the dark background.
    font           = dict(family="DM Mono, monospace", color="#e2e8f0", size=12),
    legend         = dict(
        bgcolor     = "#111827",
        bordercolor = "#1e3a5f",
        borderwidth = 1,
        font        = dict(family="DM Mono", color="#e2e8f0", size=11),
    ),
)
_AXIS_STYLE = dict(gridcolor="#1e3a5f", zerolinecolor="#1e3a5f")


def build_price_chart(
    df_raw:        pd.DataFrame,
    test_idx:      pd.DatetimeIndex,
    actual_prices: np.ndarray,
    pred_prices:   np.ndarray,
    future_dates:  pd.DatetimeIndex,
    future_means:  list[float],
    future_stds:   list[float],
) -> go.Figure:
    """Build the main price + volume subplot figure.

    Layout:
        Row 1 (70%) — historical price, test actuals, test predictions,
                       future forecast line, MC uncertainty band
        Row 2 (30%) — candlestick-coloured volume bars
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes   = True,
        vertical_spacing = 0.03,
        row_heights    = [0.7, 0.3],
        subplot_titles = ("Price & Forecast", "Volume"),
    )

    # Historical close
    fig.add_trace(go.Scatter(
        x=df_raw.index, y=df_raw["Close"],
        mode="lines", name="Historical",
        line=dict(color="#38bdf8", width=1.5),
    ), row=1, col=1)

    # Test set — actual
    fig.add_trace(go.Scatter(
        x=test_idx, y=actual_prices,
        mode="lines", name="Actual (Test)",
        line=dict(color="#7dd3fc", width=1),
    ), row=1, col=1)

    # Test set — predicted
    fig.add_trace(go.Scatter(
        x=test_idx, y=pred_prices,
        mode="lines", name="Predicted (Test)",
        line=dict(color="#f472b6", dash="dash", width=1.5),
    ), row=1, col=1)

    # Future forecast
    fig.add_trace(go.Scatter(
        x=future_dates, y=future_means,
        mode="lines", name="Future Forecast",
        line=dict(color="#4ade80", width=3),
    ), row=1, col=1)

    # MC uncertainty band (filled polygon)
    upper = [m + s for m, s in zip(future_means, future_stds)]
    lower = [m - s for m, s in zip(future_means, future_stds)]
    fig.add_trace(go.Scatter(
        x    = list(future_dates) + list(future_dates)[::-1],
        y    = upper + lower[::-1],
        fill = "toself",
        fillcolor = "rgba(74,222,128,0.12)",
        line = dict(color="rgba(255,255,255,0)"),
        hoverinfo  = "skip",
        name       = "Uncertainty Band",
        showlegend = True,
    ), row=1, col=1)

    # Volume bars — green if close ≥ open, red otherwise
    bar_colors = [
        "#4ade80" if row["Close"] >= row["Open"] else "#f87171"
        for _, row in df_raw.iterrows()
    ]
    fig.add_trace(go.Bar(
        x=df_raw.index, y=df_raw["Volume"],
        marker_color=bar_colors, name="Volume", opacity=0.6,
    ), row=2, col=1)

    fig.update_layout(height=620, **_LAYOUT_BASE)
    fig.update_xaxes(
        rangeslider_visible=False,
        tickfont=dict(color="#e2e8f0", family="DM Mono, monospace", size=11),
        title_font=dict(color="#e2e8f0"),
        **_AXIS_STYLE,
    )
    fig.update_yaxes(
        tickfont=dict(color="#e2e8f0", family="DM Mono, monospace", size=11),
        title_font=dict(color="#e2e8f0"),
        **_AXIS_STYLE,
    )
    # Subplot titles are stored as annotations — override their colour explicitly
    for annotation in fig.layout.annotations:
        annotation.font = dict(color="#e2e8f0", family="DM Mono, monospace", size=12)
    return fig
