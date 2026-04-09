import React, { useState, useCallback, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import Sidebar from './components/Sidebar.jsx'
import TrainingProgress from './components/TrainingProgress.jsx'
import MetricCards from './components/MetricCards.jsx'
import PriceChart from './components/PriceChart.jsx'
import { LossChart, MacdChart } from './components/LossAndMacdCharts.jsx'
import CommodityPanel from './components/CommodityPanel.jsx'
import GdpPanel from './components/GdpPanel.jsx'
import BondPanel from './components/BondPanel.jsx'
import { CorrelationPanel, AboutModal } from './components/CorrelationAndAbout.jsx'
import { streamAnalyze } from './api.js'

const DEFAULT_CONFIG = {
  ticker:        'AAPL',
  period:        730,
  seq_length:    60,
  forecast_days: 5,
  epochs:        50,
  patience:      10,
  hidden_size:   128,
  cnn_channels:  64,
  num_heads:     4,
  dropout:       0.2,
}

const TABS = [
  { id: 'price', label: 'Price Chart' },
  { id: 'model', label: 'Model Performance' },
  { id: 'macd',  label: 'MACD' },
]

const HAM_ITEMS = [
  { id: 'commodities',  label: 'Commodities' },
  { id: 'gdp',          label: 'GDP Growth' },
  { id: 'bonds',        label: 'Bond Yields' },
  { id: 'correlations', label: 'Correlations' },
]

export default function App() {
  const [config,      setConfig]      = useState(DEFAULT_CONFIG)
  const [running,     setRunning]     = useState(false)
  const [result,      setResult]      = useState(null)
  const [error,       setError]       = useState(null)
  const [statusMsgs,  setStatusMsgs]  = useState([])
  const [epochInfo,   setEpochInfo]   = useState(null)
  const [lossHistory, setLossHistory] = useState([])
  const [activeTab,   setActiveTab]   = useState('price')
  const [extraView,   setExtraView]   = useState(null)
  const [hamOpen,     setHamOpen]     = useState(false)
  const [showAbout,   setShowAbout]   = useState(false)

  const cancelRef = useRef(null)
  const hamRef    = useRef(null)
  const runGenRef = useRef(0)


  const handleRun = useCallback(() => {
    if (cancelRef.current) cancelRef.current()
    const gen = ++runGenRef.current   // bump generation — stale events from old run are ignored

    setRunning(true)
    setError(null)
    setResult(null)
    setStatusMsgs([])
    setEpochInfo(null)
    setLossHistory([])
    setExtraView(null)
    setActiveTab('price')
    setHamOpen(false)   // always close hamburger when starting a new run

    cancelRef.current = streamAnalyze(config, event => {
      if (runGenRef.current !== gen) return   // stale event from a previous run — discard
      switch (event.type) {
        case 'status':
          setStatusMsgs(prev => [...prev, event.message])
          break
        case 'epoch':
          setEpochInfo(event)
          setLossHistory(prev => [...prev, event.val_loss])
          break
        case 'result':
          setResult(event)
          setRunning(false)
          setEpochInfo(null)
          break
        case 'error':
          setError(event.message)
          setRunning(false)
          setEpochInfo(null)
          break
      }
    })
  }, [config])

  const handleHamItem = id => {
    setExtraView(prev => prev === id ? null : id)
    setHamOpen(false)
  }

  const currency = result?.currency ?? '$'
  const ticker   = result?.ticker   ?? config.ticker

  return (
    <div className="app-shell">
      <Sidebar config={config} onChange={setConfig} onRun={handleRun} running={running} />

      <div className="main-content">
        {/* Header */}
        <div className="tt-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Logo mark */}
            <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
              <rect width="38" height="38" rx="8" fill="rgba(251,176,59,0.1)" stroke="rgba(251,176,59,0.35)" strokeWidth="1"/>
              {/* Candlestick bars */}
              <rect x="8"  y="22" width="4" height="8"  rx="1" fill="#f87171" opacity="0.9"/>
              <line x1="10" y1="20" x2="10" y2="22" stroke="#f87171" strokeWidth="1.5" opacity="0.9"/>
              <line x1="10" y1="30" x2="10" y2="32" stroke="#f87171" strokeWidth="1.5" opacity="0.9"/>
              <rect x="17" y="14" width="4" height="10" rx="1" fill="#4ade80" opacity="0.9"/>
              <line x1="19" y1="11" x2="19" y2="14" stroke="#4ade80" strokeWidth="1.5" opacity="0.9"/>
              <line x1="19" y1="24" x2="19" y2="27" stroke="#4ade80" strokeWidth="1.5" opacity="0.9"/>
              <rect x="26" y="10" width="4" height="12" rx="1" fill="#4ade80" opacity="0.9"/>
              <line x1="28" y1="7"  x2="28" y2="10" stroke="#4ade80" strokeWidth="1.5" opacity="0.9"/>
              <line x1="28" y1="22" x2="28" y2="25" stroke="#4ade80" strokeWidth="1.5" opacity="0.9"/>
              {/* Trend arrow */}
              <polyline points="7,28 14,20 21,23 31,10" stroke="#fbb03b" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.85"/>
            </svg>
            <div>
              <div className="tt-title">
                Ticker<span>-</span>Teller
              </div>
              <div className="tt-subtitle">
                CNN → BiLSTM → Attention &nbsp;·&nbsp; Monte Carlo Forecast &nbsp;·&nbsp; 31 Features
              </div>
              {result && (
                <div className="tt-status-bar">
                  <span className="dot-live" />
                  <span>{ticker}</span>
                  <span style={{ color: 'var(--border-bright)' }}>·</span>
                  <span>{result.features?.total ?? 31} features</span>
                  <span style={{ color: 'var(--border-bright)' }}>·</span>
                  <span style={{ color: result.device === 'cuda' ? 'var(--green)' : 'var(--text-dim)' }}>
                    {result.device?.toUpperCase() ?? 'CPU'}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="tt-meta">
            FastAPI + React/Vite<br />
            <span className="tt-meta-version">v3.1.0</span>
          </div>
        </div>

        {/* Training progress */}
        {(running || statusMsgs.length > 0) && !result && (
          <TrainingProgress
            status={running}
            epochInfo={epochInfo}
            totalEpochs={config.epochs}
            statusMessages={statusMsgs}
            lossHistory={lossHistory}
          />
        )}

        {/* Error */}
        {error && <div className="error-msg">⚠ {error}</div>}

        {/* Results */}
        {result ? (
          <>
            <MetricCards
              summary={result.summary}
              metrics={result.metrics}
              currency={currency}
              forecastDays={config.forecast_days}
            />

            {/* Signal + data-split pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div className="signal-row">
                <span className="signal-label">AI Signal</span>
                {/* FIX: use result.summary.badge (now sent by backend) */}
                <span className={`badge badge-${result.summary?.badge ?? 'neutral'}`}>
                  {result.summary?.signal ?? '—'}
                </span>
              </div>
              <div className="split-pills">
                <span className="pill pill-train">
                  Train {result.splits?.n_train?.toLocaleString() ?? '—'}
                </span>
                <span className="pill pill-val">
                  Val {result.splits?.n_val?.toLocaleString() ?? '—'}
                </span>
                <span className="pill pill-test">
                  Test {result.splits?.n_test?.toLocaleString() ?? '—'}
                </span>
              </div>
            </div>

            {/* Model architecture expander */}
            <ModelExpander model={result.model} metrics={result.metrics} currency={currency} />

            {/* Tabs + hamburger — dropdown rendered via portal to escape all overflow clipping */}
            <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
              <div className="tabs" style={{ border: 'none', flex: 1 }}>
                {TABS.map(t => (
                  <button
                    key={t.id}
                    className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              <div style={{ flexShrink: 0, padding: '0 0.25rem' }} ref={hamRef}>
                <button className="ham-btn" onClick={() => setHamOpen(o => !o)}>
                  ☰ More Analysis
                </button>
              </div>
            </div>

            {/* Ham dropdown — portal renders it on document.body, outside all overflow containers */}
            <HamPortal
              open={hamOpen}
              anchorRef={hamRef}
              onClose={() => setHamOpen(false)}
            >
              <div className="ham-menu-label">Extended Analysis</div>
              {HAM_ITEMS.map(item => (
                <button
                  key={item.id}
                  className={`ham-item ${extraView === item.id ? 'active' : ''}`}
                  onClick={() => handleHamItem(item.id)}
                >
                  {item.label}
                </button>
              ))}
              {extraView && (
                <>
                  <hr className="ham-divider" />
                  <button
                    className="ham-item ham-close"
                    onClick={() => { setExtraView(null); setHamOpen(false) }}
                  >
                    ✕ Close panel
                  </button>
                </>
              )}
            </HamPortal>

            {/* Tab content */}
            {activeTab === 'price' && (
              <PriceChart charts={result.charts} currency={currency} />
            )}
            {activeTab === 'model' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <LossChart lossData={result.charts?.loss} />
                <TestMetricsTable metrics={result.metrics} currency={currency} />
              </div>
            )}
            {activeTab === 'macd' && (
              <MacdChart charts={result.charts} />
            )}

            {/* Extra panel */}
            {extraView && (
              <div className="extra-panel">
                <div className="extra-panel-header">
                  <div className="section-header" style={{ margin: 0 }}>
                    {HAM_ITEMS.find(i => i.id === extraView)?.label}
                  </div>
                  <button className="close-panel-btn" onClick={() => setExtraView(null)}>
                    ✕ Close
                  </button>
                </div>

                {extraView === 'commodities' && (
                  <CommodityPanel period={config.period} forecastDays={config.forecast_days} />
                )}
                {extraView === 'gdp' && (
                  <GdpPanel period={config.period} forecastDays={30} />
                )}
                {extraView === 'bonds' && (
                  /* BondPanel always fetches independently — no inline data needed */
                  <BondPanel period={config.period} />
                )}
                {extraView === 'correlations' && (
                  <CorrelationPanel correlations={result.charts?.correlations} />
                )}
              </div>
            )}

            {/* Footer */}
            <div className="footer">
              <span>
                Ticker-Teller v3.1 &nbsp;·&nbsp; {ticker} &nbsp;·&nbsp;
                {result.features?.total ?? 31} features ({result.features?.price ?? 17}p + {result.features?.macro ?? 14}m) &nbsp;·&nbsp;
                {result.device?.toUpperCase() ?? 'CPU'}
              </span>
              <button className="about-link" onClick={() => setShowAbout(true)}>
                ℹ About
              </button>
            </div>
          </>
        ) : !running && !error && (
          <LandingView onAbout={() => setShowAbout(true)} />
        )}
      </div>

      {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
    </div>
  )
}


// ── Ham Portal — renders dropdown on document.body to escape all overflow clipping ──
function HamPortal({ open, anchorRef, onClose, children }) {
  const [pos, setPos] = React.useState({ top: 0, right: 0 })
  const menuRef = React.useRef(null)

  React.useEffect(() => {
    if (!open || !anchorRef.current) return
    const rect = anchorRef.current.getBoundingClientRect()
    setPos({
      top:   rect.bottom + window.scrollY + 6,
      right: window.innerWidth - rect.right,
    })
  }, [open, anchorRef])

  React.useEffect(() => {
    if (!open) return
    const handler = e => {
      const inAnchor = anchorRef.current && anchorRef.current.contains(e.target)
      const inMenu   = menuRef.current   && menuRef.current.contains(e.target)
      if (!inAnchor && !inMenu) onClose()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open, anchorRef, onClose])

  if (!open) return null

  return createPortal(
    <div
      ref={menuRef}
      className="ham-menu"
      style={{ position: 'absolute', top: pos.top, right: pos.right, zIndex: 9999 }}
    >
      {children}
    </div>,
    document.body
  )
}

// ── Landing view ──────────────────────────────────────────────────────────────
function LandingView({ onAbout }) {
  const features = [
    { icon: '🧠', text: 'CNN → BiLSTM → Multi-Head Attention hybrid architecture' },
    { icon: '📊', text: '31 features — OHLCV, 12 technical indicators, 14 macro factors' },
    { icon: '🎲', text: 'Monte Carlo Dropout for calibrated uncertainty bands' },
    { icon: '📡', text: 'Live training progress streamed via Server-Sent Events' },
    { icon: '🌍', text: 'Bond yields, commodity forecasts & GDP proxies' },
  ]
  const tickers = ['AAPL', 'TSLA', 'MSFT', 'NVDA', 'RELIANCE.NS', 'BTC-USD']

  return (
    <div className="landing-box">
      <div style={{
        fontFamily: 'var(--font-display)',
        fontStyle: 'normal',
        fontWeight: 700,
        fontSize: '2.2rem',
        color: 'var(--text-bright)',
        marginBottom: '0.4rem',
        lineHeight: 1,
        letterSpacing: '-0.02em',
      }}>
        Ready to analyse.
      </div>
      <p style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '0.74rem',
        color: 'var(--text-muted)',
        lineHeight: 1.8,
        marginBottom: '1.4rem',
      }}>
        Enter a ticker symbol in the sidebar and press <strong style={{ color: 'var(--amber)' }}>Run</strong> to begin.
        The model fetches live data, engineers 31 features, trains a deep hybrid network,
        and streams progress in real time.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginBottom: '1.4rem' }}>
        {features.map(f => (
          <div key={f.text} style={{
            display: 'flex', alignItems: 'flex-start', gap: '0.7rem',
            fontFamily: 'var(--font-mono)', fontSize: '0.72rem',
            color: 'var(--text-muted)', lineHeight: 1.6,
          }}>
            <span style={{ fontSize: '0.85rem', flexShrink: 0, marginTop: '0.05rem' }}>{f.icon}</span>
            <span>{f.text}</span>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{
          fontFamily: 'var(--font-mono)', fontSize: '0.58rem',
          color: 'var(--text-dim)', letterSpacing: '0.12em',
          textTransform: 'uppercase', marginBottom: '0.5rem',
        }}>
          Quick start
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {tickers.map(sym => (
            <span key={sym} style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.66rem',
              padding: '3px 10px', borderRadius: '3px',
              background: 'var(--amber-subtle)',
              border: '1px solid var(--border-accent)',
              color: 'var(--amber)', letterSpacing: '0.06em',
              cursor: 'default',
            }}>
              {sym}
            </span>
          ))}
        </div>
      </div>

      <button className="about-link" onClick={onAbout} style={{ fontSize: '0.68rem' }}>
        ℹ Architecture, methodology &amp; disclaimer
      </button>
    </div>
  )
}

// ── Model expander ─────────────────────────────────────────────────────────────
function ModelExpander({ model, metrics, currency }) {
  const [open, setOpen] = useState(false)
  if (!model) return null
  const items = [
    { label: 'Total Parameters',    value: model.total_params?.toLocaleString()     ?? '—' },
    { label: 'Trainable Params',    value: model.trainable_params?.toLocaleString() ?? '—' },
    { label: 'RMSE (Test Set)',     value: metrics?.rmse != null ? `${currency}${metrics.rmse.toFixed(4)}` : '—' },
    { label: 'MAPE (Test Set)',     value: metrics?.mape != null ? `${metrics.mape.toFixed(2)}%`           : '—' },
  ]
  return (
    <div className="expander">
      <div className="expander-header" onClick={() => setOpen(o => !o)}>
        <span>Model Architecture &amp; Extended Metrics</span>
        <span style={{ color: 'var(--text-dim)', fontSize: '0.62rem', fontFamily: 'var(--font-mono)' }}>
          {model.total_params?.toLocaleString()} params &nbsp;{open ? '▲' : '▼'}
        </span>
      </div>
      {open && (
        <div className="expander-body">
          {items.map(({ label, value }) => (
            <div key={label} className="metric-card" style={{ minWidth: 140, flex: '1 1 140px' }}>
              <div className="metric-label">{label}</div>
              <div className="metric-value" style={{ fontSize: '1.1rem' }}>{value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Test metrics table ──────────────────────────────────────────────────────────
function TestMetricsTable({ metrics, currency }) {
  if (!metrics) return null
  const rows = [
    { label: 'MAE — Mean Absolute Error',       value: metrics.mae  != null ? `${currency}${metrics.mae.toFixed(4)}`  : '—' },
    { label: 'RMSE — Root Mean Squared Error',  value: metrics.rmse != null ? `${currency}${metrics.rmse.toFixed(4)}` : '—' },
    { label: 'MAPE — Mean Abs. % Error',        value: metrics.mape != null ? `${metrics.mape.toFixed(2)}%`           : '—' },
    { label: 'Directional Accuracy',            value: metrics.directional_accuracy != null ? `${metrics.directional_accuracy.toFixed(1)}%` : '—' },
  ]
  return (
    <div className="chart-wrap">
      <div className="chart-title">Test Set Metrics</div>
      <table className="data-table">
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.label}>
              <td style={{ color: 'var(--text-muted)' }}>{r.label}</td>
              <td style={{ color: 'var(--amber)', fontWeight: 600 }}>{r.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
