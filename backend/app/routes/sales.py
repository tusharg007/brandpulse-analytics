"""Sales data endpoints + CSV export."""
import csv
import io
from flask import Blueprint, request, jsonify, Response
from app.extensions import db
from app.models import SalesRecord, Brand

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/api/sales', methods=['GET'])
def get_sales():
    """Filtered, paginated sales records."""
    query = SalesRecord.query

    # ── Filters ─────────────────────────────────────────
    brand_id = request.args.get('brand_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    if brand_id:
        query = query.filter(SalesRecord.brand_id == brand_id)
    if start_date:
        query = query.filter(SalesRecord.date >= start_date)
    if end_date:
        query = query.filter(SalesRecord.date <= end_date)
    if platform:
        query = query.filter(SalesRecord.platform == platform)

    pagination = query.order_by(SalesRecord.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'sales': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@sales_bp.route('/api/analytics/export', methods=['GET'])
def export_csv():
    """Stream filtered sales data as a CSV download."""
    query = SalesRecord.query.join(Brand)

    brand_id = request.args.get('brand_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform')

    if brand_id:
        query = query.filter(SalesRecord.brand_id == brand_id)
    if start_date:
        query = query.filter(SalesRecord.date >= start_date)
    if end_date:
        query = query.filter(SalesRecord.date <= end_date)
    if platform:
        query = query.filter(SalesRecord.platform == platform)

    records = query.order_by(SalesRecord.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Brand', 'Date', 'Revenue', 'Units Sold',
        'Platform', 'Return Rate', 'Revenue/Unit', 'Anomalous'
    ])

    for r in records:
        writer.writerow([
            r.id, r.brand.name, r.date, r.revenue, r.units_sold,
            r.platform, r.return_rate, r.revenue_per_unit, r.is_anomalous
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=brandpulse_sales_export.csv'}
    )
