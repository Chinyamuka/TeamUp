"""
WebSocket Event Handlers - Real-Time Collaboration
"""

# ============================================================
# IMPORTS
# ============================================================
from flask import request  # Added for request.sid
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token

from app.extensions import socketio, redis_client
from app.models import User, Task, Board


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token(token):
    """Extract user from JWT token."""
    try:
        decoded = decode_token(token)
        user_id = decoded.get('sub')
        if user_id:
            return User.query.get(int(user_id))
    except Exception:
        return None
    return None


def get_board_or_404(board_id):
    """Get a board by ID (only if it's not archived)."""
    return Board.query.filter_by(id=board_id, is_archived=False).first()


def broadcast_to_board(board_id, event, data):
    """Broadcast an event to all clients in a board room."""
    room = f'board_{board_id}'
    socketio.emit(event, data, room=room)


def update_presence(board_id, user_id, status):
    """Update presence state in Redis."""
    key = f'presence:board_{board_id}'
    
    if status == 'online':
        redis_client.sadd(key, str(user_id))
        redis_client.expire(key, 3600)
    else:
        redis_client.srem(key, str(user_id))


def get_online_users(board_id):
    """Get all online users for a board."""
    key = f'presence:board_{board_id}'
    members = redis_client.smembers(key)
    return [int(m) for m in members] if members else []


# ============================================================
# WEBSOCKET EVENT HANDLERS
# ============================================================

@socketio.on('connect')
def handle_connect(auth=None):
    """
    Handle client connection.
    
    SocketIO passes authentication data to this handler.
    We accept the 'auth' parameter but don't use it here.
    """
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")
    # Presence cleanup is handled by Redis expiry


@socketio.on('join_board')
def handle_join_board(data):
    """
    Join a board room and update presence.
    
    Request Data:
        {
            "token": "access_token_here",
            "board_id": 1
        }
    """
    token = data.get('token')
    board_id = data.get('board_id')
    
    if not token or not board_id:
        emit('error', {'message': 'Token and board_id are required'})
        return
    
    user = get_user_from_token(token)
    if not user:
        emit('error', {'message': 'Invalid token'})
        return
    
    board = get_board_or_404(board_id)
    if not board:
        emit('error', {'message': 'Board not found'})
        return
    
    if not board.project.is_member(user):
        emit('error', {'message': 'You do not have access to this board'})
        return
    
    room = f'board_{board_id}'
    join_room(room)
    
    update_presence(board_id, user.id, 'online')
    online_users = get_online_users(board_id)
    
    broadcast_to_board(board_id, 'presence_update', {
        'user_id': user.id,
        'user_name': user.full_name,
        'status': 'online',
        'online_users': online_users
    })
    
    emit('joined_board', {
        'board_id': board_id,
        'online_users': online_users
    })


@socketio.on('leave_board')
def handle_leave_board(data):
    """Leave a board room."""
    board_id = data.get('board_id')
    
    if not board_id:
        emit('error', {'message': 'board_id is required'})
        return
    
    room = f'board_{board_id}'
    leave_room(room)
    
    emit('left_board', {'board_id': board_id})


@socketio.on('task_created')
def handle_task_created(data):
    """Broadcast task creation to board subscribers."""
    board_id = data.get('board_id')
    task_data = data.get('task')
    
    if board_id and task_data:
        broadcast_to_board(board_id, 'task_created', task_data)


@socketio.on('task_updated')
def handle_task_updated(data):
    """Broadcast task update to board subscribers."""
    board_id = data.get('board_id')
    task_data = data.get('task')
    
    if board_id and task_data:
        broadcast_to_board(board_id, 'task_updated', task_data)


@socketio.on('task_moved')
def handle_task_moved(data):
    """Broadcast task movement to board subscribers."""
    board_id = data.get('board_id')
    task_data = data.get('task')
    
    if board_id and task_data:
        broadcast_to_board(board_id, 'task_moved', task_data)


@socketio.on('task_deleted')
def handle_task_deleted(data):
    """Broadcast task deletion to board subscribers."""
    board_id = data.get('board_id')
    task_id = data.get('task_id')
    
    if board_id and task_id:
        broadcast_to_board(board_id, 'task_deleted', {'task_id': task_id})


@socketio.on('presence_update')
def handle_presence_update(data):
    """Handle manual presence update (e.g., typing, viewing task)."""
    board_id = data.get('board_id')
    status = data.get('status')
    
    if board_id:
        broadcast_to_board(board_id, 'presence_update', {
            'user_id': data.get('user_id'),
            'user_name': data.get('user_name'),
            'status': status
        })


# ============================================================
# REGISTER EVENT HANDLERS
# ============================================================

def register_socket_handlers(sio):
    """Register all SocketIO event handlers."""
    # The handlers are already decorated with @socketio.on()
    pass
