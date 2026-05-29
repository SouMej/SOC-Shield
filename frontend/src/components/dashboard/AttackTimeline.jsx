import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'white', padding: '10px 14px', borderRadius: 10,
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)', fontSize: '0.82rem',
        border: '1px solid #e8ecf1',
      }}>
        <div style={{ color: '#94a3b8', marginBottom: 4, fontSize: '0.75rem' }}>{label}</div>
        {payload.map((p, i) => (
          <div key={i} style={{ color: p.color, fontWeight: 500 }}>{p.name}: {p.value}</div>
        ))}
      </div>
    );
  }
  return null;
};

export default function AttackTimeline({ data = [] }) {
  const chartData = data.map(d => ({
    time: new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    total: d.total || d.count || 0,
    critical: d.severities?.CRITICAL || 0,
    high: d.severities?.HIGH || 0,
  }));

  return (
    <div className="card">
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1a1d26' }}>Attack Timeline</span>
        <span style={{ fontSize: '0.72rem', color: '#94a3b8', background: '#f1f4f9', padding: '3px 10px', borderRadius: 6 }}>Last 24h</span>
      </div>
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="gradBlue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradPurple" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f2f5" />
            <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="total" stroke="#3b82f6" fill="url(#gradBlue)" strokeWidth={2.5} name="Total" dot={false} />
            <Area type="monotone" dataKey="critical" stroke="#8b5cf6" fill="url(#gradPurple)" strokeWidth={2} name="Critical" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
          Collecting timeline data...
        </div>
      )}
    </div>
  );
}
