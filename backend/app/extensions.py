"""Shared extensions — imported by app factory and across modules."""
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from celery import Celery
import redis as redis_lib

db = SQLAlchemy()
socketio = SocketIO()
celery = Celery()

# Global Redis client — initialized in init_redis()
redis_client = None


def init_redis(app):
    """Initialize Redis client from app config."""
    global redis_client
    redis_url = app.config.get('REDIS_URL')
    if redis_url:
        try:
            redis_client = redis_lib.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            app.logger.info("Redis connected successfully")
        except Exception as e:
            app.logger.warning(f"Redis unavailable: {e} -- caching disabled.")
            redis_client = None
    else:
        app.logger.info("Redis URL not configured -- caching disabled.")
