"""
TeamUp Application Factory

This module creates and configures the Flask application.
The following the application factory pattern allows:
- Multiple app instances for different environments
- Easy testing with different configurations
- Clean separation of configuration and app creation

SRS References:
- Section 2.1: Three-tier architecture
- Section 2.5: Stateless application servers
- Section 5.1: Modular monolith architecture
- Section 7: API Design
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config.settings import get_config
from app.extensions import db, redis_client, socketio, celery, jwt, cors, limiter


def create_app(config_name=None):
    """
    Application factory function.
    
    This function creates a configured Flask application instance.
    It loads the appropriate configuration, initializes extensions,
    registers blueprints, and sets up error handlers.
    
    Args:
        config_name: Optional configuration environment name.
                    If None, uses FLASK_ENV environment variable.
                    Defaults to 'development'.
    
    Returns:
        Flask: Configured Flask application instance
    
    SRS References:
    - Section 2.5: "Application servers must be stateless"
    - Section 5.2: "N identical Flask + Flask-SocketIO nodes"
    """
    
    # ============================================================
    # STEP 1: DETERMINE CONFIGURATION
    # ============================================================
    # Get the appropriate configuration class based on environment
    # Development, Testing, or Production
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_class = get_config(config_name)
    
    # ============================================================
    # STEP 2: CREATE FLASK APP INSTANCE
    # ============================================================
    # Create the Flask application with:
    # - __name__: Helps Flask find resources (templates, static files)
    # - instance_relative_config: Allow instance-specific config
    app = Flask(
        __name__,
        instance_relative_config=True
    )
    
    # ============================================================
    # STEP 3: LOAD CONFIGURATION
    # ============================================================
    # Load configuration from the config class
    # Config values come from environment variables via settings.py
    app.config.from_object(config_class)
    
    # Create instance folder if it doesn't exist
    # Used for instance-specific files (like SQLite in some cases)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # ============================================================
    # STEP 4: INITIALIZE EXTENSIONS
    # ============================================================
    # Each extension is initialized with the app instance
    # This connects the extension to our Flask app
    
    # Database ORM (SRS Section 6.2)
    # SQLAlchemy - connects to PostgreSQL
    db.init_app(app)
    
    # Database Migrations (SRS Section 2.5, NFR-14)
    # Alembic - handles schema changes
    Migrate(app, db, directory='migrations')
    
    # JWT Authentication (SRS Section 7.3, FR-1.2)
    # Handles JWT token creation and validation
    jwt.init_app(app)
    
    # CORS (SRS Section 2.1)
    # Allows React frontend to call the API
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 86400  # 24 hours
        }
    })
    
    # Rate Limiting (SRS Section 3.7, FR-7.1)
    # Protects infrastructure from abuse
    limiter.init_app(app)
    
    # Redis - Initialize connection
    # Used for caching, backplane, rate limiting (Section 6.3)
    redis_client.init_app(app)
    
    # SocketIO - WebSocket for real-time (SRS Section 7.2)
    # Handles real-time event broadcasting
    # Uses Redis as message queue for cross-node communication (Section 5.3)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS', ['*']),
        message_queue=app.config.get('REDIS_URL'),
        async_mode='eventlet',
        ping_timeout=60,
        ping_interval=25
    )
    
    # Celery - Background tasks (SRS Section 3.8)
    # Updates Celery configuration from Flask app
    celery.conf.update(app.config)
    app.extensions['celery'] = celery
    
    # ============================================================
    # STEP 5: REGISTER BLUEPRINTS (API ROUTES)
    # ============================================================
    # Blueprints organize routes by domain.
    # Each blueprint handles a specific area:
    # - auth: Authentication endpoints (FR-1.1 to FR-1.5)
    # - projects: Project/Board management (FR-2.1 to FR-2.4)
    # - tasks: Task operations (FR-3.1 to FR-3.5)
    # - notifications: User notifications (FR-6.1 to FR-6.4)
    #
    # Note: Blueprints will be created in later files
    # We'll import them here once they exist
    
    # Register authentication blueprint
    # from app.api.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Register projects/boards blueprint
    # from app.api.projects import projects_bp
    # app.register_blueprint(projects_bp, url_prefix='/api/projects')
    
    # Register tasks blueprint
    # from app.api.tasks import tasks_bp
    # app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    
    # Register notifications blueprint
    # from app.api.notifications import notifications_bp
    # app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    
    # ============================================================
    # STEP 6: CONFIGURE WEBSOCKET HANDLERS
    # ============================================================
    # WebSocket event handlers for real-time communication
    # These handle events like:
    # - join_board: Subscribe to board updates
    # - task_created: Broadcast new task
    # - presence_update: User online/offline status
    #
    # Handlers will be imported from app.websocket.events
    # from app.websocket.events import register_socket_handlers
    # register_socket_handlers(socketio)
    
    # ============================================================
    # STEP 7: CONFIGURE ERROR HANDLERS
    # ============================================================
    # Global error handlers for consistent API responses
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 - Resource not found."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 - Bad request."""
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid request parameters'
        }), 400
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """
        Handle 429 - Rate limit exceeded.
        
        SRS Reference:
        - FR-7.2: "Return HTTP 429 with a Retry-After header"
        """
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later.'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 - Internal server error."""
        # Log the error for debugging
        app.logger.error(f"Internal Server Error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Something went wrong on our end'
        }), 500
    
    # ============================================================
    # STEP 8: HEALTH CHECK ENDPOINT
    # ============================================================
    # Health check for load balancers and monitoring
    # SRS Reference: NFR-16 - "Application exposes health and metrics endpoints"
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'environment': app.config.get('ENV', 'unknown'),
            'database': 'connected'  # We'll add actual check later
        }), 200
    
    @app.route('/')
    def index():
        """Root endpoint with API information."""
        return jsonify({
            'name': 'TeamUp API',
            'version': '1.0.0',
            'description': 'Distributed Real-Time Collaborative Task Management System',
            'endpoints': {
                'health': '/health',
                'api': '/api/',
                'docs': '/api/docs'  # Future API documentation
            }
        }), 200
    
    # ============================================================
    # STEP 9: BEFORE/REQUEST HANDLERS
    # ============================================================
    # These run before every request
    
    @app.before_request
    def before_request():
        """
        Request preprocessing.
        
        - Logs incoming requests (NFR-17: Structured logs)
        - Adds request ID for tracing
        - Sets up a database session if needed
        """
        # Log request details (SRS Section 4.6, NFR-17)
        app.logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
    
    @app.after_request
    def after_request(response):
        """
        Request post-processing.
        
        - Adds security headers
        - Logs response status
        """
        # Add security headers (SRS Section 9)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    # ============================================================
    # STEP 10: RETURN THE CONFIGURED APP
    # ============================================================
    return app
