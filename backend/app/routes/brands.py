"""Brand CRUD endpoints."""
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import Brand, SalesRecord
from sqlalchemy import func

brands_bp = Blueprint('brands', __name__)


# ── Validation schema ──────────────────────────────────────
class BrandSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    category = fields.String(
        required=True,
        validate=validate.OneOf(['fashion', 'lifestyle', 'footwear'])
    )
    launch_date = fields.Date(required=True)
    region = fields.String(required=True, validate=validate.Length(min=1, max=100))


brand_schema = BrandSchema()


@brands_bp.route('/api/brands', methods=['GET'])
def get_brands():
    """List all brands with pagination and total revenue."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Brand.query.order_by(Brand.name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    brands = []
    for brand in pagination.items:
        brand_dict = brand.to_dict()
        total_revenue = (
            db.session.query(func.coalesce(func.sum(SalesRecord.revenue), 0))
            .filter(SalesRecord.brand_id == brand.id)
            .scalar()
        )
        brand_dict['total_revenue'] = round(float(total_revenue), 2)
        brands.append(brand_dict)

    return jsonify({
        'brands': brands,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
    })


@brands_bp.route('/api/brands/<int:brand_id>', methods=['GET'])
def get_brand(brand_id):
    """Get a single brand with total revenue."""
    brand = db.session.get(Brand, brand_id)
    if not brand:
        return jsonify({"error": "Brand not found"}), 404

    brand_dict = brand.to_dict()
    total_revenue = (
        db.session.query(func.coalesce(func.sum(SalesRecord.revenue), 0))
        .filter(SalesRecord.brand_id == brand.id)
        .scalar()
    )
    brand_dict['total_revenue'] = round(float(total_revenue), 2)
    return jsonify(brand_dict)


@brands_bp.route('/api/brands', methods=['POST'])
def create_brand():
    """Create a new brand."""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = brand_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    if Brand.query.filter_by(name=data['name']).first():
        return jsonify({"error": f"Brand '{data['name']}' already exists"}), 409

    brand = Brand(**data)
    db.session.add(brand)
    db.session.commit()
    return jsonify(brand.to_dict()), 201
