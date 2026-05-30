"""Unit tests for analytics endpoints."""


def test_analytics_summary(client, seed_data):
    """GET /api/analytics/summary returns correct KPI data."""
    resp = client.get('/api/analytics/summary')
    assert resp.status_code == 200
    data = resp.get_json()

    assert 'total_revenue' in data
    assert 'total_units_sold' in data
    assert 'top_brand' in data
    assert 'best_platform' in data

    # Total revenue should be sum of all seeded records
    assert data['total_revenue'] == 370000.0
    assert data['total_units_sold'] == 555


def test_analytics_trends(client, seed_data):
    """GET /api/analytics/trends returns time series data."""
    resp = client.get('/api/analytics/trends')
    assert resp.status_code == 200
    data = resp.get_json()

    assert isinstance(data, list)
    assert len(data) > 0
    assert 'period' in data[0]
    assert 'revenue' in data[0]


def test_analytics_trends_filtered(client, seed_data):
    """GET /api/analytics/trends with brand_id filter."""
    brand = seed_data['brands'][0]
    resp = client.get(f'/api/analytics/trends?brand_id={brand["id"]}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_top_brands(client, seed_data):
    """GET /api/analytics/top-brands returns ranked brands."""
    resp = client.get('/api/analytics/top-brands?limit=3')
    assert resp.status_code == 200
    data = resp.get_json()

    assert isinstance(data, list)
    assert len(data) == 3
    # Should be sorted by revenue descending
    revenues = [b['total_revenue'] for b in data]
    assert revenues == sorted(revenues, reverse=True)


def test_platform_split(client, seed_data):
    """GET /api/analytics/platform-split returns per-platform data."""
    resp = client.get('/api/analytics/platform-split')
    assert resp.status_code == 200
    data = resp.get_json()

    assert isinstance(data, list)
    platforms = {d['platform'] for d in data}
    assert 'Amazon' in platforms


def test_health_check(client):
    """GET /api/health returns status."""
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'healthy'
