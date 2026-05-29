import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import StatsCards from '../components/dashboard/StatsCards';
import ThreatFeed from '../components/dashboard/ThreatFeed';
import SeverityChart from '../components/dashboard/SeverityChart';
import AttackTimeline from '../components/dashboard/AttackTimeline';
import TopUsers from '../components/dashboard/TopUsers';
import HostVisibility from '../components/dashboard/HostVisibility';
import AIAnalysisPanel from '../components/dashboard/AIAnalysisPanel';
import MitreHeatmap from '../components/dashboard/MitreHeatmap';

export default function DashboardPage({ wsAlerts = [] }) {
  const [stats, setStats] = useState(null);
  const [severity, setSeverity] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [aiAnalyses, setAiAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsData, sevData, tlData, aiData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getSeverityDistribution().catch(() => []),
        api.getAttackTimeline().catch(() => []),
        api.getAiAnalyses().catch(() => []),
      ]);
      if (statsData) setStats(statsData);
      setSeverity(sevData);
      setTimeline(tlData);
      setAiAnalyses(aiData);
    } catch (e) {
      console.error('Dashboard fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 12000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {/* Page Title */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: 24 }}
      >
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>
          SOC Dashboard
        </h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Real-time Active Directory threat monitoring & AI-powered analysis
        </p>
      </motion.div>

      {/* Stats Cards */}
      <div style={{ marginBottom: 20 }}>
        <StatsCards stats={stats} aiCount={aiAnalyses.length} />
      </div>

      {/* Row 1: Timeline + Severity */}
      <div className="dashboard-grid" style={{ marginBottom: 20 }}>
        <AttackTimeline data={timeline} />
        <SeverityChart data={severity} />
      </div>

      {/* Row 2: Threat Feed + AI Panel */}
      <div className="dashboard-grid" style={{ marginBottom: 20 }}>
        <ThreatFeed alerts={wsAlerts} />
        <AIAnalysisPanel analyses={aiAnalyses} />
      </div>

      {/* Row 3: Top Users + Host Visibility */}
      <div className="dashboard-grid" style={{ marginBottom: 20 }}>
        <TopUsers users={stats?.alerts?.top_users || []} />
        <HostVisibility hosts={stats?.events?.by_hostname || []} />
      </div>

      {/* Row 4: MITRE Heatmap */}
      <div style={{ marginBottom: 20 }}>
        <MitreHeatmap />
      </div>
    </div>
  );
}
