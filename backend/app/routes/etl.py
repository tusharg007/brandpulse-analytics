"""ETL pipeline trigger and log endpoints."""
from flask import Blueprint, jsonify
from app.models import ETLLog
from app.extensions import db

etl_bp = Blueprint('etl', __name__)


@etl_bp.route('/api/etl/trigger', methods=['POST'])
def trigger_etl():
    """Trigger ETL pipeline asynchronously via Celery."""
    try:
        from app.tasks import run_etl_task
        task = run_etl_task.delay()
        return jsonify({
            "task_id": task.id,
            "status": "queued",
            "message": "ETL pipeline queued for execution",
        }), 202
    except Exception:
        # Fallback to sync execution if Celery is unavailable
        from app.services.etl_service import run_etl_pipeline
        try:
            result = run_etl_pipeline()
            return jsonify({
                "message": "ETL pipeline completed (sync fallback)",
                "records_processed": result['records_processed'],
                "status": result['status'],
            }), 200
        except Exception as e:
            return jsonify({"message": "ETL pipeline failed", "error": str(e)}), 500


@etl_bp.route('/api/etl/status/<task_id>', methods=['GET'])
def etl_status(task_id):
    """Check status of an async ETL task."""
    from app.extensions import celery
    result = celery.AsyncResult(task_id)
    return jsonify({
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.ready() else None,
    })


@etl_bp.route('/api/etl/logs', methods=['GET'])
def get_etl_logs():
    """Return the most recent ETL run logs."""
    logs = (
        ETLLog.query
        .order_by(ETLLog.run_timestamp.desc())
        .limit(10)
        .all()
    )
    return jsonify([log.to_dict() for log in logs])
