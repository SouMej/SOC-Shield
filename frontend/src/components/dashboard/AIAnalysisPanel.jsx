import { motion } from 'framer-motion';
import { Cpu, ChevronDown, ChevronUp, Zap } from 'lucide-react';
import { useState } from 'react';

function ScoreGauge({ score }) {
  const color = score >= 80 ? '#ef4444' : score >= 60 ? '#f97316' : score >= 40 ? '#eab308' : '#22c55e';
  const pct = Math.min(score, 100);
  return (
    <div style={{ position: 'relative', width: 48, height: 48 }}>
      <svg width="48" height="48" viewBox="0 0 48 48">
        <circle cx="24" cy="24" r="20" fill="none" stroke="#f1f4f9" strokeWidth="4" />
        <circle cx="24" cy="24" r="20" fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={`${pct * 1.26} 126`} strokeLinecap="round" transform="rotate(-90 24 24)"
          style={{ transition: 'stroke-dasharray 0.6s ease' }} />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.72rem', fontWeight: 700, color,
      }}>{score}</div>
    </div>
  );
}

export default function AIAnalysisPanel({ analyses = [] }) {
  const [expandedId, setExpandedId] = useState(null);

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <Cpu size={18} color="#8b5cf6" />
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>AI Threat Analysis</span>
        <span style={{
          marginLeft: 'auto', fontSize: '0.68rem', padding: '3px 10px',
          background: '#f3f0ff', color: '#7c3aed', borderRadius: 8, fontWeight: 600,
        }}>LangGraph + Groq</span>
      </div>
      <div style={{ maxHeight: 500, overflowY: 'auto' }}>
        {analyses.slice(0, 10).map((a, i) => {
          const isExpanded = expandedId === (a.analysis_id || i);
          return (
            <motion.div key={a.analysis_id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              transition={{ delay: i * 0.05 }}
              style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer' }}
              onClick={() => setExpandedId(isExpanded ? null : (a.analysis_id || i))}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <ScoreGauge score={a.threat_score || 0} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span className={`badge badge-${(a.severity || 'info').toLowerCase()}`}>{a.severity}</span>
                    <span style={{ fontSize: '0.84rem', fontWeight: 500, color: '#1a1d26' }}>
                      {a.title || a.attack_type || 'Analysis'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.76rem', color: '#5f6d7e', lineHeight: 1.4 }}>
                    {(a.explanation || '').slice(0, 100)}{(a.explanation || '').length > 100 ? '...' : ''}
                  </div>
                </div>
                {isExpanded ? <ChevronUp size={16} color="#94a3b8" /> : <ChevronDown size={16} color="#94a3b8" />}
              </div>
              {isExpanded && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                  style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '0.82rem', color: '#5f6d7e', marginBottom: 12, lineHeight: 1.5 }}>{a.explanation}</div>
                  {a.mitre_techniques?.length > 0 && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>MITRE ATT&CK</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {(a.mitre_techniques || []).map((t, j) => (
                          <span key={j} style={{ padding: '3px 9px', borderRadius: 6, fontSize: '0.72rem', background: '#eff6ff', color: '#3b82f6', fontFamily: 'monospace', fontWeight: 500 }}>
                            {typeof t === 'string' ? t : t.id}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {a.recommended_actions?.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Actions</div>
                      {a.recommended_actions.map((action, j) => (
                        <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#5f6d7e', marginBottom: 4 }}>
                          <Zap size={12} color="#f97316" /> {action}
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          );
        })}
        {analyses.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
            <Cpu size={32} style={{ marginBottom: 12, opacity: 0.3 }} />
            <div>AI engine analyzing events...</div>
          </div>
        )}
      </div>
    </div>
  );
}
