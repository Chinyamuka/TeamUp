"""
Board API Routes with Role-Based Access Control (RBAC)

This module handles board management endpoints with permission checks.

SRS References:
- FR-2.2: Board with custom columns (To Do, In Progress, Done)
- FR-2.4: Only Owners/Admins can remove members or delete boards
- FR-1.3: Role-based access control (Owner, Admin, Member)
- Section 9: Server-side authorization enforcement
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Project, Board, Column
from app.utils.permissions import (
    get_user_role,
    has_role,
    can_view_project,
    can_manage_boards,
    can_create_task,
    can_edit_task,
    can_delete_task,
    get_user_role_display
)

# Create blueprint
boards_bp = Blueprint('boards', __name__, url_prefix='/api/boards')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_project_or_404(project_id, user):
    """Get a project by ID and check if user has access."""
    project = Project.query.filter_by(id=project_id, is_archived=False).first()
    if not project:
        return None
    if not project.is_member(user):
        return None
    return project


def get_board_or_404(board_id, user):
    """Get a board by ID and check if user has access."""
    board = Board.query.filter_by(id=board_id, is_archived=False).first()
    if not board:
        return None
    if not board.project.is_member(user):
        return None
    return board


def check_board_permission(board, user, action):
    """
    Check if user has permission for a board action.
    
    Actions:
        - 'view': Can view board
        - 'create': Can create board
        - 'edit': Can edit board
        - 'delete': Can delete board
        - 'reorder': Can reorder columns
    """
    project = board.project
    user_role = get_user_role(user, project)
    
    if action == 'view':
        return user_role is not None
    elif action == 'create':
        return user_role in ['owner', 'admin', 'member']
    elif action in ['edit', 'delete', 'reorder']:
        return user_role in ['owner', 'admin']
    
    return False


# ============================================================
# ENDPOINTS WITH RBAC
# ============================================================

@boards_bp.route('/project/<int:project_id>', methods=['GET'])
@jwt_required()
def list_boards(project_id):
    """
    List all boards in a project.
    
    SRS Reference:
        FR-2.2: "Board with custom columns (To Do, In Progress, Done)"
    
    Returns:
        200: List of boards
        403: User doesn't have access
        404: Project not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Check if user can view this project
    if not can_view_project(user, project):
        return jsonify({'error': 'You do not have access to this project'}), 403
    
    boards = project.boards.filter_by(is_archived=False).all()
    
    boards_data = []
    for board in boards:
        board_dict = board.to_dict(include_columns=True)
        board_dict['user_role'] = get_user_role(user, project)
        boards_data.append(board_dict)
    
    return jsonify({
        'boards': boards_data,
        'count': len(boards_data)
    }), 200


@boards_bp.route('/project/<int:project_id>', methods=['POST'])
@jwt_required()
def create_board(project_id):
    """
    Create a new board in a project.
    
    SRS Reference:
        FR-2.2: "Board with custom columns (To Do, In Progress, Done)"
    
    Request Body:
        {
            "name": "Board Name",
            "description": "Board description (optional)"
        }
    
    Returns:
        201: Board created with default columns
        403: User doesn't have permission
        404: Project not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Check if user can create boards (member+)
    if not has_role(user, project, 'member'):
        return jsonify({
            'error': 'You do not have permission to create boards',
            'your_role': get_user_role(user, project),
            'required_role': 'member'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Board name is required'}), 400
    
    description = data.get('description', '')
    
    # Get position
    last_board = project.boards.filter_by(is_archived=False).order_by(Board.position.desc()).first()
    position = (last_board.position + 1) if last_board else 0
    
    # Create board
    board = Board(
        project_id=project.id,
        name=name,
        description=description,
        position=position
    )
    db.session.add(board)
    db.session.flush()
    
    # Create default columns
    default_columns = [
        Column(name='To Do', position=0, board_id=board.id),
        Column(name='In Progress', position=1, board_id=board.id),
        Column(name='Done', position=2, board_id=board.id)
    ]
    
    for column in default_columns:
        db.session.add(column)
    
    db.session.commit()
    
    board_dict = board.to_dict(include_columns=True)
    board_dict['user_role'] = get_user_role(user, project)
    
    return jsonify({
        'message': 'Board created successfully',
        'board': board_dict
    }), 201


@boards_bp.route('/<int:board_id>', methods=['GET'])
@jwt_required()
def get_board(board_id):
    """
    Get a specific board by ID with all columns and tasks.
    
    SRS Reference:
        Section 7.1: GET /api/boards/:id
    
    Returns:
        200: Board details with columns and tasks
        403: User doesn't have access
        404: Board not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    board = get_board_or_404(board_id, user)
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Check if user can view this board
    if not check_board_permission(board, user, 'view'):
        return jsonify({'error': 'You do not have access to this board'}), 403
    
    board_dict = board.to_dict(include_columns=True)
    board_dict['user_role'] = get_user_role(user, board.project)
    
    return jsonify({
        'board': board_dict
    }), 200


@boards_bp.route('/<int:board_id>', methods=['PUT'])
@jwt_required()
def update_board(board_id):
    """
    Update a board.
    
    Request Body:
        {
            "name": "New Board Name",
            "description": "New description",
            "position": 1
        }
    
    Returns:
        200: Board updated
        403: User doesn't have permission
        404: Board not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    board = get_board_or_404(board_id, user)
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Check if user can edit board (admin+)
    if not check_board_permission(board, user, 'edit'):
        return jsonify({
            'error': 'You do not have permission to update this board',
            'your_role': get_user_role(user, board.project),
            'required_role': 'admin'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    description = data.get('description')
    position = data.get('position')
    is_archived = data.get('is_archived')
    
    if name is not None:
        board.name = name
    
    if description is not None:
        board.description = description
    
    if position is not None:
        board.position = position
    
    if is_archived is not None:
        if is_archived:
            board.archive()
        else:
            board.unarchive()
    
    db.session.commit()
    
    board_dict = board.to_dict(include_columns=True)
    board_dict['user_role'] = get_user_role(user, board.project)
    
    return jsonify({
        'message': 'Board updated successfully',
        'board': board_dict
    }), 200


@boards_bp.route('/<int:board_id>', methods=['DELETE'])
@jwt_required()
def archive_board(board_id):
    """
    Archive (soft delete) a board.
    
    SRS Reference:
        FR-2.4: "Only Owners/Admins can remove members or delete boards"
    
    Returns:
        200: Board archived
        403: User doesn't have permission
        404: Board not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    board = get_board_or_404(board_id, user)
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Check if user can delete board (admin+)
    if not check_board_permission(board, user, 'delete'):
        return jsonify({
            'error': 'You do not have permission to archive this board',
            'your_role': get_user_role(user, board.project),
            'required_role': 'admin'
        }), 403
    
    board.archive()
    db.session.commit()
    
    return jsonify({
        'message': 'Board archived successfully'
    }), 200


@boards_bp.route('/<int:board_id>/reorder', methods=['POST'])
@jwt_required()
def reorder_columns(board_id):
    """
    Reorder columns within a board.
    
    SRS Reference:
        FR-3.2: "Drag-and-drop reordering of tasks within and across columns"
    
    Request Body:
        {
            "column_order": [3, 1, 2]  # List of column IDs in desired order
        }
    
    Returns:
        200: Columns reordered
        403: User doesn't have permission
        404: Board not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    board = get_board_or_404(board_id, user)
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Check if user can reorder columns (admin+)
    if not check_board_permission(board, user, 'reorder'):
        return jsonify({
            'error': 'You do not have permission to reorder columns',
            'your_role': get_user_role(user, board.project),
            'required_role': 'admin'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    column_order = data.get('column_order')
    if not column_order:
        return jsonify({'error': 'Column order is required'}), 400
    
    # Reorder columns
    board.reorder_columns(column_order)
    db.session.commit()
    
    return jsonify({
        'message': 'Columns reordered successfully'
    }), 200


@boards_bp.route('/<int:board_id>/permissions', methods=['GET'])
@jwt_required()
def get_board_permissions(board_id):
    """
    Get the current user's permissions for a board.
    
    Returns:
        200: Permission summary
        404: Board not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    board = get_board_or_404(board_id, user)
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    user_role = get_user_role(user, board.project)
    
    return jsonify({
        'board_id': board_id,
        'user_role': user_role,
        'permissions': {
            'can_view': check_board_permission(board, user, 'view'),
            'can_edit': check_board_permission(board, user, 'edit'),
            'can_delete': check_board_permission(board, user, 'delete'),
            'can_reorder': check_board_permission(board, user, 'reorder'),
            'can_create_task': has_role(user, board.project, 'member'),
            'can_edit_task': has_role(user, board.project, 'member'),
            'can_delete_task': has_role(user, board.project, 'member')
        }
    }), 200
