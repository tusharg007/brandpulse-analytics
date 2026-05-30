"""BrandPulse -- Flask application factory."""
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.extensions import db, init_redis, socketio, celery


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # -- Extensions --
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Initialize Redis (skip in test mode)
    if not app.config.get('TESTING'):
        init_redis(app)

    # Initialize SocketIO (skip in test mode)
    if not app.config.get('TESTING'):
        redis_url = app.config.get('REDIS_URL')
        # Use eventlet if available, otherwise fall back to threading
        try:
            import eventlet  # noqa: F401
            async_mode = 'eventlet'
        except ImportError:
            async_mode = 'threading'

        socketio.init_app(
            app,
            message_queue=redis_url if redis_url else None,
            cors_allowed_origins="*",
            async_mode=async_mode,
        )
    else:
        socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    # Configure Celery
    redis_url = app.config.get('REDIS_URL') or 'redis://localhost:6379/0'
    celery.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
    )

    class ContextTask(celery.Task):
        """Ensure Celery tasks run within Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # -- Register blueprints --
    from app.routes.brands import brands_bp
    from app.routes.sales import sales_bp
    from app.routes.analytics import analytics_bp
    from app.routes.etl import etl_bp
    from app.routes.health import health_bp
    from app.routes.chat import chat_bp

    app.register_blueprint(brands_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(etl_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)

    # Import socket handlers
    from app import sockets  # noqa: F401

    # -- Error handlers --
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": str(error), "status": 400}), 400

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error", "status": 500}), 500

    return app
