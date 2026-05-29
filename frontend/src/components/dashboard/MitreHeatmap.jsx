import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';
import { api } from '../../services/api';

const TACTICS = [
  'Reconnaissance', 'Resource Development', 'Initial Access', 'Execution',
  'Persistence', 'Privilege Escalation', 'Defense Evasion', 'Credential Access',
  'Discovery', 'Lateral Movement', 'Collection', 'Command and Control',
  'Exfiltration', 'Impact',
];

export default function MitreHeatmap() {
  const [data, setData] = useState([]);

  useEffect(() => {
    api.getMitreHeatmap().then(setData).catch(() => {});
    const interval = setInterval(() => {
      api.getMitreHeatmap().then(setData).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const maxCount = Math.max(...data.flatMap(t => (t.techniques || []).map(tc => tc.count || 0)), 1);

  return (
    <div className="card">
      <div style={{ marginBottom: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
        <Shield size={18} color="#3b82f6" />
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>MITRE ATT&CK Coverage</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', gap: 6, minWidth: 800 }}>
          {(data.length > 0 ? data : TACTICS.map(t => ({ tactic: t, techniques: [] }))).map((tactic, ti) => (
            <div key={tactic.tactic} style={{ flex: 1, minWidth: 55 }}>
              <div style={{
                fontSize: '0.62rem', fontWeight: 600, color: '#94a3b8',
                textAlign: 'center', marginBottom: 10, height: 28,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                lineHeight: 1.2, textTransform: 'uppercase', letterSpacing: '0.04em',
              }}>
                {tactic.tactic.replace(' and ', ' & ')}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {(tactic.techniques || []).map((tech, i) => {
                  const intensity = maxCount > 0 ? (tech.count || 0) / maxCount : 0;
                  const bg = intensity > 0
                    ? `rgba(239, 68, 68, ${0.1 + intensity * 0.9})`
                    : '#f8f9fc';
                  const color = intensity > 0.4 ? 'white' : intensity > 0 ? '#ef4444' : '#94a3b8';
                  return (
                    <motion.div key={tech.id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      transition={{ delay: ti * 0.02 + i * 0.01 }}
                      title={`${tech.id}: ${tech.name} (${tech.count || 0} detections)`}
                      style={{
                        padding: '5px 3px', borderRadius: 4, background: bg, textAlign: 'center',
                        fontSize: '0.58rem', color, cursor: 'pointer', transition: 'all 150ms',
                        fontFamily: 'monospace', fontWeight: intensity > 0 ? 600 : 400,
                      }}>
                      {tech.id}
                    </motion.div>
                  );
                })}
                {(tactic.techniques || []).length === 0 && (
                  <div style={{
                    padding: '8px 3px', borderRadius: 4, background: '#f8f9fc',
                    textAlign: 'center', fontSize: '0.55rem', color: '#cbd5e1',
                  }}>—</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
