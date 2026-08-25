"""
TeamUp Application Factory
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
    """

    # Determine configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    config_class = get_config(config_name)

    # Create Flask app instance
    app = Flask(
        __name__,
        instance_relative_config=True
    )

    # Load configuration
    app.config.from_object(config_class)

    # Create instance folder if it doesn't exist
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)

    # Database Migrations - Alembic
    Migrate(app, db, directory='migrations')

    # Import models for Alembic detection
    # This must happen AFTER db.init_app() but BEFORE we use models
    from app.models import User, Project, Board, Column, Task
    from app.models import TaskAssignment, Comment, Notification

    # JWT Authentication
    jwt.init_app(app)

    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 86400
        }
    })

    # Rate Limiting
    limiter.init_app(app)

    # Redis
    redis_client.init_app(app)

    # SocketIO - FIXED: Allow all origins for development
    socketio.init_app(
        app,
        cors_allowed_origins="*",  # Allow all origins for development
        message_queue=app.config.get('REDIS_URL'),
        async_mode='eventlet',
        ping_timeout=60,
        ping_interval=25
    )

    # Celery
    celery.conf.update(app.config)
    app.extensions['celery'] = celery

    # ============================================================
    # REGISTER BLUEPRINTS (API ROUTES)
    # ============================================================
    # Register authentication blueprint
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register projects blueprint
    from app.api.projects import projects_bp
    app.register_blueprint(projects_bp)

    # Register boards blueprint
    from app.api.boards import boards_bp
    app.register_blueprint(boards_bp)

    # Register tasks blueprint
    from app.api.tasks import tasks_bp
    app.register_blueprint(tasks_bp)

    # Register task assignments blueprint
    from app.api.task_assignments import assignments_bp
    app.register_blueprint(assignments_bp)

    # Register comments blueprint
    from app.api.comments import comments_bp
    app.register_blueprint(comments_bp)

    # ============================================================
    # REGISTER WEBSOCKET EVENT HANDLERS
    # ============================================================
    from app.websocket.events import register_socket_handlers
    register_socket_handlers(socketio)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'Invalid request parameters'
        }), 400

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal Server Error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Something went wrong on our end'
        }), 500

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'environment': app.config.get('ENV', 'unknown'),
            'database': 'connected'
        }), 200

    @app.route('/')
    def index():
        return jsonify({
            'name': 'TeamUp API',
            'version': '1.0.0',
            'description': 'Distributed Real-Time Collaborative Task Management System',
            'endpoints': {
                'health': '/health',
                'api': '/api/',
                'docs': '/api/docs'
            }
        }), 200

    # Before/after request handlers
    @app.before_request
    def before_request():
        app.logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )

    @app.after_request
    def after_request(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    return app
