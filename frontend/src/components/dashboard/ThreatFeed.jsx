import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock } from 'lucide-react';

function timeAgo(timestamp) {
  if (!timestamp) return '';
  const diff = Date.now() - new Date(timestamp).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

export default function ThreatFeed({ alerts = [] }) {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <AlertTriangle size={18} color="#f97316" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>Live Threat Feed</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="live-dot" />
          <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{alerts.length} alerts</span>
        </div>
      </div>
      <div style={{ maxHeight: 420, overflowY: 'auto' }}>
        <AnimatePresence initial={false}>
          {alerts.slice(0, 20).map((alert, i) => (
            <motion.div key={alert.alert_id || alert._id || i}
              className={`threat-feed-item severity-${(alert.severity || 'info').toLowerCase()}`}
              initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span className={`badge badge-${(alert.severity || 'info').toLowerCase()}`}>{alert.severity || 'INFO'}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.7rem', color: '#94a3b8' }}>
                  <Clock size={11} /> {timeAgo(alert['@timestamp'])}
                </div>
              </div>
              <div style={{ fontSize: '0.85rem', fontWeight: 500, color: '#1a1d26', marginBottom: 4 }}>
                {alert.attack_type || 'Security Alert'}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#5f6d7e', lineHeight: 1.4 }}>
                {(alert.explanation || '').slice(0, 120)}{(alert.explanation || '').length > 120 ? '...' : ''}
              </div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: '0.72rem', color: '#94a3b8' }}>
                {alert.hostname && <span>🖥 {alert.hostname}</span>}
                {alert.target_user && <span>👤 {alert.target_user}</span>}
                {alert.threat_score > 0 && (
                  <span style={{ color: alert.threat_score >= 80 ? '#ef4444' : '#f97316', fontWeight: 600 }}>
                    Score: {alert.threat_score}
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {alerts.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
            <AlertTriangle size={32} style={{ marginBottom: 12, opacity: 0.3 }} />
            <div>No alerts yet — monitoring for threats...</div>
          </div>
        )}
      </div>
    </div>
  );
}
