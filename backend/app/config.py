"""Application configuration loaded from environment variables."""
import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://brandpulse:brandpulse_secret@localhost:5432/brandpulse_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Pagination defaults
    ITEMS_PER_PAGE = 20

    # Cache TTL in seconds
    CACHE_TTL = 300  # 5 minutes


class TestConfig(Config):
    """Test configuration — in-memory SQLite for speed."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    REDIS_URL = None
