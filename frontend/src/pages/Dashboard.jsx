/**
 * Dashboard — Main analytics page with CSS Grid layout.
 */
import { useState, useCallback } from 'react';
import { HiCurrencyRupee, HiCube, HiShoppingBag, HiExclamationTriangle, HiArrowDownTray } from 'react-icons/hi2';
import useAnalytics from '../hooks/useAnalytics';
import KPICard from '../components/KPICard';
import SalesChart from '../components/SalesChart';
import TopBrandsChart from '../components/TopBrandsChart';
import PlatformPieChart from '../components/PlatformPieChart';
import FilterBar from '../components/FilterBar';
import ETLPanel from '../components/ETLPanel';
import { exportCSV } from '../services/api';

const formatRevenue = (v) => {
  if (!v) return '₹0';
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${(v / 1000).toFixed(1)}K`;
};

export default function Dashboard() {
  const [filters, setFilters] = useState({ brandId: undefined, startDate: undefined, endDate: undefined, period: 'monthly' });
  const { summary, trends, topBrands, platformBreakdown, loading, refetch, setSummary } = useAnalytics(filters);
  const [lastUpdated] = useState(new Date());

  const handleExport = async () => {
    try {
      const res = await exportCSV(filters);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'brandpulse_export.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 className="text-heading" style={{ margin: 0 }}>Brand Analytics</h1>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={handleExport}>
            <HiArrowDownTray size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <KPICard label="Total Revenue" value={formatRevenue(summary?.total_revenue)} icon={HiCurrencyRupee} loading={loading} />
        <KPICard label="Total Units" value={summary?.total_units_sold?.toLocaleString()} icon={HiCube} loading={loading} />
        <KPICard label="Active Brands" value={summary?.active_brands} icon={HiShoppingBag} loading={loading} />
        <KPICard label="Anomalies" value={summary?.anomalies_count} icon={HiExclamationTriangle} loading={loading} />
      </div>

      {/* Main Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: 16, marginBottom: 24 }}>
        <SalesChart
          data={trends}
          period={filters.period}
          onPeriodChange={(p) => setFilters(f => ({ ...f, period: p }))}
          loading={loading}
        />
        <div style={{ display: 'grid', gridTemplateRows: '1fr 1fr', gap: 16 }}>
          <TopBrandsChart data={topBrands} loading={loading} />
          <PlatformPieChart data={platformBreakdown} loading={loading} />
        </div>
      </div>

      {/* Bottom Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <FilterBar filters={filters} onFilterChange={setFilters} />
        <ETLPanel />
      </div>
    </div>
  );
}
