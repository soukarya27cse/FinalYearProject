/**
 * api.js — Ticker-Teller Frontend API v3
 * Direct connection to backend (127.0.0.1:8000) to ensure SSE stability.
 */

const BASE = 'http://127.0.0.1:8000/api';

/**
 * Stream a POST request for stock analysis as Server-Sent Events (SSE).
 * @param {Object} config - The model configuration (ticker, epochs, etc.)
 * @param {Function} onEvent - Callback for parsed JSON events (status, epoch, result, error)
 * @returns {Function} - A function to abort the stream.
 */
export function streamAnalyze(config, onEvent) {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
        signal: controller.signal,
      });

      if (!res.ok) {
        onEvent({ type: 'error', message: `HTTP ${res.status}: ${res.statusText}` });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE frames are typically separated by double newlines
        let parts = buffer.split('\n\n');
        
        // Keep the last (potentially incomplete) part in the buffer
        buffer = parts.pop() || '';

        for (const part of parts) {
          // A single SSE message can contain multiple lines (e.g., data: {...})
          const lines = part.split('\n');
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data:')) {
              try {
                const dataString = trimmed.replace('data:', '').trim();
                if (dataString) {
                  const json = JSON.parse(dataString);
                  onEvent(json);
                }
              } catch (e) {
                console.warn("Failed to parse SSE line:", trimmed, e);
              }
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error("Stream Fetch Error:", err);
        onEvent({ type: 'error', message: err.message });
      }
    }
  })();

  return () => controller.abort();
}

/**
 * Fetches general metadata for a ticker (Sector, Industry, etc.)
 */
export async function fetchTickerInfo(ticker) {
  if (!ticker) return null;
  const res = await fetch(`${BASE}/ticker-info?ticker=${encodeURIComponent(ticker)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} - Failed to fetch ticker info`);
  return res.json();
}

/**
 * Fetches commodity historical data and Holt-Winters forecasts.
 */
export async function fetchCommodities(period = 730, forecastDays = 10) {
  const res = await fetch(`${BASE}/commodities?period=${period}&forecast_days=${forecastDays}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} - Failed to fetch commodities`);
  return res.json();
}

/**
 * Fetches GDP proxy data derived from country-specific ETFs.
 */
export async function fetchGdp(period = 730, forecastDays = 30) {
  const res = await fetch(`${BASE}/gdp?period=${period}&forecast_days=${forecastDays}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} - Failed to fetch GDP data`);
  return res.json();
}

/**
 * Fetches US Treasury Bond yields (5Y, 10Y) and their spread.
 */
export async function fetchBonds(period = 730) {
  const res = await fetch(`${BASE}/bonds?period=${period}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} - Failed to fetch bond yields`);
  return res.json();
}

/**
 * Basic health check for the FastAPI backend.
 */
export async function fetchHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(`HTTP ${res.status} - Backend unhealthy`);
  return res.json();
}