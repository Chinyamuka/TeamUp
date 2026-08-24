"""
TeamUp Configuration Settings

Based on SRS Requirements:
- Section 2.4: Operating Environment (PostgreSQL 15, Redis 7, RabbitMQ 3.x)
- Section 2.5: Design Constraints (Stateless servers)
- Section 7.3: JWT Authentication (Token expiration)
- Section 9: Security (bcrypt cost, secrets)
- FR-7.1: Rate Limiting
- NFR-14: Database migrations with Alembic

This configuration follows the Twelve-Factor App methodology (SRS Section 1.4):
- Config is stored in environment variables
- Different environments use different configs
- No hard-coded secrets in the codebase
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
# This is why we ignore .env in .gitignore!
load_dotenv()


class Config:
    """
    Base configuration class.
    All environment-specific configs inherit from this.
    
    Why a class?
    - Clean organization of settings
    - Easy to override for different environments
    - Can add computed properties
    """
    
    # ============================================================
    # FLASK CORE SETTINGS (SRS Section 2.4)
    # ============================================================
    # SECRET_KEY: Used for session encryption and CSRF protection
    # MUST be changed in production! (Section 9 - Secrets management)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # DEBUG: Enables detailed error pages and auto-reload
    # NEVER enable in production! (Security risk)
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # ENV: Current environment (development, production, testing)
    ENV = os.getenv('FLASK_ENV', 'development')
    
    # ============================================================
    # PRIMARY DATABASE - PostgreSQL (SRS Section 2.4, 6.2)
    # ============================================================
    # PostgreSQL 15 is the primary database (SRS Section 2.4)
    # Format: postgresql://user:password@host:port/database
    # For local development with Docker:
    # DATABASE_URL=postgresql://teamup:teamup_password@localhost:5432/teamup_db
    
    # All environments use PostgreSQL (no SQLite)
    # This ensures migrations work the same everywhere
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://teamup:teamup_password@localhost:5432/teamup_db'  # Default for Docker
    )
    
    # Track modifications: Disabled for performance
    # This reduces memory usage
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Pool settings for production (SRS Section 5.5)
    # Connection pooling improves performance under load
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'pool_pre_ping': True,  # Check connection before using
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
    }
    
    # ============================================================
    # REDIS SETTINGS (SRS Section 2.4, 6.3)
    # ============================================================
    # Redis is used for three purposes (SRS Section 6.3):
    # 1. Caching query results
    # 2. Socket.IO backplane for WebSocket fan-out (Section 5.3)
    # 3. Rate limiting counters (FR-7.1)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Redis connection settings
    REDIS_OPTIONS = {
        'decode_responses': True,  # Automatically decode bytes to strings
        'socket_keepalive': True,  # Keep connections alive
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True,
    }
    
    # ============================================================
    # RABBITMQ SETTINGS (SRS Section 2.4, 6.4)
    # ============================================================
    # RabbitMQ is the message broker for Celery (Section 6.4)
    # Used for background tasks like notifications (FR-8.1)
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672//')
    
    # ============================================================
    # CELERY SETTINGS (SRS Section 3.8, 6.4)
    # ============================================================
    # Celery handles background tasks (FR-8.1)
    # Uses RabbitMQ as broker (SRS Section 6.4)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', RABBITMQ_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    
    # Celery settings from SRS Section 3.8
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    
    # Task time limits (SRS Section 3.8 - background processing)
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
    
    # Retry settings (FR-8.2)
    CELERY_TASK_RETRY_LIMIT = 3  # Maximum retry attempts
    CELERY_TASK_RETRY_BACKOFF = True  # Exponential backoff
    
    # ============================================================
    # JWT AUTHENTICATION SETTINGS (SRS Section 7.3, FR-1.2)
    # ============================================================
    # JWT_SECRET_KEY: Used to sign JWT tokens
    # MUST be changed in production!
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Token expiration times (SRS Section 7.3)
    # Access token: Short-lived (15 minutes as per SRS)
    # Refresh token: Long-lived (7 days as per SRS)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '900'))  # 15 minutes
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '604800'))  # 7 days
    )
    
    # Token security settings
    JWT_TOKEN_LOCATION = ['headers']  # Tokens come in Authorization header
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Algorithm for signing tokens
    JWT_ALGORITHM = 'HS256'
    
    # ============================================================
    # SECURITY SETTINGS (SRS Section 9, NFR-11)
    # ============================================================
    # Bcrypt settings for password hashing (NFR-11)
    # cost=12 means 2^12 rounds of hashing
    # Higher cost = more secure but slower
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', '12'))
    
    # ============================================================
    # CORS SETTINGS (SRS Section 2.1)
    # ============================================================
    # CORS_ORIGINS: Which domains can access our API
    # Development: http://localhost:3000 (React dev server)
    # Production: Your actual domain
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # ============================================================
    # RATE LIMITING SETTINGS (SRS Section 3.7, FR-7.1)
    # ============================================================
    # Rate limits from FR-7.1 and FR-7.3
    RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100/hour')
    RATE_LIMIT_AUTH = os.getenv('RATE_LIMIT_AUTH', '20/hour')
    
    # Rate limit storage uses Redis (FR-7.1)
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # ============================================================
    # WEBSOCKET SETTINGS (SRS Section 7.2, 5.3)
    # ============================================================
    # Socket.IO settings for WebSocket communication
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv(
        'SOCKETIO_CORS_ALLOWED_ORIGINS',
        'http://localhost:3000'
    )
    
    # Redis backplane for cross-node communication (SRS Section 5.3)
    # This ensures FR-4.3: events reach all nodes
    SOCKETIO_MESSAGE_QUEUE = REDIS_URL
    
    # ============================================================
    # CACHE SETTINGS (SRS Section 6.3)
    # ============================================================
    # TTL (Time To Live) for cached data
    CACHE_DEFAULT_TTL = int(os.getenv('CACHE_DEFAULT_TTL', '300'))  # 5 minutes
    CACHE_BOARD_TTL = int(os.getenv('CACHE_BOARD_TTL', '15'))  # 15 seconds (SRS 6.3)
    
    # ============================================================
    # NOTIFICATION SETTINGS (SRS Section 3.6)
    # ============================================================
    # Email settings for notification delivery
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    
    # Daily digest time (FR-6.3)
    DIGEST_SEND_HOUR = int(os.getenv('DIGEST_SEND_HOUR', '9'))  # 9 AM
    DIGEST_SEND_MINUTE = int(os.getenv('DIGEST_SEND_MINUTE', '0'))
    
    # ============================================================
    # LOGGING SETTINGS (SRS Section 4.6, NFR-17)
    # ============================================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/teamup.log')
    
    # ============================================================
    # OBSERVABILITY (SRS Section 4.6, NFR-16)
    # ============================================================
    # Prometheus metrics endpoint
    PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'True').lower() == 'true'
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '5000'))


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Uses PostgreSQL via Docker as specified in SRS Section 2.4
    All environments use the same database engine for consistency
    """
    
    DEBUG = True
    ENV = 'development'
    
    # PostgreSQL in development (via Docker)
    # Default connection matches docker-compose.yml
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://teamup:teamup_password@localhost:5432/teamup_db'
    )
    
    # More permissive rate limits for development
    RATE_LIMIT_DEFAULT = '1000/hour'
    RATE_LIMIT_AUTH = '100/hour'
    
    # Log more details in development
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Uses a separate PostgreSQL database for tests
    """
    
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    
    # PostgreSQL for testing (separate database)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://teamup:teamup_password@localhost:5432/teamup_test_db'
    )
    
    # Disable rate limiting in tests
    RATE_LIMIT_DEFAULT = '1000000/hour'
    RATE_LIMIT_AUTH = '1000000/hour'
    
    # Use a separate Redis database for tests
    REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')
    
    # Shorter token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=300)
    
    # Disable email sending in tests
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    PostgreSQL is REQUIRED (SRS Section 2.4)
    """
    
    DEBUG = False
    ENV = 'production'
    
    # PostgreSQL is required in production (SRS Section 2.4)
    # Must be set in environment variables
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError(
            "DATABASE_URL must be set in production! "
            "PostgreSQL is required (SRS Section 2.4)"
        )
    
    # Ensure PostgreSQL is used (not SQLite)
    if SQLALCHEMY_DATABASE_URI.startswith('sqlite://'):
        raise ValueError(
            "SQLite is not allowed in production! "
            "Use PostgreSQL as specified in SRS Section 2.4"
        )
    
    # Stricter rate limits for production (FR-7.1)
    RATE_LIMIT_DEFAULT = '100/hour'
    RATE_LIMIT_AUTH = '20/hour'
    
    # Production CORS (must be set in environment)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    
    # Production logging
    LOG_LEVEL = 'WARNING'


# ============================================================
# CONFIGURATION SELECTION
# ============================================================
# This maps environment names to configuration classes
# Used by app/__init__.py to load the right config
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config(env_name=None):
    """
    Get the appropriate configuration class for the environment.
    
    Args:
        env_name: Environment name (development, testing, production)
                 If None, uses FLASK_ENV environment variable
    
    Returns:
        Config class appropriate for the environment
    
    Example:
        config = get_config('production')
        print(config.DATABASE_URL)
    """
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', 'development')
    
    return config_map.get(env_name, DevelopmentConfig)
