"""
Task API Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import db
from app.models import User, Column, Task

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


def get_user_from_token():
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_column_or_404(column_id, user):
    column = Column.query.filter_by(id=column_id, is_archived=False).first()
    if not column:
        return None
    if not column.board.project.is_member(user):
        return None
    return column


@tasks_bp.route('/column/<int:column_id>/tasks', methods=['GET'])
@jwt_required()
def list_tasks(column_id):
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    tasks = column.tasks.filter_by(is_archived=False).all()
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks],
        'count': len(tasks)
    }), 200


@tasks_bp.route('/column/<int:column_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(column_id):
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    if not column.board.project.is_member(user):
        return jsonify({'error': 'You do not have permission to create tasks'}), 403
    
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
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid due_date format'}), 400
    
    last_task = column.tasks.filter_by(is_archived=False).order_by(Task.position.desc()).first()
    position = (last_task.position + 1) if last_task else 0
    
    task = Task(
        column_id=column.id,
        title=title,
        description=description,
        due_date=due_date,
        position=position,
        priority=priority,
        labels=labels
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'message': 'Task created successfully',
        'task': task.to_dict()
    }), 201


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if not task.column.board.project.is_member(user):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if not task.column.board.project.is_member(user):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title')
    if title is not None:
        task.title = title
    
    description = data.get('description')
    if description is not None:
        task.description = description
    
    priority = data.get('priority')
    if priority is not None:
        task.priority = priority
    
    labels = data.get('labels')
    if labels is not None:
        task.labels = labels
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task updated successfully',
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def archive_task(task_id):
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if not task.column.board.project.is_member(user):
        return jsonify({'error': 'Access denied'}), 403
    
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
            "position": 0  # Optional
        }
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if not task.column.board.project.is_member(user):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    target_column_id = data.get('target_column_id')
    if not target_column_id:
        return jsonify({'error': 'target_column_id is required'}), 400
    
    target_column = get_column_or_404(target_column_id, user)
    if not target_column:
        return jsonify({'error': 'Target column not found or access denied'}), 404
    
    if task.column.board.project_id != target_column.board.project_id:
        return jsonify({'error': 'Cannot move task to a different project'}), 400
    
    position = data.get('position')
    task.move_to_column(target_column, position)
    db.session.commit()
    
    return jsonify({
        'message': 'Task moved successfully',
        'task': task.to_dict()
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
            "task_order": [5, 3, 1, 2, 4]
        }
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    if not column.board.project.is_member(user):
        return jsonify({'error': 'You do not have permission to reorder tasks'}), 403
    
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
