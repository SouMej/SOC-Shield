/**
 * API Service — Centralized API client for the SOC backend.
 */
const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  // Dashboard
  getStats: (timeFrom = 'now-24h') =>
    request(`/dashboard/stats?time_from=${timeFrom}`),
  getSeverityDistribution: (timeFrom = 'now-24h') =>
    request(`/dashboard/severity-distribution?time_from=${timeFrom}`),
  getAttackTimeline: (timeFrom = 'now-24h', interval = '1h') =>
    request(`/dashboard/attack-timeline?time_from=${timeFrom}&interval=${interval}`),
  getMitreHeatmap: (timeFrom = 'now-7d') =>
    request(`/dashboard/mitre-heatmap?time_from=${timeFrom}`),
  getAiAnalyses: (size = 20) =>
    request(`/dashboard/ai-analyses?size=${size}`),
  getHealth: () => request('/dashboard/health'),

  // Alerts
  getAlerts: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.severity) qs.set('severity', params.severity);
    if (params.size) qs.set('size', params.size);
    if (params.time_from) qs.set('time_from', params.time_from);
    return request(`/alerts?${qs.toString()}`);
  },
  acknowledgeAlert: (index, id) =>
    request(`/alerts/${index}/${id}/acknowledge`, { method: 'POST' }),

  // Search
  searchEvents: (body) =>
    request('/search', { method: 'POST', body: JSON.stringify(body) }),
  getRecentEvents: (size = 50) =>
    request(`/search/recent?size=${size}`),
  getCategories: () => request('/search/categories'),
};
