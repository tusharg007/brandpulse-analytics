"""Shared test fixtures — using in-memory SQLite for speed."""
import pytest
from datetime import date, datetime
from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import Brand, SalesRecord, ETLLog


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Database session for direct model access."""
    with app.app_context():
        yield _db


@pytest.fixture
def seed_data(app, db):
    """Seed the test database with sample brands and sales records."""
    with app.app_context():
        brands = [
            Brand(name='TestBrand A', category='fashion', launch_date=date(2022, 1, 1), region='North India'),
            Brand(name='TestBrand B', category='footwear', launch_date=date(2021, 6, 15), region='South India'),
            Brand(name='TestBrand C', category='lifestyle', launch_date=date(2023, 3, 10), region='Pan India'),
        ]
        for b in brands:
            db.session.add(b)
        db.session.flush()

        sales = [
            SalesRecord(brand_id=brands[0].id, date=date(2024, 1, 15), revenue=50000, units_sold=100,
                        platform='Amazon', return_rate=0.05, revenue_per_unit=500, is_anomalous=False),
            SalesRecord(brand_id=brands[0].id, date=date(2024, 2, 15), revenue=75000, units_sold=150,
                        platform='Flipkart', return_rate=0.35, revenue_per_unit=500, is_anomalous=True),
            SalesRecord(brand_id=brands[1].id, date=date(2024, 1, 20), revenue=120000, units_sold=60,
                        platform='Direct', return_rate=0.10, revenue_per_unit=2000, is_anomalous=False),
            SalesRecord(brand_id=brands[1].id, date=date(2024, 3, 10), revenue=95000, units_sold=45,
                        platform='Amazon', return_rate=0.08, revenue_per_unit=2111.11, is_anomalous=False),
            SalesRecord(brand_id=brands[2].id, date=date(2024, 2, 1), revenue=30000, units_sold=200,
                        platform='Flipkart', return_rate=0.15, revenue_per_unit=150, is_anomalous=False),
        ]
        for s in sales:
            db.session.add(s)
        db.session.commit()

        # Return plain dicts to avoid DetachedInstanceError
        brand_dicts = [{'id': b.id, 'name': b.name, 'category': b.category} for b in brands]
        return {'brands': brand_dicts, 'sales': len(sales)}
