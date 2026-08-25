"""
Task Assignment API Routes

This module handles task assignment operations:
- Assign users to tasks
- Remove users from tasks
- List assigned users

SRS References:
- FR-3.3: "Assigning a task to one or more project members"
- Section 6.2: task_assignments table schema
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Task, TaskAssignment

# Create blueprint
assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/tasks')


def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_task_or_404(task_id, user):
    """Get a task by ID and check if user has access."""
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return None
    if not task.column.board.project.is_member(user):
        return None
    return task


# ============================================================
# ENDPOINT 1: ASSIGN USER TO TASK
# ============================================================
# POST /api/tasks/<task_id>/assign

@assignments_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_user(task_id):
    """
    Assign a user to a task.
    
    SRS Reference:
        FR-3.3: "Assigning a task to one or more project members"
    
    Request Body:
        {
            "user_id": 2
        }
    
    Returns:
        201: User assigned successfully
        400: User already assigned
        401: User not authenticated
        403: Access denied
        404: Task or user not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task
    task = get_task_or_404(task_id, current_user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Check if user is a member of the project
    if not task.column.board.project.is_member(current_user):
        return jsonify({'error': 'You do not have permission to assign tasks'}), 403
    
    # Step 4: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Step 5: Find the user to assign
    user_to_assign = User.query.get(user_id)
    if not user_to_assign:
        return jsonify({'error': 'User not found'}), 404
    
    # Step 6: Check if the user is a member of the project
    if not task.column.board.project.is_member(user_to_assign):
        return jsonify({'error': 'User is not a member of this project'}), 400
    
    # Step 7: Check if user is already assigned
    if task.is_assigned_to_user(user_to_assign):
        return jsonify({'error': 'User is already assigned to this task'}), 400
    
    # Step 8: Assign the user
    assignment = task.assign_user(
        user=user_to_assign,
        assigned_by=current_user
    )
    db.session.commit()
    
    # Step 9: Return success
    return jsonify({
        'message': 'User assigned successfully',
        'assignment': assignment.to_dict()
    }), 201


# ============================================================
# ENDPOINT 2: REMOVE USER FROM TASK
# ============================================================
# DELETE /api/tasks/<task_id>/assign/<user_id>

@assignments_bp.route('/<int:task_id>/assign/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_assignment(task_id, user_id):
    """
    Remove a user's assignment from a task.
    
    SRS Reference:
        FR-3.3: Task assignment management
    
    Returns:
        200: User unassigned successfully
        401: User not authenticated
        403: Access denied
        404: Task or assignment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task
    task = get_task_or_404(task_id, current_user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Check permission
    if not task.column.board.project.is_member(current_user):
        return jsonify({'error': 'You do not have permission'}), 403
    
    # Step 4: Find the user to unassign
    user_to_remove = User.query.get(user_id)
    if not user_to_remove:
        return jsonify({'error': 'User not found'}), 404
    
    # Step 5: Check if user is assigned
    if not task.is_assigned_to_user(user_to_remove):
        return jsonify({'error': 'User is not assigned to this task'}), 404
    
    # Step 6: Remove assignment
    task.remove_user(user_to_remove)
    db.session.commit()
    
    # Step 7: Return success
    return jsonify({
        'message': 'User unassigned successfully'
    }), 200


# ============================================================
# ENDPOINT 3: LIST ASSIGNED USERS
# ============================================================
# GET /api/tasks/<task_id>/assign

@assignments_bp.route('/<int:task_id>/assign', methods=['GET'])
@jwt_required()
def list_assignments(task_id):
    """
    List all users assigned to a task.
    
    SRS Reference:
        FR-3.3: Task assignment
    
    Returns:
        200: List of assigned users
        401: User not authenticated
        404: Task not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task
    task = get_task_or_404(task_id, current_user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Get all assignees
    assignees = task.get_assignees()
    
    # Step 4: Return list
    return jsonify({
        'assignees': [user.to_dict() for user in assignees],
        'count': len(assignees)
    }), 200


# ============================================================
# ENDPOINT 4: CHECK IF USER IS ASSIGNED
# ============================================================
# GET /api/tasks/<task_id>/assigned/<user_id>

@assignments_bp.route('/<int:task_id>/assigned/<int:user_id>', methods=['GET'])
@jwt_required()
def check_assignment(task_id, user_id):
    """
    Check if a user is assigned to a task.
    
    Returns:
        200: Assignment status
        401: User not authenticated
        404: Task not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task
    task = get_task_or_404(task_id, current_user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Find the user
    user_to_check = User.query.get(user_id)
    if not user_to_check:
        return jsonify({'error': 'User not found'}), 404
    
    # Step 4: Check assignment
    is_assigned = task.is_assigned_to_user(user_to_check)
    
    # Step 5: Return status
    return jsonify({
        'task_id': task_id,
        'user_id': user_id,
        'is_assigned': is_assigned
    }), 200
