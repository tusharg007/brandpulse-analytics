"""Health check endpoint."""
from flask import Blueprint, jsonify
from app.extensions import db, redis_client

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Check database and Redis connectivity."""
    status = {"status": "healthy", "database": "ok", "redis": "ok"}

    # Check PostgreSQL
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception as e:
        status["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
        else:
            status["redis"] = "not configured"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    code = 200 if status["status"] == "healthy" else 503
    return jsonify(status), code
