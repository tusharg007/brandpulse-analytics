"""Aggregated analytics endpoints with Redis caching."""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, case, extract
from app.extensions import db
from app.models import SalesRecord, Brand
from app.services.cache_service import get_cached, set_cached

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/analytics/summary', methods=['GET'])
def get_summary():
    """KPI summary — total revenue, units, top brand, best platform. Cached 5 min."""
    cache_key = 'analytics:summary'
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached)

    summary = _get_summary_data()
    set_cached(cache_key, summary, ttl=300)
    return jsonify(summary)


def _get_summary_data():
    """Compute KPI summary dict. Shared by route and Celery kpi_update task."""
    total_revenue = db.session.query(
        func.coalesce(func.sum(SalesRecord.revenue), 0)
    ).scalar()

    total_units = db.session.query(
        func.coalesce(func.sum(SalesRecord.units_sold), 0)
    ).scalar()

    # Top brand by revenue
    top_brand = (
        db.session.query(Brand.name, func.sum(SalesRecord.revenue).label('rev'))
        .join(SalesRecord)
        .group_by(Brand.name)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .first()
    )

    # Best platform by revenue
    best_platform = (
        db.session.query(
            SalesRecord.platform,
            func.sum(SalesRecord.revenue).label('rev')
        )
        .group_by(SalesRecord.platform)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .first()
    )

    active_brands = db.session.query(func.count(func.distinct(SalesRecord.brand_id))).scalar()
    anomalies_count = SalesRecord.query.filter_by(is_anomalous=True).count()

    return {
        'total_revenue': round(float(total_revenue), 2),
        'total_units_sold': int(total_units),
        'top_brand': top_brand[0] if top_brand else None,
        'top_brand_revenue': round(float(top_brand[1]), 2) if top_brand else 0,
        'best_platform': best_platform[0] if best_platform else None,
        'best_platform_revenue': round(float(best_platform[1]), 2) if best_platform else 0,
        'active_brands': int(active_brands),
        'anomalies_count': int(anomalies_count),
    }


@analytics_bp.route('/api/analytics/trends', methods=['GET'])
def get_trends():
    """Revenue trends over time grouped by month or week."""
    brand_id = request.args.get('brand_id', type=int)
    period = request.args.get('period', 'monthly')

    # Build cache key
    cache_key = f'analytics:trends:{brand_id}:{period}'
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached)

    # Group by year-month for portability (works with both PG and SQLite)
    query = db.session.query(
        extract('year', SalesRecord.date).label('year'),
        extract('month', SalesRecord.date).label('month'),
        func.sum(SalesRecord.revenue).label('revenue'),
        func.sum(SalesRecord.units_sold).label('units_sold'),
    )

    if brand_id:
        query = query.filter(SalesRecord.brand_id == brand_id)

    results = (
        query.group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )

    trends = []
    for row in results:
        trends.append({
            'period': f"{int(row.year)}-{int(row.month):02d}",
            'revenue': round(float(row.revenue), 2),
            'units_sold': int(row.units_sold),
        })

    set_cached(cache_key, trends, ttl=300)
    return jsonify(trends)


@analytics_bp.route('/api/analytics/top-brands', methods=['GET'])
def get_top_brands():
    """Top N brands ranked by revenue."""
    limit = request.args.get('limit', 5, type=int)

    cache_key = f'analytics:top_brands:{limit}'
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached)

    results = (
        db.session.query(
            Brand.id,
            Brand.name,
            Brand.category,
            func.sum(SalesRecord.revenue).label('total_revenue'),
            func.sum(SalesRecord.units_sold).label('total_units'),
        )
        .join(SalesRecord)
        .group_by(Brand.id, Brand.name, Brand.category)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .limit(limit)
        .all()
    )

    top_brands = []
    for row in results:
        top_brands.append({
            'id': row.id,
            'name': row.name,
            'category': row.category,
            'total_revenue': round(float(row.total_revenue), 2),
            'total_units': int(row.total_units),
        })

    set_cached(cache_key, top_brands, ttl=300)
    return jsonify(top_brands)


@analytics_bp.route('/api/analytics/platform-split', methods=['GET'])
def get_platform_split():
    """Revenue breakdown by platform for the pie chart."""
    cache_key = 'analytics:platform_split'
    cached = get_cached(cache_key)
    if cached:
        return jsonify(cached)

    results = (
        db.session.query(
            SalesRecord.platform,
            func.sum(SalesRecord.revenue).label('revenue'),
            func.sum(SalesRecord.units_sold).label('units'),
        )
        .group_by(SalesRecord.platform)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .all()
    )

    split = []
    for row in results:
        split.append({
            'platform': row.platform,
            'revenue': round(float(row.revenue), 2),
            'units': int(row.units),
        })

    set_cached(cache_key, split, ttl=300)
    return jsonify(split)
