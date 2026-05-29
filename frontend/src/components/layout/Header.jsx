import { Bell, Search } from 'lucide-react';

export default function Header({ isConnected, alertCount = 0 }) {
  return (
    <header style={{
      position: 'fixed', top: 0, right: 0, left: 'var(--sidebar-width)',
      height: 'var(--header-height)', zIndex: 40,
      background: 'rgba(255, 255, 255, 0.9)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-primary)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 28px',
      transition: 'left var(--transition-normal)',
    }}>
      {/* Search */}
      <div style={{ position: 'relative', width: 340 }}>
        <Search size={16} style={{
          position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
          color: '#94a3b8',
        }} />
        <input
          type="text"
          placeholder="Search events, alerts, users..."
          className="search-input"
        />
      </div>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        {/* Connection status */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 7,
          padding: '5px 12px', borderRadius: 8,
          background: isConnected ? '#ecfdf5' : '#fef2f2',
          fontSize: '0.75rem', fontWeight: 600,
          color: isConnected ? '#16a34a' : '#dc2626',
        }}>
          <div className={`live-dot ${isConnected ? '' : 'disconnected'}`} />
          {isConnected ? 'Live' : 'Offline'}
        </div>

        {/* Notifications */}
        <button style={{
          position: 'relative', background: '#f1f4f9', border: 'none',
          cursor: 'pointer', color: '#5f6d7e', padding: 9,
          borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Bell size={19} />
          {alertCount > 0 && (
            <span style={{
              position: 'absolute', top: 3, right: 3,
              width: 17, height: 17, borderRadius: '50%',
              background: '#ef4444',
              color: 'white', fontSize: '0.62rem', fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '2px solid white',
            }}>
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          )}
        </button>

        {/* User */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
          <div style={{
            width: 34, height: 34, borderRadius: '50%',
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.82rem', fontWeight: 600, color: 'white',
          }}>
            A
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1a1d26' }}>Analyst</span>
            <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>SOC Team</span>
          </div>
        </div>
      </div>
    </header>
  );
}
