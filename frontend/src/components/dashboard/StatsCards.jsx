import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, ShieldAlert, Cpu, TrendingUp } from 'lucide-react';

function AnimatedNumber({ value, duration = 1000 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    const start = display;
    const diff = value - start;
    if (diff === 0) return;
    const startTime = Date.now();
    const step = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) ref.current = requestAnimationFrame(step);
    };
    ref.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(ref.current);
  }, [value]);

  return <span>{display.toLocaleString()}</span>;
}

const cards = [
  { key: 'totalEvents', label: 'Total Events', icon: Activity, accent: 'accent-blue', color: '#3b82f6', bgColor: '#eff6ff' },
  { key: 'activeAlerts', label: 'Active Alerts', icon: AlertTriangle, accent: 'accent-orange', color: '#f97316', bgColor: '#fff7ed' },
  { key: 'criticalThreats', label: 'Critical Threats', icon: ShieldAlert, accent: 'accent-red', color: '#ef4444', bgColor: '#fef2f2' },
  { key: 'aiAnalyses', label: 'AI Analyses', icon: Cpu, accent: 'accent-purple', color: '#8b5cf6', bgColor: '#f3f0ff' },
];

export default function StatsCards({ stats, aiCount = 0 }) {
  const values = {
    totalEvents: stats?.events?.total || 0,
    activeAlerts: stats?.alerts?.unacknowledged || 0,
    criticalThreats: (stats?.alerts?.by_severity || []).find(s => s.name === 'CRITICAL')?.count || 0,
    aiAnalyses: aiCount,
  };

  return (
    <div className="stats-grid">
      {cards.map(({ key, label, icon: Icon, accent, color, bgColor }, i) => (
        <motion.div
          key={key}
          className={`stat-card ${accent}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08, duration: 0.4 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', fontWeight: 500, marginBottom: 10 }}>
                {label}
              </div>
              <div style={{ fontSize: '1.85rem', fontWeight: 700, color: '#1a1d26', lineHeight: 1 }}>
                <AnimatedNumber value={values[key]} />
              </div>
            </div>
            <div style={{
              width: 44, height: 44, borderRadius: 12,
              background: bgColor, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
            }}>
              <Icon size={22} color={color} />
            </div>
          </div>
          <div style={{
            marginTop: 14, display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span className="trend-badge up">
              <TrendingUp size={12} />
              +12%
            </span>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>vs last 24h</span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
