import { motion } from 'framer-motion';
import { Monitor } from 'lucide-react';

export default function TopHosts({ hosts = [] }) {
  const maxCount = Math.max(...hosts.map(h => h.count), 1);

  return (
    <div className="card">
      <div style={{ marginBottom: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
        <Monitor size={18} color="#06b6d4" />
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>Top Attacked Hosts</span>
      </div>
      {hosts.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {hosts.slice(0, 8).map((host, i) => (
            <motion.div key={host.name} initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
              style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 34, height: 34, borderRadius: 10, background: '#f0fdfa',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <Monitor size={16} color="#06b6d4" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: '0.84rem', fontWeight: 500, fontFamily: 'monospace', color: '#1a1d26' }}>{host.name}</span>
                  <span style={{ fontSize: '0.75rem', color: '#06b6d4', fontWeight: 600 }}>{host.count}</span>
                </div>
                <div style={{ height: 5, borderRadius: 3, background: '#f1f4f9', overflow: 'hidden' }}>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${(host.count / maxCount) * 100}%` }}
                    transition={{ duration: 0.6, delay: i * 0.05 }}
                    style={{ height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, #06b6d4, #22d3ee)' }} />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>No host data yet</div>
      )}
    </div>
  );
}
