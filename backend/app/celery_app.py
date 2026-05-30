"""Celery app entry point for the worker process."""
from app import create_app
from app.extensions import celery

app = create_app()
app.app_context().push()
