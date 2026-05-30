/**
 * useAnalytics — fetches all analytics data with filter support.
 */
import { useState, useEffect, useCallback } from 'react';
import { getAnalyticsSummary, getTrends, getTopBrands, getPlatformSplit } from '../services/api';

export default function useAnalytics(filters = {}) {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [topBrands, setTopBrands] = useState([]);
  const [platformBreakdown, setPlatformBreakdown] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, trendRes, topRes, platRes] = await Promise.all([
        getAnalyticsSummary(),
        getTrends(filters.brandId, filters.period || 'monthly'),
        getTopBrands(5),
        getPlatformSplit(),
      ]);
      setSummary(sumRes.data);
      setTrends(trendRes.data);
      setTopBrands(topRes.data);
      setPlatformBreakdown(platRes.data);
    } catch (err) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [filters.brandId, filters.period]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  return { summary, trends, topBrands, platformBreakdown, loading, error, refetch: fetchAll, setSummary };
}
