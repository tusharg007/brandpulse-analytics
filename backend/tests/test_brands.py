"""Unit tests for brand CRUD endpoints."""
import json


def test_get_brands_empty(client):
    """GET /api/brands with no data returns empty list."""
    resp = client.get('/api/brands')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['brands'] == []
    assert data['total'] == 0


def test_create_brand(client):
    """POST /api/brands creates a brand."""
    resp = client.post('/api/brands', json={
        'name': 'NewBrand',
        'category': 'fashion',
        'launch_date': '2024-01-01',
        'region': 'West India',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['name'] == 'NewBrand'
    assert data['category'] == 'fashion'


def test_create_brand_duplicate(client):
    """POST /api/brands with duplicate name returns 409."""
    payload = {
        'name': 'DupeBrand',
        'category': 'footwear',
        'launch_date': '2024-06-01',
        'region': 'Pan India',
    }
    client.post('/api/brands', json=payload)
    resp = client.post('/api/brands', json=payload)
    assert resp.status_code == 409


def test_create_brand_validation(client):
    """POST /api/brands with invalid data returns 400."""
    resp = client.post('/api/brands', json={
        'name': '',
        'category': 'invalid_category',
    })
    assert resp.status_code == 400


def test_get_brands_with_data(client, seed_data):
    """GET /api/brands returns seeded brands with total revenue."""
    resp = client.get('/api/brands')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total'] == 3
    # Each brand should have total_revenue field
    for brand in data['brands']:
        assert 'total_revenue' in brand


def test_get_brand_detail(client, seed_data):
    """GET /api/brands/<id> returns single brand."""
    brands = seed_data['brands']
    resp = client.get(f'/api/brands/{brands[0]["id"]}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['name'] == 'TestBrand A'
    assert data['total_revenue'] > 0


def test_get_brand_not_found(client):
    """GET /api/brands/<id> with invalid id returns 404."""
    resp = client.get('/api/brands/99999')
    assert resp.status_code == 404


def test_get_brands_pagination(client, seed_data):
    """GET /api/brands with pagination params."""
    resp = client.get('/api/brands?page=1&per_page=2')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['brands']) == 2
    assert data['pages'] == 2
