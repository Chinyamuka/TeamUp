"""
Task Assignment API Routes with Role-Based Access Control (RBAC)

This module handles task assignment operations with permission checks.

SRS References:
- FR-3.3: "Assigning a task to one or more project members"
- FR-6.1: "Create an in-app notification when a user is assigned a task"
- FR-1.3: Role-based access control (Owner, Admin, Member)
- Section 9: Server-side authorization enforcement
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Task, TaskAssignment
from app.models.notification import Notification
from app.utils.permissions import (
    get_user_role,
    has_role,
    get_user_role_display
)

# Create blueprint
assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/tasks')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

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


def can_assign_task(task, user):
    """
    Check if user can assign users to a task.
    
    Allowed: member+ in the project
    """
    return has_role(user, task.column.board.project, 'member')


def can_unassign_task(task, user):
    """
    Check if user can unassign users from a task.
    
    Allowed: member+ in the project
    """
    return has_role(user, task.column.board.project, 'member')


# ============================================================
# TASK ASSIGNMENT ENDPOINTS WITH RBAC
# ============================================================

@assignments_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_user(task_id):
    """
    Assign a user to a task.
    
    SRS References:
        FR-3.3: "Assigning a task to one or more project members"
        FR-6.1: "Create an in-app notification when a user is assigned a task"
    
    Request Body:
        {
            "user_id": 2
        }
    
    Returns:
        201: User assigned successfully
        403: User doesn't have permission
        404: Task or user not found
        409: User already assigned
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the task
    task = get_task_or_404(task_id, current_user)
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # Step 3: Check if user can assign tasks (member+)
    if not can_assign_task(task, current_user):
        return jsonify({
            'error': 'You do not have permission to assign users to this task',
            'your_role': get_user_role(current_user, task.column.board.project),
            'required_role': 'member'
        }), 403
    
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
    
    # Step 6: Check if user is a member of the project
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
    
    # Step 9: Create notification (FR-6.1)
    notification = Notification.create_task_assigned(
        user=user_to_assign,
        task=task,
        assigned_by=current_user
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'message': 'User assigned successfully',
        'assignment': assignment.to_dict()
    }), 201


@assignments_bp.route('/<int:task_id>/assign/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_assignment(task_id, user_id):
    """
    Remove a user's assignment from a task.
    
    SRS Reference:
        FR-3.3: Task assignment management
    
    Returns:
        200: User unassigned successfully
        403: User doesn't have permission
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
    
    # Step 3: Check if user can unassign (member+)
    if not can_unassign_task(task, current_user):
        return jsonify({
            'error': 'You do not have permission to remove assignments from this task',
            'your_role': get_user_role(current_user, task.column.board.project),
            'required_role': 'member'
        }), 403
    
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
    
    return jsonify({
        'message': 'User unassigned successfully'
    }), 200


@assignments_bp.route('/<int:task_id>/assign', methods=['GET'])
@jwt_required()
def list_assignments(task_id):
    """
    List all users assigned to a task.
    
    SRS Reference:
        FR-3.3: Task assignment listing
    
    Returns:
        200: List of assigned users
        403: User doesn't have access
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
    
    # Step 3: Check if user can view this task
    if not has_role(current_user, task.column.board.project, 'viewer'):
        return jsonify({'error': 'You do not have access to this task'}), 403
    
    # Step 4: Get all assignees
    assignees = task.get_assignees()
    
    assignees_data = []
    for assignee in assignees:
        assignee_dict = assignee.to_dict()
        assignee_dict['role'] = get_user_role(assignee, task.column.board.project)
        assignees_data.append(assignee_dict)
    
    return jsonify({
        'assignees': assignees_data,
        'count': len(assignees_data)
    }), 200


@assignments_bp.route('/<int:task_id>/assigned/<int:user_id>', methods=['GET'])
@jwt_required()
def check_assignment(task_id, user_id):
    """
    Check if a user is assigned to a task.
    
    Returns:
        200: Assignment status
        403: User doesn't have access
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
    
    # Step 3: Check if user can view this task
    if not has_role(current_user, task.column.board.project, 'viewer'):
        return jsonify({'error': 'You do not have access to this task'}), 403
    
    # Step 4: Find the user
    user_to_check = User.query.get(user_id)
    if not user_to_check:
        return jsonify({'error': 'User not found'}), 404
    
    # Step 5: Check assignment
    is_assigned = task.is_assigned_to_user(user_to_check)
    
    return jsonify({
        'task_id': task_id,
        'user_id': user_id,
        'is_assigned': is_assigned,
        'user_role': get_user_role(user_to_check, task.column.board.project)
    }), 200


@assignments_bp.route('/<int:task_id>/assign/permissions', methods=['GET'])
@jwt_required()
def get_assignment_permissions(task_id):
    """
    Get the current user's permissions for task assignments.
    
    Returns:
        200: Permission summary
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
    
    user_role = get_user_role(current_user, task.column.board.project)
    
    return jsonify({
        'task_id': task_id,
        'user_role': user_role,
        'permissions': {
            'can_assign': can_assign_task(task, current_user),
            'can_unassign': can_unassign_task(task, current_user),
            'can_view_assignments': has_role(current_user, task.column.board.project, 'viewer')
        }
    }), 200
