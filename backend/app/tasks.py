"""Celery tasks for async ETL processing and BrandBot AI replies."""
import os
import time
from datetime import datetime

from app.extensions import celery, db, socketio
from app.models import ETLLog, SalesRecord, Brand, ChatRoom, ChatMessage
from app.services.cache_service import invalidate_cache


@celery.task(bind=True)
def run_etl_task(self):
    """Async ETL pipeline execution via Celery. Wraps existing etl_service logic."""
    from app.services.etl_service import run_etl_pipeline

    log_entry = ETLLog(run_timestamp=datetime.utcnow(), status='running')
    db.session.add(log_entry)
    db.session.commit()

    try:
        start = time.time()

        socketio.emit('etl_started', {
            'task_id': self.request.id,
            'timestamp': datetime.utcnow().isoformat(),
        }, namespace='/', to='etl_updates')

        # Reuse existing ETL pipeline
        result = run_etl_pipeline()

        duration = time.time() - start

        # Count anomalies from recent ingestion
        anomaly_count = SalesRecord.query.filter_by(is_anomalous=True).count()

        # Update log entry
        log_entry.records_processed = result.get('records_processed', 0)
        log_entry.status = 'success'
        log_entry.anomalies_detected = anomaly_count
        log_entry.duration_seconds = round(duration, 2)
        db.session.commit()

        # Broadcast anomaly alerts to brand rooms
        anomaly_records = (
            SalesRecord.query
            .filter_by(is_anomalous=True)
            .order_by(SalesRecord.ingestion_timestamp.desc())
            .limit(5)
            .all()
        )

        for record in anomaly_records:
            brand = db.session.get(Brand, record.brand_id)
            if not brand:
                continue
            room = ChatRoom.query.filter_by(brand_id=brand.id).first()
            if room:
                msg_text = (
                    f"Anomaly detected for {brand.name}: "
                    f"return_rate={record.return_rate:.0%} on "
                    f"{record.date} via {record.platform}"
                )
                alert_msg = ChatMessage(
                    room_id=room.id,
                    sender_name='BrandBot',
                    sender_type='bot',
                    content=msg_text,
                    message_type='anomaly_alert',
                    timestamp=datetime.utcnow(),
                )
                db.session.add(alert_msg)
                db.session.commit()

                socketio.emit('anomaly_alert', alert_msg.to_dict(),
                              namespace='/', to='alerts')

        invalidate_cache('analytics:*')

        # Broadcast ETL completion
        socketio.emit('etl_complete', {
            'records_processed': result.get('records_processed', 0),
            'anomalies': anomaly_count,
            'duration': round(duration, 2),
            'status': 'success',
        }, namespace='/', to='etl_updates')

        # Broadcast KPI update to dashboard
        from app.routes.analytics import _get_summary_data
        try:
            summary = _get_summary_data()
            socketio.emit('kpi_update', summary, namespace='/', to='dashboard')
        except Exception:
            pass

        return {
            'records_processed': result.get('records_processed', 0),
            'anomalies': anomaly_count,
            'duration': round(duration, 2),
        }

    except Exception as e:
        log_entry.status = 'failed'
        log_entry.error_message = str(e)
        log_entry.duration_seconds = time.time() - start
        db.session.commit()

        socketio.emit('etl_complete', {
            'status': 'failed',
            'error': str(e),
        }, namespace='/', to='etl_updates')

        raise


@celery.task
def bot_reply(room_id, trigger_message):
    """Generate an AI reply using Anthropic Claude and broadcast via WebSocket."""
    try:
        import anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY', '')

        if not api_key:
            reply_text = ("BrandBot is not configured. Set ANTHROPIC_API_KEY "
                          "environment variable to enable AI responses.")
        else:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=200,
                system=(
                    "You are BrandBot, an AI analyst assistant for BrandPulse -- India's "
                    "largest D2C fashion & lifestyle brand portfolio. You help brand "
                    "managers understand sales anomalies, revenue trends, and "
                    "performance insights. Be concise, data-focused, and "
                    "actionable. Maximum 2-3 sentences."
                ),
                messages=[{"role": "user", "content": trigger_message}],
            )
            reply_text = response.content[0].text

        msg = ChatMessage(
            room_id=room_id,
            sender_name='BrandBot',
            sender_type='bot',
            content=reply_text,
            message_type='text',
            timestamp=datetime.utcnow(),
        )
        db.session.add(msg)
        db.session.commit()

        socketio.emit('new_message', msg.to_dict(),
                      namespace='/', to=f"room_{room_id}")

    except Exception as e:
        error_msg = ChatMessage(
            room_id=room_id,
            sender_name='BrandBot',
            sender_type='bot',
            content=f"Sorry, I encountered an error: {str(e)[:100]}",
            message_type='text',
            timestamp=datetime.utcnow(),
        )
        db.session.add(error_msg)
        db.session.commit()
        socketio.emit('new_message', error_msg.to_dict(),
                      namespace='/', to=f"room_{room_id}")
