"""
Task API Routes with Role-Based Access Control (RBAC)

This module handles task management endpoints with permission checks.

SRS References:
- FR-3.1: Task CRUD with title, description, labels, due date
- FR-3.2: Drag-and-drop reordering within and across columns
- FR-3.3: Assigning a task to one or more project members
- FR-1.3: Role-based access control (Owner, Admin, Member)
- Section 9: Server-side authorization enforcement
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import db
from app.models import User, Project, Board, Column, Task, TaskAssignment
from app.utils.permissions import (
    get_user_role,
    has_role,
    can_view_project,
    can_create_task,
    can_edit_task,
    can_delete_task,
    get_user_role_display
)

# Create blueprint
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_column_or_404(column_id, user):
    """Get a column by ID and check if user has access."""
    column = Column.query.filter_by(id=column_id, is_archived=False).first()
    if not column:
        return None
    if not column.board.project.is_member(user):
        return None
    return column


def get_task_or_404(task_id, user):
    """Get a task by ID and check if user has access."""
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return None
    if not task.column.board.project.is_member(user):
        return None
    return task


def check_task_permission(task, user, action):
    """
    Check if user has permission for a task action.
    
    Actions:
        - 'view': Can view task
        - 'create': Can create task
        - 'edit': Can edit task
        - 'delete': Can delete task
        - 'assign': Can assign users
    """
    project = task.column.board.project
    user_role = get_user_role(user, project)
    
    if action == 'view':
        return user_role is not None
    elif action == 'create':
        return user_role in ['owner', 'admin', 'member']
    elif action in ['edit', 'delete', 'assign']:
        return user_role in ['owner', 'admin', 'member']
    
    return False


# ============================================================
# TASK ENDPOINTS WITH RBAC
# ============================================================

@tasks_bp.route('/column/<int:column_id>/tasks', methods=['GET'])
@jwt_required()
def list_tasks(column_id):
    """
    List all tasks in a column.
    
    SRS Reference:
        Section 7.1: REST API returns task data
        Section 6.1: Column (1) --- (M) Task
    
    Query Parameters:
        include_archived: Include archived tasks (default: false)
    
    Returns:
        200: List of tasks
        403: User doesn't have permission
        404: Column not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    # Check if user can view this column's board
    if not can_view_project(user, column.board.project):
        return jsonify({'error': 'You do not have access to this board'}), 403
    
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    
    if include_archived:
        tasks = column.tasks.all()
    else:
        tasks = column.tasks.filter_by(is_archived=False).all()
    
    tasks_data = []
    for task in tasks:
        task_dict = task.to_dict(include_assignees=True)
        task_dict['user_role'] = get_user_role(user, column.board.project)
        tasks_data.append(task_dict)
    
    return jsonify({
        'tasks': tasks_data,
        'count': len(tasks_data)
    }), 200


@tasks_bp.route('/column/<int:column_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(column_id):
    """
    Create a new task in a column.
    
    SRS Reference:
        FR-3.1: "Create tasks with title, description, labels, due date"
    
    Request Body:
        {
            "title": "Fix login bug",
            "description": "Users can't log in with special characters",
            "due_date": "2026-09-01T00:00:00",
            "priority": "high",
            "labels": ["bug", "frontend"],
            "estimated_hours": 2.5
        }
    
    Returns:
        201: Task created successfully
        403: User doesn't have permission
        404: Column not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    # Check if user can create tasks (member+)
    if not has_role(user, column.board.project, 'member'):
        return jsonify({
            'error': 'You do not have permission to create tasks',
            'your_role': get_user_role(user, column.board.project),
            'required_role': 'member'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Task title is required'}), 400
    
    description = data.get('description', '')
    due_date_str = data.get('due_date')
    priority = data.get('priority', 'medium')
    labels = data.get('labels', [])
    estimated_hours = data.get('estimated_hours')
    
    # Parse due_date if provided
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    # Validate priority
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if priority not in valid_priorities:
        return jsonify({'error': f'Priority must be one of: {", ".join(valid_priorities)}'}), 400
    
    # Get position (add to the end)
    last_task = column.tasks.filter_by(is_archived=False).order_by(Task.position.desc()).first()
    position = (last_task.position + 1) if last_task else 0
    
    # Create task
    task = Task(
        column_id=column.id,
        title=title,
        description=description,
        due_date=due_date,
        position=position,
        priority=priority,
        labels=labels,
        estimated_hours=estimated_hours
    )
    
    db.session.add(task)
    db.session.commit()
    
    task_dict = task.to_dict(include_assignees=True)
    task_dict['user_role'] = get_user_role(user, column.board.project)
    
    return jsonify({
        'message': 'Task created successfully',
        'task': task_dict
    }), 201


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """
    Get a specific task by ID.
    
    SRS Reference:
        Section 7.1: GET /api/tasks/:id
    
    Returns:
        200: Task details with assignees and comments
        403: User doesn't have access
        404: Task not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Check if user can view this task
    if not check_task_permission(task, user, 'view'):
        return jsonify({'error': 'You do not have access to this task'}), 403
    
    task_dict = task.to_dict(include_assignees=True, include_comments=True)
    task_dict['user_role'] = get_user_role(user, task.column.board.project)
    
    return jsonify({
        'task': task_dict
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """
    Update a task.
    
    SRS Reference:
        FR-3.1: "Update tasks with title, description, labels, due date"
    
    Request Body:
        {
            "title": "New title",
            "description": "New description",
            "due_date": "2026-09-02T00:00:00",
            "priority": "critical",
            "labels": ["bug", "backend", "urgent"],
            "estimated_hours": 3.0,
            "actual_hours": 2.5
        }
    
    Returns:
        200: Task updated successfully
        403: User doesn't have permission
        404: Task not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Check if user can edit task (member+)
    if not check_task_permission(task, user, 'edit'):
        return jsonify({
            'error': 'You do not have permission to update this task',
            'your_role': get_user_role(user, task.column.board.project),
            'required_role': 'member'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title')
    if title is not None:
        task.title = title
    
    description = data.get('description')
    if description is not None:
        task.description = description
    
    due_date_str = data.get('due_date')
    if due_date_str is not None:
        if due_date_str == '':
            task.due_date = None
        else:
            try:
                task.due_date = datetime.fromisoformat(due_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid due_date format'}), 400
    
    priority = data.get('priority')
    if priority is not None:
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if priority not in valid_priorities:
            return jsonify({'error': f'Priority must be one of: {", ".join(valid_priorities)}'}), 400
        task.priority = priority
    
    labels = data.get('labels')
    if labels is not None:
        task.labels = labels
    
    estimated_hours = data.get('estimated_hours')
    if estimated_hours is not None:
        task.estimated_hours = estimated_hours
    
    actual_hours = data.get('actual_hours')
    if actual_hours is not None:
        task.actual_hours = actual_hours
    
    is_archived = data.get('is_archived')
    if is_archived is not None:
        if is_archived:
            task.archive()
        else:
            task.unarchive()
    
    db.session.commit()
    
    task_dict = task.to_dict(include_assignees=True)
    task_dict['user_role'] = get_user_role(user, task.column.board.project)
    
    return jsonify({
        'message': 'Task updated successfully',
        'task': task_dict
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def archive_task(task_id):
    """
    Archive (soft delete) a task.
    
    SRS Reference:
        FR-3.1: "Delete tasks"
    
    Returns:
        200: Task archived successfully
        403: User doesn't have permission
        404: Task not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Check if user can delete task (member+)
    if not check_task_permission(task, user, 'delete'):
        return jsonify({
            'error': 'You do not have permission to delete this task',
            'your_role': get_user_role(user, task.column.board.project),
            'required_role': 'member'
        }), 403
    
    task.archive()
    db.session.commit()
    
    return jsonify({
        'message': 'Task archived successfully'
    }), 200


@tasks_bp.route('/<int:task_id>/move', methods=['POST'])
@jwt_required()
def move_task(task_id):
    """
    Move a task to a different column.
    
    SRS Reference:
        FR-3.2: "Drag-and-drop reordering of tasks within and across columns"
    
    Request Body:
        {
            "target_column_id": 2,
            "position": 0  # Optional: position in the target column
        }
    
    Returns:
        200: Task moved successfully
        403: User doesn't have permission
        404: Task or target column not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Check if user can edit task (member+)
    if not check_task_permission(task, user, 'edit'):
        return jsonify({
            'error': 'You do not have permission to move this task',
            'your_role': get_user_role(user, task.column.board.project),
            'required_role': 'member'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    target_column_id = data.get('target_column_id')
    if not target_column_id:
        return jsonify({'error': 'target_column_id is required'}), 400
    
    target_column = get_column_or_404(target_column_id, user)
    if not target_column:
        return jsonify({'error': 'Target column not found or access denied'}), 404
    
    # Check if both columns are in the same project
    if task.column.board.project_id != target_column.board.project_id:
        return jsonify({'error': 'Cannot move task to a different project'}), 400
    
    position = data.get('position')
    task.move_to_column(target_column, position)
    db.session.commit()
    
    task_dict = task.to_dict(include_assignees=True)
    task_dict['user_role'] = get_user_role(user, task.column.board.project)
    
    return jsonify({
        'message': 'Task moved successfully',
        'task': task_dict
    }), 200


@tasks_bp.route('/column/<int:column_id>/reorder', methods=['POST'])
@jwt_required()
def reorder_tasks(column_id):
    """
    Reorder tasks within a column.
    
    SRS Reference:
        FR-3.2: "Drag-and-drop reordering of tasks within columns"
    
    Request Body:
        {
            "task_order": [5, 3, 1, 2, 4]  # List of task IDs in desired order
        }
    
    Returns:
        200: Tasks reordered successfully
        403: User doesn't have permission
        404: Column not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    # Check if user can edit tasks (member+)
    if not has_role(user, column.board.project, 'member'):
        return jsonify({
            'error': 'You do not have permission to reorder tasks',
            'your_role': get_user_role(user, column.board.project),
            'required_role': 'member'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    task_order = data.get('task_order')
    if not task_order:
        return jsonify({'error': 'task_order is required'}), 400
    
    column.reorder_tasks(task_order)
    db.session.commit()
    
    return jsonify({
        'message': 'Tasks reordered successfully'
    }), 200


@tasks_bp.route('/<int:task_id>/permissions', methods=['GET'])
@jwt_required()
def get_task_permissions(task_id):
    """
    Get the current user's permissions for a task.
    
    Returns:
        200: Permission summary
        404: Task not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    user_role = get_user_role(user, task.column.board.project)
    
    return jsonify({
        'task_id': task_id,
        'user_role': user_role,
        'permissions': {
            'can_view': check_task_permission(task, user, 'view'),
            'can_edit': check_task_permission(task, user, 'edit'),
            'can_delete': check_task_permission(task, user, 'delete'),
            'can_assign': check_task_permission(task, user, 'assign'),
            'can_move': check_task_permission(task, user, 'edit')
        }
    }), 200
