/**
 * PlatformPieChart — Donut chart with center total and custom legend.
 */
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['var(--chart-1)', 'var(--chart-3)', 'var(--chart-2)', 'var(--chart-4)', 'var(--chart-5)'];

const formatRevenue = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${(v / 1000).toFixed(0)}K`;
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--bg-border)',
      borderRadius: 8, padding: '8px 12px', fontSize: 12,
    }}>
      <span style={{ fontWeight: 600 }}>{payload[0].name}</span>
      <span style={{ marginLeft: 8, color: 'var(--text-secondary)' }}>{formatRevenue(payload[0].value)}</span>
    </div>
  );
};

export default function PlatformPieChart({ data, loading }) {
  const total = (data || []).reduce((s, d) => s + d.revenue, 0);

  if (loading) {
    return (
      <div className="card" style={{ height: '100%' }}>
        <div className="card-header"><span className="card-title">Platform Split</span></div>
        <div className="skeleton" style={{ width: 160, height: 160, borderRadius: '50%', margin: '16px auto' }} />
      </div>
    );
  }

  return (
    <div className="card" style={{ height: '100%' }}>
      <div className="card-header"><span className="card-title">Platform Split</span></div>
      <div style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie data={data} dataKey="revenue" nameKey="platform" cx="50%" cy="50%" innerRadius="55%" outerRadius="80%" strokeWidth={0}>
              {(data || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {/* Center label */}
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none',
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 2 }}>Total</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{formatRevenue(total)}</div>
        </div>
      </div>

      {/* Custom legend row */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 8 }}>
        {(data || []).map((d, i) => {
          const pct = total > 0 ? ((d.revenue / total) * 100).toFixed(0) : 0;
          return (
            <div key={d.platform} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS[i % COLORS.length] }} />
              <span style={{ color: 'var(--text-secondary)' }}>{d.platform}</span>
              <span style={{ color: 'var(--text-tertiary)' }}>{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
