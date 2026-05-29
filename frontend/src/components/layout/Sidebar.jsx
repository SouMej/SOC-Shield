import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Bell, Search, Shield, Settings,
  ChevronLeft, ChevronRight, Zap, History
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/alerts', icon: Bell, label: 'Alerts' },
  { path: '/search', icon: Search, label: 'Log Search' },
  { path: '/mitre', icon: Shield, label: 'MITRE ATT&CK' },
  { path: '/history', icon: History, label: 'Threat History' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ collapsed, onToggle }) {
  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 250 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      style={{
        position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50,
        background: '#ffffff',
        borderRight: '1px solid var(--border-primary)',
        display: 'flex', flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Logo */}
      <div style={{
        padding: collapsed ? '20px 16px' : '20px 22px',
        display: 'flex', alignItems: 'center', gap: 11,
        minHeight: 'var(--header-height)',
      }}>
        <div style={{
          width: 34, height: 34, borderRadius: 10,
          background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, boxShadow: '0 2px 8px rgba(59,130,246,0.3)',
        }}>
          <Shield size={18} color="white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
            >
              <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1a1d26' }}>
                SOC<span style={{ color: '#3b82f6' }}>Shield</span>
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {navItems.map(({ path, icon: Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 12,
              padding: collapsed ? '11px 16px' : '10px 14px',
              borderRadius: 10,
              color: isActive ? '#3b82f6' : '#5f6d7e',
              background: isActive ? '#eff6ff' : 'transparent',
              textDecoration: 'none',
              fontSize: '0.875rem', fontWeight: isActive ? 600 : 450,
              transition: 'all 150ms ease',
              justifyContent: collapsed ? 'center' : 'flex-start',
            })}
          >
            <Icon size={19} style={{ flexShrink: 0 }} />
            <AnimatePresence>
              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  {label}
                </motion.span>
              )}
            </AnimatePresence>
          </NavLink>
        ))}
      </nav>

      {/* Bottom info */}
      {!collapsed && (
        <div style={{
          padding: '16px 18px', borderTop: '1px solid var(--border-subtle)',
          margin: '0 10px',
        }}>
          <div style={{
            padding: '12px 14px', borderRadius: 12,
            background: 'linear-gradient(135deg, #eff6ff, #f3f0ff)',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Zap size={16} color="white" />
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#1a1d26' }}>AI Engine</div>
              <div style={{ fontSize: '0.68rem', color: '#5f6d7e' }}>Groq · LangGraph</div>
            </div>
          </div>
        </div>
      )}

      {/* Toggle */}
      <button
        onClick={onToggle}
        style={{
          padding: '14px', borderTop: '1px solid var(--border-subtle)',
          background: 'transparent', border: 'none', cursor: 'pointer',
          color: '#94a3b8', display: 'flex', justifyContent: 'center',
        }}
      >
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </motion.aside>
  );
}
