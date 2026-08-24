"""
TeamUp Application Entry Point

This script starts the Flask application with SocketIO support.
It serves as the main entry point for both development and production.

SRS References:
- Section 2.4: "Linux containers (Docker), Python 3.11 runtime"
- Section 5.1: "Modular monolith (auth, boards, tasks, notifications as internal modules)"
- Section 7.2: "WebSocket Events (Socket.IO)"
- Section 11: "Application Server: Gunicorn + gevent"

For production, this should be run with Gunicorn:
    gunicorn -k gevent -w 4 run:app

For development, this runs the built-in Flask development server.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
# This ensures all imports work correctly
sys.path.insert(0, str(Path(__file__).parent))

# Import the create_app factory and socketio instance
# create_app: Creates our Flask application
# socketio: WebSocket server for real-time updates
from app import create_app
from app.extensions import socketio


# ============================================================
# CREATE THE APPLICATION INSTANCE
# ============================================================
# Determine environment from FLASK_ENV environment variable
# Default: development (safest default for local development)
env = os.getenv('FLASK_ENV', 'development')

# Create the app with the appropriate configuration
# This follows the application factory pattern (app/__init__.py)
app = create_app(env)

# Get host and port from environment variables with defaults
# This allows overriding for Docker or different environments
host = os.getenv('FLASK_HOST', '0.0.0.0')  # 0.0.0.0 allows external connections
port = int(os.getenv('FLASK_PORT', 5000))  # Default port 5000

# Debug mode from environment (default: False for safety)
# In production, this should ALWAYS be False!
debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == '__main__':
    """
    Start the application with SocketIO support.
    
    SocketIO provides WebSocket capabilities for real-time features:
    - Real-time task updates (FR-4.1)
    - Presence indicators (FR-5.1)
    - Live collaboration
    
    For development, we use the built-in server with debug mode.
    For production, use Gunicorn with gevent worker class.
    
    Production command:
    gunicorn -k gevent -w 4 --worker-connections 1000 run:app
    
    SRS References:
    - Section 7.2: WebSocket Events (Socket.IO)
    - Section 5.4: Flask-SocketIO, eventlet
    - Section 11: Gunicorn + gevent for production
    """
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     TeamUp Backend Server -(Zactech Software Services )   ║
    ║                                                           ║
    ║   Environment: {env.upper():<20}                          ║
    ║   Host:        {host:<20}                                 ║
    ║   Port:        {port:<20}                                 ║
    ║   Debug:       {str(debug):<20}                           ║
    ║                                                           ║
    ║   API URL:     http://{host}:{port}/                      ║
    ║   Health:      http://{host}:{port}/health                ║
    ║   WebSocket:   ws://{host}:{port}/socket.io/              ║
    ║                                                           ║
    ║   For production, use:                                    ║
    ║   gunicorn -k gevent -w 4 run:app                         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Start the SocketIO server
    # allow_unsafe_werkzeug=True is only for development
    # It allows Werkzeug's development server to work with SocketIO
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True  # Only for development!
    )
