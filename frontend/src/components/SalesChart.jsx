/**
 * SalesChart — Revenue trend area chart with styled tooltip.
 */
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const formatRevenue = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${v}`;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--bg-border)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: 'var(--text-primary)', display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: 'var(--text-secondary)' }}>{p.name}</span>
          <span style={{ fontWeight: 600 }}>{formatRevenue(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

export default function SalesChart({ data, period, onPeriodChange, loading }) {
  if (loading) {
    return (
      <div className="card" style={{ height: '100%' }}>
        <div className="card-header">
          <span className="card-title">Revenue Trend</span>
        </div>
        <div className="skeleton" style={{ width: '100%', height: 280 }} />
      </div>
    );
  }

  return (
    <div className="card" style={{ height: '100%' }}>
      <div className="card-header">
        <span className="card-title">Revenue Trend</span>
        <div style={{ display: 'flex', gap: 2 }}>
          {['monthly', 'weekly'].map((p) => (
            <button
              key={p}
              onClick={() => onPeriodChange?.(p)}
              className="btn"
              style={{
                padding: '4px 10px', fontSize: 11, fontWeight: 500, borderRadius: 100,
                background: period === p ? 'var(--accent-primary)' : 'transparent',
                color: period === p ? '#fff' : 'var(--text-secondary)',
                border: period === p ? 'none' : '1px solid var(--bg-border)',
              }}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.15} />
              <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--bg-border)" strokeDasharray="4 4" vertical={false} />
          <XAxis dataKey="period" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} tickFormatter={formatRevenue} axisLine={false} tickLine={false} width={55} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey="revenue" stroke="var(--chart-1)" strokeWidth={2} fill="url(#areaFill)" dot={false} activeDot={{ r: 4, fill: 'var(--chart-1)' }} name="Revenue" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
