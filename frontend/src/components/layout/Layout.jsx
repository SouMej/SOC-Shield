import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout({ isConnected, alertCount }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="app-layout">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <Header isConnected={isConnected} alertCount={alertCount} />
      <main
        className={`main-content ${collapsed ? 'collapsed' : ''}`}
        style={{ marginLeft: collapsed ? 72 : 260 }}
      >
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
