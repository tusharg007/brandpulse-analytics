export default function BrandCard({ brand, onClick }) {
  const categoryColors = {
    fashion:   'from-indigo-500/20 to-purple-500/20 border-indigo-500/30',
    footwear:  'from-amber-500/20 to-orange-500/20 border-amber-500/30',
    lifestyle: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30',
  };

  const categoryEmoji = {
    fashion: '👗',
    footwear: '👟',
    lifestyle: '🏠',
  };

  const colors = categoryColors[brand.category] || categoryColors.fashion;

  return (
    <div
      onClick={() => onClick?.(brand)}
      className={`glass-card cursor-pointer bg-gradient-to-br ${colors} animate-slide-up`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-white">{brand.name}</h3>
          <p className="text-sm text-slate-400">{brand.region}</p>
        </div>
        <span className="text-2xl">{categoryEmoji[brand.category] || '📊'}</span>
      </div>

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/10">
        <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-white/10 text-slate-300 capitalize">
          {brand.category}
        </span>
        <p className="text-sm font-semibold text-brand-300">
          ₹{Number(brand.total_revenue || 0).toLocaleString('en-IN')}
        </p>
      </div>
    </div>
  );
}
