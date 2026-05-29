import { motion } from 'framer-motion';
import { User } from 'lucide-react';

const AVATAR_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#f97316', '#10b981', '#ec4899', '#6366f1', '#14b8a6'];

export default function TopUsers({ users = [] }) {
  const maxCount = Math.max(...users.map(u => u.count), 1);

  return (
    <div className="card">
      <div style={{ marginBottom: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
        <User size={18} color="#8b5cf6" />
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>Top Suspicious Users</span>
      </div>
      {users.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {users.slice(0, 8).map((user, i) => (
            <motion.div key={user.name} initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
              style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 34, height: 34, borderRadius: 10,
                background: AVATAR_COLORS[i % AVATAR_COLORS.length],
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.78rem', fontWeight: 600, color: 'white', flexShrink: 0,
              }}>
                {(user.name || '?')[0].toUpperCase()}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: '0.84rem', fontWeight: 500, color: '#1a1d26' }}>{user.name}</span>
                  <span style={{ fontSize: '0.75rem', color: '#f97316', fontWeight: 600 }}>{user.count}</span>
                </div>
                <div style={{ height: 5, borderRadius: 3, background: '#f1f4f9', overflow: 'hidden' }}>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${(user.count / maxCount) * 100}%` }}
                    transition={{ duration: 0.6, delay: i * 0.05 }}
                    style={{ height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, #f97316, #fb923c)' }} />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>No user data yet</div>
      )}
    </div>
  );
}
