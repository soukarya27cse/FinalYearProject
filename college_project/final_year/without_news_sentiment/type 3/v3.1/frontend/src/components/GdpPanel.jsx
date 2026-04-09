import React, { useEffect, useState } from 'react'
import {
  ComposedChart, Line, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts'
import { fetchGdp } from '../api.js'

const PALETTE = ['#38bdf8','#4ade80','#f472b6','#fbbf24','#818cf8','#f87171','#a78bfa']
const axisStyle = { fontFamily: 'IBM Plex Mono, monospace', fontSize: 9.5, fill: '#445566' }
const gridStyle  = { stroke: '#1e2d45', strokeDasharray: '3 3' }

function gdpColor(val) {
  if (val >= 3.0) return '#4ade80'
  if (val >= 1.5) return '#fbbf24'
  return '#f87171'
}

function GdpCard({ country, data }) {
  const current = data.current_annual_pct
  const fcast30 = data.forecast_pct?.slice(-1)[0] ?? current
  const delta   = fcast30 - current
  const dPos    = delta >= 0
  return (
    <div className="gdp-card">
      <div className="gdp-country">{country}</div>
      <div className="gdp-val" style={{ color: gdpColor(current) }}>{current.toFixed(1)}%</div>
      <div className="gdp-delta" style={{ color: dPos ? '#4ade80' : '#f87171' }}>
        30d Δ: {dPos ? '+' : ''}{delta.toFixed(2)}%
      </div>
      <div className="gdp-source">{data.source}</div>
    </div>
  )
}

export default function GdpPanel({ period = 730, forecastDays = 30, inlineData = null }) {
  const [data,    setData]    = useState(inlineData)
  const [loading, setLoading] = useState(!inlineData)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (inlineData) { setData(inlineData); return }
    setLoading(true)
    fetchGdp(period, forecastDays)
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [period, forecastDays, inlineData])

  if (loading) return <div className="status-msg"><span className="status-dot" />Loading GDP data…</div>
  if (error)   return <div className="error-msg">⚠ {error}</div>
  if (!data || !Object.keys(data).length) return <div className="status-msg">No GDP data available.</div>

  const items     = Object.entries(data)
  const countries = items.map(([c]) => c)

  const barData = items.map(([country, d]) => ({
    country, current: d.current_annual_pct, fill: gdpColor(d.current_annual_pct),
  }))

  const maxLen   = Math.max(...items.map(([, d]) => d.forecast_dates?.length ?? 0))
  const fcstRows = Array.from({ length: maxLen }, (_, i) => {
    const row = { date: items[0][1].forecast_dates?.[i] ?? `D${i + 1}` }
    items.forEach(([country, d]) => {
      row[country]         = d.forecast_pct?.[i]  ?? null
      row[country + '_up'] = d.upper_pct?.[i]     ?? null
      row[country + '_dn'] = d.lower_pct?.[i]     ?? null
    })
    return row
  })

  const tableRows = items.map(([country, d]) => {
    const current = d.current_annual_pct
    const f30     = d.forecast_pct?.slice(-1)[0] ?? current
    return { country, current, f30, delta: f30 - current, source: d.source }
  })

  return (
    <div>
      <div style={{ marginBottom: '0.6rem', fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color: 'var(--text-dim)' }}>
        Annualised 252-day ETF return proxy · Holt smoothing · ±1σ confidence bands
      </div>

      <div className="gdp-grid">
        {items.map(([country, d]) => <GdpCard key={country} country={country} data={d} />)}
      </div>

      <div className="chart-wrap" style={{ marginBottom: '0.75rem' }}>
        <div className="chart-title">Current Annualised GDP Growth (%)</div>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey="country" tick={axisStyle} />
            <YAxis tick={axisStyle} width={42} tickFormatter={v => `${v.toFixed(1)}%`} />
            <Tooltip
              contentStyle={{ background: '#0f1420', border: '1px solid #253650', borderRadius: 6, fontFamily: 'IBM Plex Mono, monospace', fontSize: '0.65rem' }}
              formatter={v => [`${v.toFixed(2)}%`]}
            />
            <Bar dataKey="current" name="GDP Growth %">
              {barData.map((entry, i) => <Cell key={i} fill={entry.fill} fillOpacity={0.85} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-wrap" style={{ marginBottom: '0.75rem' }}>
        <div className="chart-title">30-Session Forward Forecast with ±1σ Bands</div>
        <ResponsiveContainer width="100%" height={210}>
          <ComposedChart data={fcstRows} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey="date" tick={axisStyle} minTickGap={30} />
            <YAxis tick={axisStyle} width={47} tickFormatter={v => `${v.toFixed(1)}%`} />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                // Only show country lines — filter out _up / _dn band series
                const lines = payload.filter(p => p.value != null && !p.dataKey.endsWith('_up') && !p.dataKey.endsWith('_dn'))
                if (!lines.length) return null
                return (
                  <div style={{
                    background: '#0f1420',
                    border: '1px solid #253650',
                    borderRadius: 6,
                    padding: '0.4rem 0.7rem',
                    fontFamily: 'IBM Plex Mono, monospace',
                    fontSize: '0.64rem',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.75)',
                    minWidth: 140,
                  }}>
                    <div style={{ color: '#445566', fontSize: '0.57rem', marginBottom: '0.3rem' }}>{label}</div>
                    {lines.map((p, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: '1.2rem', padding: '1px 0' }}>
                        <span style={{ color: p.color }}>{p.name}</span>
                        <span style={{ color: '#edf2f7', fontWeight: 600 }}>{Number(p.value).toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                )
              }}
            />
            <Legend wrapperStyle={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '0.58rem', color: '#7a91aa', paddingTop: '4px', lineHeight: 1.6 }} />
            {countries.map((country, i) => {
              const color = PALETTE[i % PALETTE.length]
              return (
                <React.Fragment key={country}>
                  <Area dataKey={country + '_up'} stroke="transparent" fill={color + '10'} dot={false} activeDot={false} legendType="none" />
                  <Area dataKey={country + '_dn'} stroke="transparent" fill={color + '10'} dot={false} activeDot={false} legendType="none" />
                  <Line dataKey={country} stroke={color} dot={false} activeDot={{ r: 3, strokeWidth: 0, fill: color }} strokeWidth={2} name={country} />
                </React.Fragment>
              )
            })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-wrap" style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr><th>Country</th><th>Current (ann. %)</th><th>30-Day Forecast</th><th>Δ</th><th>Source</th></tr>
          </thead>
          <tbody>
            {tableRows.map(r => (
              <tr key={r.country}>
                <td style={{ color: 'var(--text)', fontWeight: 500 }}>{r.country}</td>
                <td style={{ color: gdpColor(r.current) }}>{r.current.toFixed(2)}%</td>
                <td style={{ color: gdpColor(r.f30) }}>{r.f30.toFixed(2)}%</td>
                <td className={r.delta >= 0 ? 'tbl-pos' : 'tbl-neg'}>{r.delta >= 0 ? '+' : ''}{r.delta.toFixed(2)}%</td>
                <td style={{ color: 'var(--text-dim)' }}>{r.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
