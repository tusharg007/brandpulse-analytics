/**
 * FilterBar — Inline horizontal filter strip.
 */
import { useState, useEffect } from 'react';
import { getBrands } from '../services/api';

export default function FilterBar({ filters, onFilterChange }) {
  const [brands, setBrands] = useState([]);

  useEffect(() => {
    getBrands(1, 100).then(r => setBrands(r.data.brands || [])).catch(() => {});
  }, []);

  const activeCount = [filters.brandId, filters.startDate, filters.endDate].filter(Boolean).length;

  const update = (key, val) => onFilterChange?.({ ...filters, [key]: val || undefined });

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--bg-border)',
      borderRadius: 8, padding: '10px 16px',
      display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
    }}>
      {/* Brand dropdown */}
      <select
        className="select-input"
        value={filters.brandId || ''}
        onChange={(e) => update('brandId', e.target.value)}
        style={{ minWidth: 130 }}
      >
        <option value="">All Brands</option>
        {brands.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
      </select>

      {/* Date from */}
      <input
        type="date"
        className="input"
        value={filters.startDate || ''}
        onChange={(e) => update('startDate', e.target.value)}
        style={{ width: 140 }}
      />

      {/* Date to */}
      <input
        type="date"
        className="input"
        value={filters.endDate || ''}
        onChange={(e) => update('endDate', e.target.value)}
        style={{ width: 140 }}
      />

      {/* Active count badge */}
      {activeCount > 0 && (
        <span className="pill pill-indigo">{activeCount} filter{activeCount > 1 ? 's' : ''} active</span>
      )}

      {/* Clear */}
      {activeCount > 0 && (
        <button
          className="btn btn-ghost"
          style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => onFilterChange?.({ brandId: undefined, startDate: undefined, endDate: undefined, period: filters.period })}
        >
          Clear
        </button>
      )}
    </div>
  );
}
