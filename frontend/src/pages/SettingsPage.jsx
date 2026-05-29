import { motion } from 'framer-motion';
import { Settings, Database, Cpu, Globe } from 'lucide-react';
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {});
  }, []);

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>
          <Settings size={24} style={{ verticalAlign: 'middle', marginRight: 10 }} />
          Settings
        </h1>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <Database size={18} color="var(--accent-blue)" />
            <span style={{ fontWeight: 600 }}>Elasticsearch</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <p>Status: <strong style={{ color: health?.elasticsearch?.status === 'green' ? 'var(--severity-low)' : 'var(--severity-medium)' }}>
              {health?.elasticsearch?.status || 'checking...'}
            </strong></p>
            <p style={{ marginTop: 8 }}>Cluster: {health?.elasticsearch?.cluster || '—'}</p>
            <p style={{ marginTop: 4 }}>Nodes: {health?.elasticsearch?.nodes || '—'}</p>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <Cpu size={18} color="var(--accent-purple)" />
            <span style={{ fontWeight: 600 }}>AI Engine</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <p>Framework: <strong>LangGraph</strong></p>
            <p style={{ marginTop: 4 }}>LLM: <strong>Groq API</strong></p>
            <p style={{ marginTop: 4 }}>Model: <strong>llama-3.3-70b-versatile</strong></p>
            <p style={{ marginTop: 4 }}>Agents: Supervisor → Triage → Correlator → Explainer</p>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <Globe size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 600 }}>Platform Info</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <p>Version: <strong>1.0.0</strong></p>
            <p style={{ marginTop: 4 }}>Backend: <strong>FastAPI + Python</strong></p>
            <p style={{ marginTop: 4 }}>Frontend: <strong>React + Tailwind CSS</strong></p>
            <p style={{ marginTop: 4 }}>Real-time: <strong>WebSocket</strong></p>
          </div>
        </div>
      </div>
    </div>
  );
}
