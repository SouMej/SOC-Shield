import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bell, Filter, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

function SeverityBadge({ severity }) {
  return <span className={`badge badge-${(severity || 'info').toLowerCase()}`}>{severity || 'INFO'}</span>;
}

function timeAgo(ts) {
  if (!ts) return '';
  const d = Date.now() - new Date(ts).getTime();
  const s = Math.floor(d / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);

  const fetchAlerts = async () => {
    try {
      const params = { size: 100, time_from: 'now-48h', acknowledged: false };
      if (filter !== 'all') params.severity = filter.toUpperCase();
      const data = await api.getAlerts(params);
      setAlerts(data);
    } catch (e) {
      console.error('Fetch alerts error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, [filter]);

  const handleAck = async (alert) => {
    if (!alert._index || !alert._id) return;
    await api.acknowledgeAlert(alert._index, alert._id);
    fetchAlerts();
  };

  const filters = ['all', 'critical', 'high', 'medium', 'low'];

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>
          <Bell size={24} style={{ verticalAlign: 'middle', marginRight: 10 }} />
          Alerts
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {alerts.length} alerts in the last 48 hours
        </p>
      </motion.div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {filters.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={filter === f ? 'btn btn-primary' : 'btn btn-ghost'}
            style={{ textTransform: 'capitalize' }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Alerts Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Attack Type</th>
              <th>Host</th>
              <th>User</th>
              <th>Score</th>
              <th>Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert, i) => (
              <motion.tr
                key={alert._id || i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.02 }}
                onClick={() => setSelected(selected === i ? null : i)}
                style={{ cursor: 'pointer' }}
              >
                <td><SeverityBadge severity={alert.severity} /></td>
                <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{alert.attack_type || 'Unknown'}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{alert.hostname || '—'}</td>
                <td>{alert.target_user || '—'}</td>
                <td>
                  <span style={{
                    fontWeight: 700, fontSize: '0.85rem',
                    color: (alert.threat_score || 0) >= 80 ? 'var(--severity-critical)' :
                           (alert.threat_score || 0) >= 50 ? 'var(--severity-high)' : 'var(--severity-medium)',
                  }}>
                    {alert.threat_score || 0}
                  </span>
                </td>
                <td style={{ fontSize: '0.78rem' }}>{timeAgo(alert['@timestamp'])}</td>
                <td>
                  {alert.acknowledged ? (
                    <span style={{ color: 'var(--severity-low)', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem' }}>
                      <CheckCircle size={14} /> Ack
                    </span>
                  ) : (
                    <span style={{ color: 'var(--severity-high)', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem' }}>
                      <Clock size={14} /> Pending
                    </span>
                  )}
                </td>
                <td>
                  {!alert.acknowledged && (
                    <button
                      className="btn btn-ghost"
                      style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                      onClick={(e) => { e.stopPropagation(); handleAck(alert); }}
                    >
                      Acknowledge
                    </button>
                  )}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>

        {alerts.length === 0 && (
          <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
            <AlertTriangle size={36} style={{ marginBottom: 12, opacity: 0.3 }} />
            <div>{loading ? 'Loading alerts...' : 'No alerts match your filters'}</div>
          </div>
        )}
      </div>

      {/* Alert Detail */}
      {selected !== null && alerts[selected] && (
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginTop: 20 }}
        >
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 12 }}>
            Alert Details
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, fontSize: '0.85rem' }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Attack Type:</span> <strong>{alerts[selected].attack_type}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Severity:</span> <SeverityBadge severity={alerts[selected].severity} /></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Host:</span> <strong>{alerts[selected].hostname}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>User:</span> <strong>{alerts[selected].target_user}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Source IP:</span> <strong>{alerts[selected].source_ip || '—'}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Score:</span> <strong>{alerts[selected].threat_score}</strong></div>
            <div style={{ gridColumn: '1 / -1' }}>
              <span style={{ color: 'var(--text-muted)' }}>Explanation:</span>
              <p style={{ marginTop: 6, lineHeight: 1.5 }}>{alerts[selected].explanation}</p>
            </div>
            {alerts[selected].mitre_techniques?.length > 0 && (
              <div style={{ gridColumn: '1 / -1' }}>
                <span style={{ color: 'var(--text-muted)' }}>MITRE Techniques:</span>
                <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                  {alerts[selected].mitre_techniques.map((t, j) => (
                    <span key={j} style={{
                      padding: '3px 8px', borderRadius: 6, fontSize: '0.75rem',
                      background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontFamily: 'monospace',
                    }}>{t}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
}
