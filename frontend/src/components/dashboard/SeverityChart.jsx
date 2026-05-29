import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
  INFO: '#3b82f6',
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const { name, value } = payload[0];
    return (
      <div style={{
        background: 'white', padding: '10px 14px', borderRadius: 10,
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)', fontSize: '0.82rem',
        border: '1px solid #e8ecf1',
      }}>
        <span style={{ color: SEVERITY_COLORS[name] || '#333', fontWeight: 600 }}>{name}</span>
        <span style={{ color: '#5f6d7e', marginLeft: 8 }}>{value} alerts</span>
      </div>
    );
  }
  return null;
};

export default function SeverityChart({ data = [] }) {
  const chartData = data.map(d => ({ name: d.severity || d.name, value: d.count }));
  const allSeverities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];
  const existing = new Set(chartData.map(d => d.name));
  allSeverities.forEach(s => { if (!existing.has(s)) chartData.push({ name: s, value: 0 }); });
  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="card">
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>Severity Distribution</span>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', background: '#f1f4f9', padding: '3px 10px', borderRadius: 6 }}>{total} total</span>
      </div>
      {total > 0 ? (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={chartData.filter(d => d.value > 0)} cx="50%" cy="50%" innerRadius={65} outerRadius={100} paddingAngle={3} dataKey="value" animationDuration={800} strokeWidth={0}>
              {chartData.filter(d => d.value > 0).map((entry, i) => (
                <Cell key={i} fill={SEVERITY_COLORS[entry.name] || '#94a3b8'} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
          No severity data available
        </div>
      )}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, justifyContent: 'center', marginTop: 8 }}>
        {chartData.map(d => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem' }}>
            <div style={{ width: 10, height: 10, borderRadius: 3, background: SEVERITY_COLORS[d.name] || '#94a3b8' }} />
            <span style={{ color: '#5f6d7e' }}>{d.name}</span>
            <span style={{ fontWeight: 600, color: '#1a1d26' }}>{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
