"""
TeamUp Application Entry Point
"""

import os
import eventlet

# Monkey patch before importing anything else
eventlet.monkey_patch()

from app import create_app
from app.extensions import socketio

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

host = os.getenv('FLASK_HOST', '0.0.0.0')
port = int(os.getenv('FLASK_PORT', 5000))
debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

if __name__ == '__main__':
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     TeamUp Backend Server -(Zactech Software Services )   ║
    ║                                                           ║
    ║   Environment: {env.upper():<20}                         ║
    ║   Host:        {host:<20}                                ║
    ║   Port:        {port:<20}                                ║
    ║   Debug:       {str(debug):<20}                          ║
    ║                                                           ║
    ║   API URL:     http://{host}:{port}/                     ║
    ║   Health:      http://{host}:{port}/health                ║
    ║   WebSocket:   ws://{host}:{port}/socket.io/              ║
    ║                                                           ║
    ║   For production, use:                                    ║
    ║   gunicorn -k gevent -w 4 run:app                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )
