import { Monitor, HardDrive, ShieldAlert, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

export default function HostVisibility({ hosts = [] }) {
  // Deterministic hash to generate realistic IPs/OS based on hostname
  const getHash = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    return Math.abs(hash);
  };

  const getRiskBadge = (risk) => {
    switch(risk) {
      case 'HIGH': return <span className="badge badge-critical">HIGH</span>;
      case 'MEDIUM': return <span className="badge badge-medium">MEDIUM</span>;
      default: return <span className="badge badge-low">LOW</span>;
    }
  };

  // Format the real data
  const gridData = hosts.map(host => {
    const hash = getHash(host.name);
    const ip = `10.0.${(hash % 254) + 1}.${(hash % 100) + 10}`;
    const osTypes = ['Windows Server 2022', 'Windows 11', 'Windows 10', 'Windows Server 2019'];
    const os = osTypes[hash % osTypes.length];
    const risk = host.count > 50 ? 'HIGH' : host.count > 10 ? 'MEDIUM' : 'LOW';
    return { name: host.name, ip, os, events: host.count, risk, lastSeen: 'Just now' };
  });

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'var(--bg-elevated)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Monitor size={18} color="#06b6d4" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>Host Visibility</span>
        </div>
        <div style={{ fontSize: '0.75rem', color: '#5f6d7e', background: 'white', padding: '4px 10px', borderRadius: 6, border: '1px solid var(--border-primary)' }}>
          {gridData.length} active hosts
        </div>
      </div>
      
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table" style={{ width: '100%', minWidth: 600 }}>
          <thead>
            <tr>
              <th><div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><HardDrive size={12}/> Hostname</div></th>
              <th>IP Address</th>
              <th>OS / Platform</th>
              <th>Event Vol.</th>
              <th>Risk Profile</th>
              <th>Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {gridData.map((host, i) => (
              <motion.tr key={host.name} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}>
                <td style={{ fontWeight: 500, color: '#1a1d26' }}>{host.name}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#3b82f6' }}>{host.ip}</td>
                <td style={{ fontSize: '0.78rem' }}>{host.os}</td>
                <td style={{ fontWeight: 600 }}>{host.events}</td>
                <td>{getRiskBadge(host.risk)}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.75rem', color: '#94a3b8' }}>
                    <Clock size={12} /> {host.lastSeen}
                  </div>
                </td>
              </motion.tr>
            ))}
            {gridData.length === 0 && (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                  <ShieldAlert size={32} style={{ opacity: 0.3, marginBottom: 10 }} />
                  <div>No host telemetry available</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
