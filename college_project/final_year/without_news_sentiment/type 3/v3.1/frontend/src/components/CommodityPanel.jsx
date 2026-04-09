// CommodityPanel.jsx
import React, { useEffect, useState } from 'react'
import {
  ComposedChart, Line, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts'
import { fetchCommodities } from '../api.js'

const PALETTE = ['#fbbf24', '#94a3b8', '#b45309', '#9ca3af', '#60a5fa']
const COMM_NAMES = ['Gold', 'Silver', 'Copper', 'Aluminium', 'Brent Oil']

const axisStyle = { fontFamily: 'JetBrains Mono, monospace', fontSize: 9.5, fill: '#8c97a4' }
const gridStyle = { stroke: '#e2e6ea', strokeDasharray: '4 4' }

function pctColor(v) {
  if (v >  1) return 'var(--green)'
  if (v >  0) return '#4ade80aa'
  if (v < -1) return 'var(--red)'
  if (v <  0) return '#f87171aa'
  return 'var(--text-dim)'
}

function CommCard({ name, data, color }) {
  const pct = data.pct_change_1d ?? 0
  return (
    <div className="comm-card">
      <div className="comm-name" style={{ color }}>{name}</div>
      <div className="comm-price">${data.last_price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      <div className="comm-delta" style={{ color: pctColor(pct) }}>
        {pct >= 0 ? '▲' : '▼'} {Math.abs(pct).toFixed(2)}% (1d)
      </div>
    </div>
  )
}

export default function CommodityPanel({ period = 730, forecastDays = 10 }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    setLoading(true); setError(null)
    fetchCommodities(period, forecastDays)
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [period, forecastDays])

  if (loading) return <div className="status-msg"><span className="status-dot" />Loading commodity data…</div>
  if (error)   return <div className="error-msg">⚠ {error}</div>
  if (!data || !Object.keys(data).length) return <div className="status-msg">Commodity data not available.</div>

  const entries = Object.entries(data)

  const maxLen  = Math.max(...entries.map(([, d]) => d.dates?.length ?? 0))
  const fcstRows = Array.from({ length: maxLen }, (_, i) => {
    const row = { date: entries[0]?.[1]?.dates?.[i] ?? `D${i + 1}` }
    entries.forEach(([name, d]) => {
      row[name]        = d.means?.[i]  ?? null
      row[name + '_u'] = d.upper?.[i]  ?? null
      row[name + '_l'] = d.lower?.[i]  ?? null
    })
    return row
  })

  const histLen  = Math.max(...entries.map(([, d]) => d.history_prices?.length ?? 0))
  const histRows = Array.from({ length: histLen }, (_, i) => {
    const row = { date: entries[0]?.[1]?.history_dates?.[i] ?? `H${i + 1}` }
    entries.forEach(([name, d]) => {
      const offset = histLen - (d.history_prices?.length ?? 0)
      row[name] = i >= offset ? (d.history_prices?.[i - offset] ?? null) : null
    })
    return row
  })

  return (
    <div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
        Holt-Winters double exponential smoothing · Yahoo Finance futures data
      </div>

      <div className="comm-grid">
        {entries.map(([name, d], i) => (
          <CommCard key={name} name={name} data={d} color={PALETTE[i % PALETTE.length]} />
        ))}
      </div>

      {histRows.length > 0 && (
        <div className="chart-wrap" style={{ marginBottom: '0.75rem' }}>
          <div className="chart-title">Historical Prices (Last 90 Sessions)</div>
          <ResponsiveContainer width="100%" height={210}>
            <ComposedChart data={histRows} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid {...gridStyle} />
              <XAxis dataKey="date" tick={axisStyle} minTickGap={45} />
              <YAxis tick={axisStyle} width={62} tickFormatter={v => `$${v >= 1000 ? `${(v/1000).toFixed(1)}k` : v.toFixed(0)}`} />
              <Tooltip
                contentStyle={{ background: '#ffffff', border: '1px solid #e2e6ea', borderRadius: 6, fontFamily: 'JetBrains Mono, monospace', fontSize: '0.65rem', color: '#1a2332' }}
                formatter={(v, name) => v != null ? [`$${Number(v).toFixed(2)}`, name] : ['—', name]}
              />
              <Legend wrapperStyle={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.6rem', color: '#8c97a4' }} />
              {entries.map(([name], i) => (
                <Line key={name} dataKey={name} stroke={PALETTE[i % PALETTE.length]} dot={false} strokeWidth={1.5} name={name} connectNulls />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="chart-wrap" style={{ marginBottom: '0.75rem' }}>
        <div className="chart-title">{forecastDays}-Session Forward Forecast with ±1σ Bands</div>
        <ResponsiveContainer width="100%" height={210}>
          <ComposedChart data={fcstRows} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey="date" tick={axisStyle} minTickGap={30} />
            <YAxis tick={axisStyle} width={62} tickFormatter={v => `$${v >= 1000 ? `${(v/1000).toFixed(1)}k` : v.toFixed(0)}`} />
            <Tooltip
              contentStyle={{ background: '#ffffff', border: '1px solid #e2e6ea', borderRadius: 6, fontFamily: 'JetBrains Mono, monospace', fontSize: '0.65rem', color: '#1a2332' }}
              formatter={(v, name) => v != null ? [`$${Number(v).toFixed(2)}`, name] : ['—', name]}
            />
            <Legend wrapperStyle={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.6rem', color: '#8c97a4' }} />
            {entries.map(([name], i) => {
              const color = PALETTE[i % PALETTE.length]
              return (
                <React.Fragment key={name}>
                  <Area dataKey={name + '_u'} stroke="transparent" fill={color + '12'} dot={false} legendType="none" />
                  <Area dataKey={name + '_l'} stroke="transparent" fill={color + '12'} dot={false} legendType="none" />
                  <Line dataKey={name} stroke={color} dot={false} strokeWidth={1.8} name={name} />
                </React.Fragment>
              )
            })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-wrap" style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr><th>Commodity</th><th>Last Price</th><th>1d Forecast</th><th>Δ%</th><th>α</th><th>β</th></tr>
          </thead>
          <tbody>
            {entries.map(([name, d], i) => {
              const pct = d.pct_change_1d ?? 0
              return (
                <tr key={name}>
                  <td style={{ color: PALETTE[i % PALETTE.length], fontWeight: 500 }}>{name}</td>
                  <td>${d.last_price?.toFixed(2)}</td>
                  <td>${d.means?.[0]?.toFixed(2) ?? '—'}</td>
                  <td className={pct >= 0 ? 'tbl-pos' : 'tbl-neg'}>{pct >= 0 ? '+' : ''}{pct.toFixed(2)}%</td>
                  <td style={{ color: 'var(--text-dim)' }}>{d.alpha}</td>
                  <td style={{ color: 'var(--text-dim)' }}>{d.beta}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}