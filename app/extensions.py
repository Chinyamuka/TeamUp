"""
TeamUp Extensions Module

This module centralizes all Flask extensions used in the application.
By centralizing extensions, we avoid circular imports and maintain
a single source of truth for third-party integrations.

Based on SRS Requirements:
- Section 6.2: SQLAlchemy ORM for PostgreSQL
- Section 6.3: Redis for caching and Socket.IO backplane
- Section 6.4: RabbitMQ via Celery for background tasks
- Section 7.2: SocketIO for WebSocket real-time communication
- Section 7.3: JWT for authentication
- Section 9: Security (CORS, rate limiting)
- FR-8.1: Celery for background processing
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from celery import Celery
import eventlet

# ============================================================
# MONKEY PATCHING FOR WEBSOCKETS
# ============================================================
# eventlet.monkey_patch() makes Python's standard library
# work with eventlet's async framework.
# 
# This is needed for Flask-SocketIO to handle multiple
# WebSocket connections efficiently (SRS Section 5.4)
# 
# What it does:
# - Makes the socket module non-blocking
# - Makes the threading module work with eventlet
# - Makes the os module work with eventlet's event loop
eventlet.monkey_patch()


# ============================================================
# DATABASE ORM - SQLAlchemy (SRS Section 6.2)
# ============================================================
# SQLAlchemy is our Object-Relational Mapper (ORM).
# 
# What is an ORM?
# - It maps Python classes to database tables
# - You work with Python objects instead of writing SQL
# - Handles connection pooling automatically
# 
# Why SQLAlchemy?
# - Most popular ORM for Flask
# - Supports PostgreSQL fully (SRS Section 2.4)
# - Handles migrations via Alembic (SRS Section 2.5, NFR-14)
# - Provides connection pooling for scalability
db = SQLAlchemy()


# ============================================================
# DATABASE MIGRATIONS - Alembic (SRS Section 2.5, NFR-14)
# ============================================================
# Flask-Migrate wraps Alembic for database schema migrations.
# 
# Why migrations?
# - Version control for your database schema
# - Apply changes without losing data
# - Rollback if something goes wrong
# - Team members all use the same schema
# 
# SRS Requirements:
# - Section 2.5: "All schema changes must go through versioned migrations"
# - NFR-14: "Schema changes applied via reversible migrations only"
migrate = Migrate()


# ============================================================
# WEBSOCKET SERVER - SocketIO (SRS Section 7.2, 5.3)
# ============================================================
# Flask-SocketIO adds WebSocket support to Flask.
# 
# What are WebSockets?
# - Persistent, bidirectional communication
# - Server can push updates to clients in real-time
# - Much faster than HTTP polling
# 
# Why SocketIO?
# - SRS Section 7.2: WebSocket events for real-time updates
# - SRS Section 5.3: Redis backplane for cross-node communication
# - SRS Section 4.1: Real-time broadcast under 500ms
# - Automatically falls back to HTTP polling if WebSockets fail
socketio = SocketIO()


# ============================================================
# JWT AUTHENTICATION (SRS Section 7.3, FR-1.2)
# ============================================================
# Flask-JWT-Extended handles JWT (JSON Web Token) authentication.
# 
# What are JWTs?
# - Self-contained tokens with user information
# - Signed with a secret key (can't be forged)
# - Stateless: no server-side session storage
# - Contains expiration time
# 
# SRS Requirements:
# - FR-1.2: "Issue short-lived JWT access token + refresh token"
# - Section 7.3: JWT authentication flow
# - Stateless authentication for horizontal scaling (Section 2.5)
jwt = JWTManager()


# ============================================================
# CROSS-ORIGIN RESOURCE SHARING - CORS (SRS Section 2.1)
# ============================================================
# Flask-CORS allows browsers to make requests from different domains.
# 
# Why CORS?
# - React frontend runs on a different port (localhost:3000)
# - Backend API runs on port 5000
# - Browsers block cross-origin requests for security
# - CORS tells the browser it's safe to allow these requests
# 
# SRS Requirements:
# - Section 2.1: Three-tier architecture with React SPA
# - React client needs to talk to Flask API
cors = CORS()


# ============================================================
# RATE LIMITING (SRS Section 3.7, FR-7.1)
# ============================================================
# Flask-Limiter enforces rate limits on API endpoints.
# 
# Why rate limiting?
# - Prevents abuse (DDoS attacks)
# - Limits API usage by free users
# - Protects shared infrastructure (FR-7.1)
# 
# SRS Requirements:
# - FR-7.1: "Enforce per-user and per-IP request rate limits"
# - FR-7.2: "Return HTTP 429 with Retry-After header"
# - FR-7.3: "Stricter limits on unauthenticated endpoints"
limiter = Limiter(key_func=get_remote_address)


# ============================================================
# REDIS CLIENT WRAPPER (SRS Section 6.3)
# ============================================================
# Redis is used for three purposes in TeamUp:
# 1. Caching - Fast access to frequently used data
# 2. Rate limiting - Counting requests per user/IP
# 3. Socket.IO backplane - Cross-node WebSocket communication
# 
# This wrapper provides a clean interface to Redis operations.
class RedisClient:
    """
    Redis client wrapper for the application.
    
    Why a wrapper class?
    - Single place to manage Redis connections
    - Easy to switch Redis configurations
    - Clean API for common operations
    - Can add logging/metrics around Redis calls
    
    SRS References:
    - Section 6.3: "Read-through cache", "Rate limiting", "Socket.IO backplane"
    - FR-7.1: Redis for rate limit counters
    - Section 5.3: Redis pub/sub for cross-node events
    """
    
    _client = None
    
    def init_app(self, app):
        """
        Initialize Redis connection with app configuration.
        
        Args:
            app: Flask application instance with REDIS_URL config
        
        Why this pattern?
        - Separation of creation and configuration
        - App can provide config, we create the client
        - Easy to test with different Redis instances
        
        SRS Section 6.3: "Redis 7 (cache + Socket.IO backplane + rate-limit counters)"
        """
        redis_url = app.config.get('REDIS_URL')
        
        if not redis_url:
            raise ValueError("REDIS_URL must be configured!")
        
        # Create Redis client with connection pooling
        # decode_responses=True: Redis returns strings instead of bytes
        # socket_keepalive=True: Maintain connections under load
        # socket_connect_timeout=5: Fail fast if Redis is down
        # retry_on_timeout=True: Retry if timeout occurs
        self._client = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test the connection
        try:
            self._client.ping()
            app.logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            app.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    @property
    def client(self):
        """
        Get the Redis client instance.
        
        This property ensures the client is initialized before use.
        """
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call init_app() first.")
        return self._client
    
    # ============================================================
    # WRAPPER METHODS FOR COMMON REDIS OPERATIONS
    # ============================================================
    # These methods provide a clean API and handle errors consistently.
    
    def get(self, key):
        """
        Get a value from Redis by key.
        
        SRS Section 6.3: "Read-through cache" - reading cached data
        """
        return self.client.get(key)
    
    def set(self, key, value, ex=None):
        """
        Set a value in Redis with optional expiry.
        
        Args:
            key: The key to store under
            value: The value to store
            ex: Expiry time in seconds (TTL)
        
        SRS Section 6.3: "Board/task list responses cached with a short TTL"
        """
        return self.client.set(key, value, ex=ex)
    
    def delete(self, key):
        """
        Delete a key from Redis.
        
        SRS Section 6.3: "Invalidated on write via explicit key delete"
        """
        return self.client.delete(key)
    
    def incr(self, key):
        """
        Increment a counter in Redis.
        
        SRS Section 6.3: "Sliding-window counters per user/IP"
        FR-7.1: Rate limiting counters
        """
        return self.client.incr(key)
    
    def expire(self, key, time):
        """
        Set expiry time on a key.
        
        FR-7.1: Rate limit windows expire after time period
        """
        return self.client.expire(key, time)
    
    def pubsub(self):
        """
        Get a pubsub connection for WebSocket backplane.
        
        SRS Section 5.3: "Redis pub/sub is mandatory for cross-node WebSocket delivery"
        FR-4.3: "Broadcast events consistently regardless of application node"
        """
        return self.client.pubsub()
    
    def publish(self, channel, message):
        """
        Publish a message to a channel.
        
        Used for: Socket.IO backplane (SRS Section 5.3)
        - When Node 1 emits an event, it publishes to Redis
        - Node 2 subscribes and forwards to its connected clients
        """
        return self.client.publish(channel, message)
    
    def sadd(self, key, *values):
        """
        Add members to a Redis set.
        
        Used for: Presence tracking (SRS Section 3.5)
        - Track which users are online
        - Track which users are viewing a board
        """
        return self.client.sadd(key, *values)
    
    def srem(self, key, *values):
        """
        Remove members from a Redis set.
        
        Used for: Presence cleanup (FR-5.3)
        - Remove user when they disconnect
        """
        return self.client.srem(key, *values)
    
    def smembers(self, key):
        """
        Get all members of a Redis set.
        
        Used for: Showing online users (FR-5.1)
        """
        return self.client.smembers(key)


# Redis client instance
# This is the instance we import and use throughout the app
redis_client = RedisClient()


# ============================================================
# CELERY FOR BACKGROUND TASKS (SRS Section 3.8, 6.4)
# ============================================================
# Celery handles asynchronous background tasks.
# 
# What are background tasks?
# - Tasks that shouldn't block the request/response cycle
# - Example: Sending emails, generating reports, cleaning up data
# 
# Why Celery? (SRS Section 3.8)
# - FR-8.1: "Process notification delivery, digest generation, and cleanup jobs"
# - FR-8.2: "Retry failed background jobs with exponential backoff"
# - FR-8.3: "Support scheduled/periodic jobs via Celery beat"
# - Offloads slow operations from the request path
# 
# Why RabbitMQ? (SRS Section 6.4)
# - Durable message queue that survives crashes
# - Supports acknowledgements (messages not lost)
# - Routing to different queues for different task types
def make_celery(app=None):
    """
    Create and configure Celery instance.
    
    This function sets up Celery with RabbitMQ as the broker
    and Redis as the result backend.
    
    Args:
        app: Flask application instance (optional)
    
    Returns:
        Celery: Configured Celery application
    
    SRS References:
    - Section 3.8: "Process notification delivery, digest generation, and cleanup jobs"
    - Section 6.4: "RabbitMQ (durable task queue for Celery workers)"
    """
    # Create Celery application
    # 'teamup' is the name of the Celery app
    celery = Celery(
        'teamup',
        broker=app.config['CELERY_BROKER_URL'] if app else None,
        backend=app.config['CELERY_RESULT_BACKEND'] if app else None
    )
    
    if app:
        # Update Celery with Flask app configuration
        celery.conf.update(app.config)
        
        # ============================================================
        # TASK ROUTING (SRS Section 6.4)
        # ============================================================
        # Route different task types to different queues.
        # This allows us to scale workers independently.
        # 
        # Example:
        # - Notifications queue: One set of workers
        # - Digests queue: Another set of workers
        # - Cleanup queue: A third set
        #
        # SRS Section 6.4: "Topic exchange routing by job type"
        celery.conf.task_routes = {
            'app.tasks.notifications.*': {'queue': 'notifications'},
            'app.tasks.digests.*': {'queue': 'digests'},
            'app.tasks.cleanup.*': {'queue': 'cleanup'},
        }
        
        # Default queue for tasks without specific routing
        celery.conf.task_default_queue = 'default'
        celery.conf.task_default_exchange = 'default'
        celery.conf.task_default_routing_key = 'default'
        
        # ============================================================
        # TASK TRACKING (SRS Section 3.8)
        # ============================================================
        # Track when tasks start (for monitoring)
        celery.conf.task_track_started = True
        
        # Task time limits (prevent runaway tasks)
        # SRS Section 3.8: Background processing with timeouts
        celery.conf.task_time_limit = 30 * 60  # 30 minutes
        celery.conf.task_soft_time_limit = 25 * 60  # 25 minutes
        
        # ============================================================
        # RESULT BACKEND (SRS Section 6.4)
        # ============================================================
        # Store task results for 1 hour
        # Useful for debugging and monitoring
        celery.conf.result_expires = 3600
        
        # ============================================================
        # SCHEDULED TASKS - Celery Beat (SRS Section 3.8, FR-8.3)
        # ============================================================
        # Periodic tasks that run on a schedule
        #
        # FR-8.3: "Support scheduled/periodic jobs via Celery beat"
        celery.conf.beat_schedule = {
            # Send daily digest emails (SRS Section 3.6, FR-6.3)
            'send-daily-digests': {
                'task': 'app.tasks.digests.send_daily_digests',
                'schedule': 86400,  # 24 hours
                'args': ()
            },
            # Clean up expired sessions and old data
            'cleanup-expired-sessions': {
                'task': 'app.tasks.cleanup.cleanup_expired_sessions',
                'schedule': 3600,  # 1 hour
                'args': ()
            },
            # Send reminders for overdue tasks
            'send-overdue-reminders': {
                'task': 'app.tasks.notifications.send_overdue_reminders',
                'schedule': 3600,  # 1 hour
                'args': ()
            }
        }
        
        # ============================================================
        # DISCOVER TASKS (SRS Section 6.4)
        # ============================================================
        # Automatically find all tasks in the app.tasks package
        celery.autodiscover_tasks(['app.tasks'])
    
    return celery


# Create Celery instance
# This is the instance we import and use throughout the app
celery = make_celery()
