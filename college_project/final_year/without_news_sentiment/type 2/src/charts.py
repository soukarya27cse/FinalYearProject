"""
src/charts.py — Plotly figure builders
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Shared Plotly theme ────────────────────────────────────────────────────────
_LAYOUT_BASE = dict(
    template      = "plotly_dark",
    paper_bgcolor = "#0b1120",
    plot_bgcolor  = "#0b1120",
    hovermode     = "x unified",
    hoverlabel    = dict(
        bgcolor   = "#111827",
        bordercolor = "#1e3a5f",
        font      = dict(family="DM Mono, monospace", color="#e2e8f0", size=12),
    ),
    font          = dict(family="DM Mono, monospace", color="#e2e8f0", size=12),
    legend        = dict(
        bgcolor     = "#111827",
        bordercolor = "#1e3a5f",
        borderwidth = 1,
        font        = dict(family="DM Mono", color="#e2e8f0", size=11),
    ),
)
_AXIS_STYLE = dict(gridcolor="#1e3a5f", zerolinecolor="#1e3a5f")

# Range selector buttons shown above the price chart x-axis
_RANGE_BUTTONS = [
    dict(count=1,  label="1M",  step="month", stepmode="backward"),
    dict(count=3,  label="3M",  step="month", stepmode="backward"),
    dict(count=6,  label="6M",  step="month", stepmode="backward"),
    dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
    dict(count=2,  label="2Y",  step="year",  stepmode="backward"),
    dict(step="all", label="ALL"),
]
_RANGE_SELECTOR_STYLE = dict(
    buttons     = _RANGE_BUTTONS,
    bgcolor     = "#111827",
    activecolor = "#1e3a5f",
    bordercolor = "#1e3a5f",
    borderwidth = 1,
    font        = dict(color="#e2e8f0", family="DM Mono, monospace", size=11),
    x=0, y=1.0,
)


def _style_axes(fig: go.Figure, date_axes: bool = False) -> None:
    """Apply consistent axis + annotation styling to any figure.

    Args:
        date_axes: if True, apply date tickformat so hover shows full date string.
    """
    x_extra = dict(
        tickformat   = "%b %d, %Y",   # e.g. "Jan 05, 2024"
        hoverformat  = "%b %d, %Y",   # shown in unified hover label
    ) if date_axes else {}

    fig.update_xaxes(
        rangeslider_visible=False,
        tickfont=dict(color="#e2e8f0", family="DM Mono, monospace", size=11),
        title_font=dict(color="#e2e8f0"),
        **_AXIS_STYLE,
        **x_extra,
    )
    fig.update_yaxes(
        tickfont=dict(color="#e2e8f0", family="DM Mono, monospace", size=11),
        title_font=dict(color="#e2e8f0"),
        **_AXIS_STYLE,
    )
    for ann in fig.layout.annotations:
        ann.font = dict(color="#e2e8f0", family="DM Mono, monospace", size=12)


def build_price_chart(
    df_raw:        pd.DataFrame,
    test_idx:      pd.DatetimeIndex,
    actual_prices: np.ndarray,
    pred_prices:   np.ndarray,
    future_dates:  pd.DatetimeIndex,
    future_means:  list[float],
    future_stds:   list[float],
) -> go.Figure:
    """Build the main price + RSI + volume subplot figure.

    Layout:
        Row 1 (55%) — historical price, test actuals, test predictions,
                       future forecast line, MC uncertainty band,
                       Bollinger Bands overlay
        Row 2 (25%) — RSI(14) with overbought/oversold bands
        Row 3 (20%) — candlestick-coloured volume bars
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes     = True,
        vertical_spacing = 0.03,
        row_heights      = [0.55, 0.25, 0.20],
        subplot_titles   = ("Price & Forecast", "RSI (14)", "Volume"),
    )

    # ── Row 1: Price ──────────────────────────────────────────────────────────

    # Bollinger Bands (if present)
    if 'BB_Upper' in df_raw.columns and 'BB_Lower' in df_raw.columns:
        fig.add_trace(go.Scatter(
            x=df_raw.index, y=df_raw['BB_Upper'],
            mode='lines', name='BB Upper',
            line=dict(color='rgba(129,140,248,0.4)', width=1, dash='dot'),
            showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_raw.index, y=df_raw['BB_Lower'],
            mode='lines', name='BB Lower',
            line=dict(color='rgba(129,140,248,0.4)', width=1, dash='dot'),
            fill='tonexty',
            fillcolor='rgba(129,140,248,0.05)',
            showlegend=True,
        ), row=1, col=1)

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
        mode="lines+markers", name="Future Forecast",
        line=dict(color="#4ade80", width=3),
        marker=dict(size=5, color="#4ade80"),
    ), row=1, col=1)

    # MC uncertainty band (filled polygon)
    upper = [m + s for m, s in zip(future_means, future_stds)]
    lower = [m - s for m, s in zip(future_means, future_stds)]
    fig.add_trace(go.Scatter(
        x         = list(future_dates) + list(future_dates)[::-1],
        y         = upper + lower[::-1],
        fill      = "toself",
        fillcolor = "rgba(74,222,128,0.12)",
        line      = dict(color="rgba(255,255,255,0)"),
        hoverinfo = "skip",
        name      = "Uncertainty Band",
        showlegend= True,
    ), row=1, col=1)

    # ── Row 2: RSI ────────────────────────────────────────────────────────────
    if 'RSI' in df_raw.columns:
        fig.add_trace(go.Scatter(
            x=df_raw.index, y=df_raw['RSI'],
            mode='lines', name='RSI',
            line=dict(color='#fbbf24', width=1.5),
            showlegend=True,
        ), row=2, col=1)
        # Overbought line
        fig.add_hline(y=70, line_dash='dash', line_color='rgba(248,113,113,0.5)',
                      annotation_text='Overbought 70', annotation_position='top right',
                      annotation_font_color='#f87171', row=2, col=1)
        # Oversold line
        fig.add_hline(y=30, line_dash='dash', line_color='rgba(74,222,128,0.5)',
                      annotation_text='Oversold 30', annotation_position='bottom right',
                      annotation_font_color='#4ade80', row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)

    # ── Row 3: Volume ─────────────────────────────────────────────────────────
    bar_colors = [
        "#4ade80" if row["Close"] >= row["Open"] else "#f87171"
        for _, row in df_raw.iterrows()
    ]
    fig.add_trace(go.Bar(
        x=df_raw.index, y=df_raw["Volume"],
        marker_color=bar_colors, name="Volume", opacity=0.6,
    ), row=3, col=1)

    fig.update_layout(height=720, **_LAYOUT_BASE)
    _style_axes(fig, date_axes=True)

    # Range selector buttons on the top x-axis (row 1)
    fig.update_xaxes(
        rangeselector = _RANGE_SELECTOR_STYLE,
        row=1, col=1,
    )
    # Rangeslider on the bottom x-axis (row 3) for drag-to-zoom
    fig.update_xaxes(
        rangeslider = dict(
            visible    = True,
            thickness  = 0.04,
            bgcolor    = "#111827",
            bordercolor= "#1e3a5f",
        ),
        row=3, col=1,
    )
    return fig


def build_loss_chart(loss_history: dict) -> go.Figure:
    """Build a train vs. val loss curve chart.

    Args:
        loss_history: dict with 'train' and 'val' lists of per-epoch losses.

    Returns:
        A Plotly figure with two lines (train loss, val loss).
    """
    epochs = list(range(1, len(loss_history['train']) + 1))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=epochs, y=loss_history['train'],
        mode='lines', name='Train Loss',
        line=dict(color='#38bdf8', width=2),
    ))
    fig.add_trace(go.Scatter(
        x=epochs, y=loss_history['val'],
        mode='lines', name='Val Loss',
        line=dict(color='#818cf8', width=2, dash='dash'),
    ))

    # Mark the best val epoch
    best_epoch = int(np.argmin(loss_history['val'])) + 1
    best_val   = min(loss_history['val'])
    fig.add_vline(
        x=best_epoch, line_dash='dot',
        line_color='rgba(251,191,36,0.6)',
        annotation_text=f'Best epoch {best_epoch}',
        annotation_font_color='#fbbf24',
    )
    fig.add_annotation(
        x=best_epoch, y=best_val,
        text=f'  ▲ {best_val:.5f}',
        showarrow=False,
        font=dict(color='#fbbf24', size=11),
        xanchor='left',
    )

    fig.update_layout(
        height=320,
        xaxis_title='Epoch',
        yaxis_title='MSE Loss',
        **_LAYOUT_BASE,
    )
    _style_axes(fig)
    return fig


def build_macd_chart(df_raw: pd.DataFrame) -> go.Figure | None:
    """Build a MACD + Signal line chart.

    Returns None if MACD columns are absent.
    """
    if 'MACD' not in df_raw.columns or 'MACD_Signal' not in df_raw.columns:
        return None

    fig = make_subplots(rows=1, cols=1)

    macd_hist  = df_raw['MACD'] - df_raw['MACD_Signal']
    hist_colors = ['#4ade80' if v >= 0 else '#f87171' for v in macd_hist]

    fig.add_trace(go.Bar(
        x=df_raw.index, y=macd_hist,
        marker_color=hist_colors, name='MACD Histogram', opacity=0.5,
    ))
    fig.add_trace(go.Scatter(
        x=df_raw.index, y=df_raw['MACD'],
        mode='lines', name='MACD',
        line=dict(color='#38bdf8', width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=df_raw.index, y=df_raw['MACD_Signal'],
        mode='lines', name='Signal',
        line=dict(color='#f472b6', width=1.5, dash='dash'),
    ))
    fig.add_hline(y=0, line_color='rgba(255,255,255,0.15)')

    fig.update_layout(height=280, **_LAYOUT_BASE)
    _style_axes(fig, date_axes=True)
    fig.update_xaxes(rangeselector=_RANGE_SELECTOR_STYLE)
    return fig