"""
Task API Routes

This module handles all task-related operations in the TeamUp application.
A task is the atomic unit of work - a sticky note on a Kanban board.

SRS References:
- FR-3.1: Task CRUD with title, description, labels, due date
- FR-3.2: Drag-and-drop reordering within and across columns
- FR-3.3: Assigning a task to one or more project members
- Section 6.2: tasks table schema
- Section 7.1: REST API endpoints

Endpoints:
    GET    /api/columns/<column_id>/tasks     - List tasks in a column
    POST   /api/columns/<column_id>/tasks     - Create a new task
    GET    /api/tasks/<task_id>               - Get task details
    PUT    /api/tasks/<task_id>               - Update a task
    DELETE /api/tasks/<task_id>               - Archive a task
    POST   /api/tasks/<task_id>/move          - Move task to another column
    POST   /api/tasks/<task_id>/reorder       - Reorder tasks within a column
"""

# ============================================================
# IMPORTS
# ============================================================
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import db
from app.models import User, Project, Board, Column, Task

# ============================================================
# CREATE BLUEPRINT
# ============================================================
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """
    Get the current user from the JWT token.
    
    Returns:
        User object if found, None if not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user


def get_column_or_404(column_id, user):
    """
    Get a column by ID and check if the user has access.
    
    Args:
        column_id: The ID of the column to fetch
        user: The current user
    
    Returns:
        Column object if found AND user has access, None otherwise
    
    How it works:
        1. Query the column by ID
        2. Check if the column's board is accessible to the user
        3. If not, return None
        4. Otherwise, return the column
    """
    column = Column.query.filter_by(
        id=column_id,
        is_archived=False
    ).first()
    
    if not column:
        return None
    
    # Check if user has access to the board's project
    if not column.board.project.is_member(user):
        return None
    
    return column


def get_task_or_404(task_id, user):
    """
    Get a task by ID and check if the user has access.
    
    Args:
        task_id: The ID of the task to fetch
        user: The current user
    
    Returns:
        Task object if found AND user has access, None otherwise
    """
    task = Task.query.filter_by(
        id=task_id,
        is_archived=False
    ).first()
    
    if not task:
        return None
    
    # Check if user has access to the column's board's project
    if not task.column.board.project.is_member(user):
        return None
    
    return task


# ============================================================
# ENDPOINT 1: LIST TASKS IN A COLUMN
# ============================================================
# GET /api/columns/<column_id>/tasks
# Lists all tasks in a specific column

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
        401: User not authenticated
        404: Column not found or access denied
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the column and check access
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    # Step 3: Check if we should include archived tasks
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    
    # Step 4: Get tasks
    if include_archived:
        tasks = column.tasks.all()
    else:
        tasks = column.tasks.filter_by(is_archived=False).all()
    
    # Step 5: Return tasks
    return jsonify({
        'tasks': [task.to_dict(include_assignees=True) for task in tasks],
        'count': len(tasks)
    }), 200


# ============================================================
# ENDPOINT 2: CREATE TASK
# ============================================================
# POST /api/columns/<column_id>/tasks
# Creates a new task in a column

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
        400: Invalid request data
        401: User not authenticated
        404: Column not found or access denied
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the column and check access
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    # Step 3: Check if user is a member of the project
    if not column.board.project.is_member(user):
        return jsonify({'error': 'You do not have permission to create tasks'}), 403
    
    # Step 4: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Step 5: Validate required fields
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Task title is required'}), 400
    
    # Step 6: Get optional fields
    description = data.get('description', '')
    due_date_str = data.get('due_date')
    priority = data.get('priority', 'medium')
    labels = data.get('labels', [])
    estimated_hours = data.get('estimated_hours')
    
    # Step 7: Parse due_date if provided
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    
    # Step 8: Validate priority
    valid_priorities = ['low', 'medium', 'high', 'critical']
    if priority not in valid_priorities:
        return jsonify({'error': f'Priority must be one of: {", ".join(valid_priorities)}'}), 400
    
    # Step 9: Get position (add to the end)
    last_task = column.tasks.filter_by(is_archived=False).order_by(Task.position.desc()).first()
    position = (last_task.position + 1) if last_task else 0
    
    # Step 10: Create task
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
    
    # Step 11: Return created task
    return jsonify({
        'message': 'Task created successfully',
        'task': task.to_dict(include_assignees=True)
    }), 201


# ============================================================
# ENDPOINT 3: GET TASK
# ============================================================
# GET /api/tasks/<task_id>
# Gets a specific task with all details

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """
    Get a specific task by ID.
    
    SRS Reference:
        Section 7.1: GET /api/tasks/:id
    
    Returns:
        200: Task details with assignees and comments
        401: User not authenticated
        404: Task not found or access denied
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task and check access
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Return task with assignees and comments
    return jsonify({
        'task': task.to_dict(include_assignees=True, include_comments=True)
    }), 200


# ============================================================
# ENDPOINT 4: UPDATE TASK
# ============================================================
# PUT /api/tasks/<task_id>
# Updates a task's properties

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
        400: Invalid request data
        401: User not authenticated
        403: User doesn't have permission
        404: Task not found
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task and check access
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Check if user is a member of the project
    if not task.column.board.project.is_member(user):
        return jsonify({'error': 'You do not have permission to update this task'}), 403
    
    # Step 4: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Step 5: Update fields that were provided
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
    
    # Step 6: Save changes
    db.session.commit()
    
    # Step 7: Return updated task
    return jsonify({
        'message': 'Task updated successfully',
        'task': task.to_dict(include_assignees=True)
    }), 200


# ============================================================
# ENDPOINT 5: ARCHIVE TASK
# ============================================================
# DELETE /api/tasks/<task_id>
# Archives (soft deletes) a task

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def archive_task(task_id):
    """
    Archive (soft delete) a task.
    
    SRS Reference:
        FR-3.1: "Delete tasks"
    
    Returns:
        200: Task archived successfully
        401: User not authenticated
        403: User doesn't have permission
        404: Task not found
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task and check access
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Check if user is a member of the project
    if not task.column.board.project.is_member(user):
        return jsonify({'error': 'You do not have permission to delete this task'}), 403
    
    # Step 4: Archive the task
    task.archive()
    db.session.commit()
    
    # Step 5: Return success
    return jsonify({
        'message': 'Task archived successfully'
    }), 200


# ============================================================
# ENDPOINT 6: MOVE TASK TO ANOTHER COLUMN (FR-3.2)
# ============================================================
# POST /api/tasks/<task_id>/move
# Moves a task to a different column

@tasks_bp.route('/<int:task_id>/move', methods=['POST'])
@jwt_required()
def move_task(task_id):
    """
    Move a task to a different column.
    
    SRS Reference:
        FR-3.2: "Drag-and-drop reordering within and across columns"
    
    Request Body:
        {
            "target_column_id": 2,
            "position": 0  # Optional: position in the target column
        }
    
    Returns:
        200: Task moved successfully
        400: Invalid request data
        401: User not authenticated
        403: User doesn't have permission
        404: Task or target column not found
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task and check access
    task = get_task_or_404(task_id, user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    target_column_id = data.get('target_column_id')
    if not target_column_id:
        return jsonify({'error': 'target_column_id is required'}), 400
    
    # Step 4: Get the target column and check access
    target_column = get_column_or_404(target_column_id, user)
    if not target_column:
        return jsonify({'error': 'Target column not found or access denied'}), 404
    
    # Step 5: Check if both columns are in the same project
    if task.column.board.project_id != target_column.board.project_id:
        return jsonify({'error': 'Cannot move task to a different project'}), 400
    
    # Step 6: Move the task
    position = data.get('position')
    task.move_to_column(target_column, position)
    db.session.commit()
    
    # Step 7: Return success
    return jsonify({
        'message': 'Task moved successfully',
        'task': task.to_dict(include_assignees=True)
    }), 200


# ============================================================
# ENDPOINT 7: REORDER TASKS WITHIN A COLUMN (FR-3.2)
# ============================================================
# POST /api/columns/<column_id>/reorder
# Reorders tasks within a column

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
        400: Invalid request data
        401: User not authenticated
        403: User doesn't have permission
        404: Column not found
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the column and check access
    column = get_column_or_404(column_id, user)
    if not column:
        return jsonify({'error': 'Column not found or access denied'}), 404
    
    # Step 3: Check if user is a member of the project
    if not column.board.project.is_member(user):
        return jsonify({'error': 'You do not have permission to reorder tasks'}), 403
    
    # Step 4: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    task_order = data.get('task_order')
    if not task_order:
        return jsonify({'error': 'task_order is required'}), 400
    
    # Step 5: Reorder tasks
    column.reorder_tasks(task_order)
    db.session.commit()
    
    # Step 6: Return success
    return jsonify({
        'message': 'Tasks reordered successfully'
    }), 200
