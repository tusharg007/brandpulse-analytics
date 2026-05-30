/**
 * KPICard — Key performance indicator card with trend indicator.
 */
import { HiArrowTrendingUp, HiArrowTrendingDown } from 'react-icons/hi2';

export default function KPICard({ label, value, icon: Icon, trend, loading }) {
  if (loading) {
    return (
      <div className="card" style={{ minHeight: 130, padding: 24 }}>
        <div className="skeleton" style={{ width: 80, height: 12, marginBottom: 16 }} />
        <div className="skeleton" style={{ width: 140, height: 28, marginBottom: 12 }} />
        <div className="skeleton" style={{ width: 60, height: 14 }} />
      </div>
    );
  }

  const trendUp = trend && trend > 0;
  const trendColor = trendUp ? 'var(--accent-success)' : 'var(--accent-danger)';

  return (
    <div className="card" style={{ minHeight: 130, padding: 24, position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14 }}>
        {Icon && <Icon size={16} style={{ color: 'var(--accent-primary)' }} />}
        <span className="text-label">{label}</span>
      </div>

      <div className="text-kpi" style={{ marginBottom: 10 }}>{value ?? '—'}</div>

      {trend !== undefined && trend !== null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: trendColor }}>
          {trendUp ? <HiArrowTrendingUp size={14} /> : <HiArrowTrendingDown size={14} />}
          <span>{Math.abs(trend).toFixed(1)}%</span>
          <span style={{ color: 'var(--text-tertiary)', fontSize: 11, marginLeft: 2 }}>vs prior</span>
        </div>
      )}
    </div>
  );
}
