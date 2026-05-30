/**
 * TopBrandsChart — Horizontal bar chart of top brands by revenue.
 */
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';

const COLORS = ['var(--chart-1)', 'var(--chart-5)', 'var(--chart-2)', 'var(--chart-4)', 'var(--chart-3)'];

const formatRevenue = (v) => {
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${(v / 1000).toFixed(0)}K`;
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: 'var(--bg-elevated)', border: '1px solid var(--bg-border)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{d.name}</div>
      <div style={{ color: 'var(--text-secondary)' }}>Revenue: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{formatRevenue(d.total_revenue)}</span></div>
    </div>
  );
};

export default function TopBrandsChart({ data, loading }) {
  if (loading) {
    return (
      <div className="card" style={{ height: '100%' }}>
        <div className="card-header">
          <span className="card-title">Top Brands</span>
        </div>
        <div className="skeleton" style={{ width: '100%', height: 200 }} />
      </div>
    );
  }

  return (
    <div className="card" style={{ height: '100%' }}>
      <div className="card-header">
        <div>
          <span className="card-title">Top Brands</span>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 8 }}>by Revenue</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 50, left: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="name" width={85} tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={false} />
          <Bar dataKey="total_revenue" radius={[0, 4, 4, 0]} barSize={18}>
            {(data || []).map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
            <LabelList dataKey="total_revenue" position="right" formatter={formatRevenue} style={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
