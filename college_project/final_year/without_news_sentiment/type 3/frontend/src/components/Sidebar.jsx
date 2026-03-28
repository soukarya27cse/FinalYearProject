import React, { useState } from 'react'

const SliderField = ({ label, value, onChange, min, max, step = 1, color = 'var(--amber)', hint }) => (
  <div>
    <div className="sidebar-label" title={hint}>{label}</div>
    <div className="slider-row">
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={e => onChange(step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value))}
        style={{ accentColor: color }}
      />
      <span className="slider-val" style={{ color }}>{value}</span>
    </div>
  </div>
)

const SelectField = ({ label, value, onChange, options, color = 'var(--amber)' }) => (
  <div>
    <div className="sidebar-label">{label}</div>
    <select value={value} onChange={e => onChange(parseInt(e.target.value))}>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  </div>
)

export default function Sidebar({ config, onChange, onRun, running }) {
  const [modelOpen, setModelOpen] = useState(true)
  const set = key => val => onChange({ ...config, [key]: val })

  return (
    <div className="sidebar">
      {/* Logo */}
      <div style={{ marginBottom: '0.25rem' }}>
        <div style={{
          fontFamily: 'var(--font-display)',
          fontStyle: 'italic',
          fontSize: '1.55rem',
          color: 'var(--text-bright)',
          lineHeight: 1,
          letterSpacing: '0.01em',
        }}>
          Ticker<span style={{ color: 'var(--amber)' }}>-</span>Teller
        </div>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.54rem',
          color: 'var(--text-dim)',
          letterSpacing: '0.16em',
          marginTop: '0.25rem',
          textTransform: 'uppercase',
        }}>
          Neural Market Intelligence
        </div>
      </div>

      {/* Data section */}
      <div className="sidebar-section-title">Data</div>

      <div>
        <div className="sidebar-label">Ticker Symbol</div>
        <input
          type="text"
          value={config.ticker}
          onChange={e => onChange({ ...config, ticker: e.target.value.toUpperCase() })}
          placeholder="e.g. AAPL, RELIANCE.NS"
          style={{ textTransform: 'uppercase', letterSpacing: '0.1em' }}
        />
      </div>

      <SliderField
        label="History Window (Days)"
        value={config.period}
        onChange={set('period')}
        min={365} max={1825}
        hint="Calendar days of price history to download"
      />
      <SliderField
        label="Lookback Sequence (Days)"
        value={config.seq_length}
        onChange={set('seq_length')}
        min={10} max={120}
        hint="Past trading days the model sees per prediction"
      />
      <SliderField
        label="Forecast Horizon (Days)"
        value={config.forecast_days}
        onChange={set('forecast_days')}
        min={1} max={30}
        color="var(--green)"
        hint="Future business days to project"
      />

      {/* Model section */}
      <div
        className="sidebar-section-title"
        style={{ cursor: 'pointer', userSelect: 'none' }}
        onClick={() => setModelOpen(o => !o)}
      >
        Model Architecture
        <span style={{ marginLeft: 'auto', fontSize: '0.6rem', color: 'var(--text-dim)' }}>
          {modelOpen ? '▲' : '▼'}
        </span>
      </div>

      {modelOpen && (
        <>
          <SelectField
            label="BiLSTM Hidden Size"
            value={config.hidden_size}
            onChange={set('hidden_size')}
            options={[32, 64, 128, 256]}
            color="var(--purple)"
          />
          <SelectField
            label="CNN Channels"
            value={config.cnn_channels}
            onChange={set('cnn_channels')}
            options={[32, 64, 128]}
            color="var(--purple)"
          />
          <SelectField
            label="Attention Heads"
            value={config.num_heads}
            onChange={set('num_heads')}
            options={[2, 4, 8]}
            color="var(--purple)"
          />
          <SliderField
            label="Dropout Rate"
            value={config.dropout}
            onChange={set('dropout')}
            min={0} max={0.5} step={0.05}
            color="var(--cyan)"
            hint="MC-Dropout rate — controls uncertainty band width"
          />
        </>
      )}

      {/* Training section */}
      <div className="sidebar-section-title">Training</div>

      <SliderField
        label="Max Epochs"
        value={config.epochs}
        onChange={set('epochs')}
        min={5} max={200}
        color="var(--purple)"
      />
      <SliderField
        label="Early-Stop Patience"
        value={config.patience}
        onChange={set('patience')}
        min={3} max={30}
        color="var(--purple)"
        hint="Stop if val-loss doesn't improve for N epochs"
      />

      {/* Run button */}
      <button
        className="run-btn"
        onClick={onRun}
        disabled={running || !config.ticker.trim()}
      >
        {running ? '⏳  Analysing…' : `▶  Run  ${config.ticker || '—'}`}
      </button>

      {/* Legend */}
      <div className="sidebar-legend">
        <div><span className="legend-dot" style={{ background: 'var(--amber)' }} />OHLCV + Tech Indicators</div>
        <div><span className="legend-dot" style={{ background: 'var(--purple)' }} />SMA · RSI · MACD · BB · RVI</div>
        <div><span className="legend-dot" style={{ background: 'var(--pink)' }} />CNN → BiLSTM → Attention</div>
        <div><span className="legend-dot" style={{ background: 'var(--green)' }} />Monte Carlo Forecast</div>
        <div><span className="legend-dot" style={{ background: 'var(--cyan)' }} />Bond Yields 5Y &amp; 10Y</div>
        <div><span className="legend-dot" style={{ background: '#fbbf24' }} />Gold · Silver · Copper · Oil</div>
        <div><span className="legend-dot" style={{ background: 'var(--violet)' }} />Buffett Proxy + GDP</div>
      </div>
    </div>
  )
}
