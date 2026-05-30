/**
 * Brands — Brand card grid with revenue and chat room links.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getBrands, getBrand } from '../services/api';
import { HiChatBubbleLeftRight } from 'react-icons/hi2';

const CATEGORY_COLORS = {
  fashion:   'var(--chart-1)',
  footwear:  'var(--chart-3)',
  lifestyle: 'var(--chart-2)',
};

const formatRevenue = (v) => {
  if (!v) return '₹0';
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  return `₹${v.toLocaleString()}`;
};

export default function Brands() {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getBrands(1, 50)
      .then(r => setBrands(r.data.brands || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleBrandClick = async (brand) => {
    if (selectedBrand?.id === brand.id) {
      setSelectedBrand(null);
      return;
    }
    try {
      const res = await getBrand(brand.id);
      setSelectedBrand(res.data);
    } catch {
      setSelectedBrand({ ...brand });
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <h1 className="text-heading" style={{ marginBottom: 8 }}>Brands</h1>
        <p style={{ color: 'var(--text-tertiary)', marginBottom: 24 }}>Explore your D2C brand portfolio</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card"><div className="skeleton" style={{ height: 100 }} /></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <h1 className="text-heading" style={{ marginBottom: 8 }}>Brands</h1>
      <p style={{ color: 'var(--text-tertiary)', marginBottom: 24 }}>Explore your D2C brand portfolio</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {brands.map(brand => {
          const accent = CATEGORY_COLORS[brand.category] || 'var(--chart-1)';
          const isSelected = selectedBrand?.id === brand.id;
          return (
            <div
              key={brand.id}
              className="card"
              onClick={() => handleBrandClick(brand)}
              style={{
                cursor: 'pointer',
                borderLeft: `3px solid ${accent}`,
                background: isSelected ? 'var(--bg-elevated)' : 'var(--bg-surface)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 2 }}>{brand.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{brand.region}</div>
                </div>
                <span className="pill pill-indigo" style={{ fontSize: 11 }}>{brand.category}</span>
              </div>

              {isSelected && selectedBrand?.total_revenue !== undefined && (
                <div style={{ marginTop: 8, paddingTop: 12, borderTop: '1px solid var(--bg-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div className="text-label" style={{ marginBottom: 4 }}>Total Revenue</div>
                      <div style={{ fontSize: 20, fontWeight: 700 }}>{formatRevenue(selectedBrand.total_revenue)}</div>
                    </div>
                    <button
                      className="btn btn-ghost"
                      onClick={(e) => { e.stopPropagation(); navigate('/chat'); }}
                      style={{ fontSize: 12, padding: '6px 10px' }}
                    >
                      <HiChatBubbleLeftRight size={14} /> Open Chat
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
