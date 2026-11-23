/**
 * API client connecting the React frontend to the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Handle API responses and uniform error reporting.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (_) {
      // ignore
    }
    throw new Error(`API Error (${response.status}): ${errorDetail}`);
  }
  return response.json();
}

/**
 * Fetch high-level KPIs and data quality audit metrics.
 */
export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/api/summary`);
  return handleResponse(res);
}

/**
 * Fetch aggregated trade lanes metrics.
 */
export async function fetchTradeLanes() {
  const res = await fetch(`${API_BASE}/api/trade-lanes`);
  return handleResponse(res);
}

/**
 * Fetch top delayed shipments.
 */
export async function fetchTopDelayed(limit = 10) {
  const res = await fetch(`${API_BASE}/api/top-delayed?limit=${limit}`);
  return handleResponse(res);
}

/**
 * Fetch filterable shipments list with optional search term, mode, carrier, and status.
 */
export async function fetchShipments({ q = '', mode = '', carrier = '', status = '', trade_lane = '', limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (q) params.append('q', q);
  if (mode) params.append('mode', mode);
  if (carrier) params.append('carrier', carrier);
  if (status) params.append('status', status);
  if (trade_lane) params.append('trade_lane', trade_lane);
  if (limit) params.append('limit', limit.toString());
  if (offset) params.append('offset', offset.toString());

  const res = await fetch(`${API_BASE}/api/shipments?${params.toString()}`);
  const data = await handleResponse(res);
  const totalHeader = res.headers.get('X-Total-Count');
  return {
    items: data,
    total: totalHeader ? parseInt(totalHeader, 10) : data.length,
  };
}

/**
 * Fetch detailed record for a single shipment.
 */
export async function fetchShipmentById(shipmentId) {
  const res = await fetch(`${API_BASE}/api/shipments/${encodeURIComponent(shipmentId)}`);
  return handleResponse(res);
}

/**
 * Natural language grounded synthesis query ("Ask the Data").
 */
export async function askData(question) {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return handleResponse(res);
}
