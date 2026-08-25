"""
Task Assignment API Routes

This module handles task assignment operations:
- Assign users to tasks
- Remove users from tasks
- List assigned users
- Check if user is assigned

SRS References:
- FR-3.3: "Assigning a task to one or more project members"
- FR-6.1: "Create an in-app notification when a user is assigned a task"
- Section 6.2: task_assignments table schema

================================================================================
HOW TASK ASSIGNMENT WORKS:
================================================================================

When a user is assigned to a task, two things happen:
1. A TaskAssignment record is created in the database
2. A Notification is created to alert the user (FR-6.1)

This is a many-to-many relationship:
- A task can have multiple users assigned
- A user can be assigned to multiple tasks

The TaskAssignment table tracks:
- Who was assigned (user_id)
- What task they were assigned to (task_id)
- Who made the assignment (assigned_by_id)
- When it was assigned (assigned_at)
- Whether it's still active (is_active)

================================================================================
WHY WE USE SOFT DELETE (is_active):
================================================================================
- We keep history of all assignments
- We can reactivate assignments if needed
- We can audit who was assigned to what
- We don't lose data when unassigning
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Task, TaskAssignment
from app.models.notification import Notification

# ============================================================
# CREATE BLUEPRINT
# ============================================================
# A blueprint groups related routes together.
# url_prefix='/api/tasks' means all routes start with /api/tasks
# So /api/tasks/1/assign becomes: assign user to task 1
assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/tasks')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """
    Get the current user from JWT token.
    
    ========================================================================
    WHY WE NEED THIS:
    ========================================================================
    - WebSocket connections use @jwt_required decorator
    - This function extracts the user ID from the token
    - We then query the database for the full User object
    
    ========================================================================
    SECURITY:
    ========================================================================
    - Always validate the token
    - Always check the user exists in the database
    - Never trust client-provided user IDs
    
    Returns:
        User object if found, None if not found
    """
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_task_or_404(task_id, user):
    """
    Get a task by ID and check if user has access.
    
    ========================================================================
    WHY WE NEED THIS:
    ========================================================================
    - Users should only see tasks in projects they are members of
    - We need to check permissions before allowing access
    - Security check: user must be a project member
    
    Args:
        task_id: The ID of the task to fetch
        user: The current user (from get_user_from_token)
    
    Returns:
        Task object if found AND user has access, None otherwise
    
    ========================================================================
    HOW IT WORKS:
    ========================================================================
    1. Query the task by ID (only non-archived tasks)
    2. If task doesn't exist, return None
    3. Check if the task's column's board's project is accessible to the user
    4. If not a member, return None
    5. Otherwise, return the task
    
    SRS Reference:
        FR-2.4: "Role-based access control at the project level"
    """
    # Query for the task
    # filter_by(is_archived=False) - only active tasks
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    
    # If task doesn't exist, return None
    if not task:
        return None
    
    # Check if user is a member of the project
    # task.column.board.project gets the project
    # is_member() checks if user is in the project's members
    if not task.column.board.project.is_member(user):
        return None
    
    return task


# ============================================================
# ENDPOINT 1: ASSIGN USER TO TASK
# ============================================================
# POST /api/tasks/<task_id>/assign

@assignments_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()  # This endpoint requires authentication
def assign_user(task_id):
    """
    Assign a user to a task.
    
    SRS References:
        FR-3.3: "Assigning a task to one or more project members"
        FR-6.1: "Create an in-app notification when a user is assigned a task"
    
    ========================================================================
    THE FLOW:
    ========================================================================
    1. Get the current user from the JWT token (the assignor)
    2. Get the task and check access
    3. Check if current user has permission to assign (must be project member)
    4. Get the user to assign from the request body
    5. Validate the user exists and is a project member
    6. Check if user is already assigned (prevent duplicates)
    7. Create the assignment
    8. Create a notification for the assigned user (FR-6.1)
    9. Save everything to the database
    10. Return the assignment details
    
    ========================================================================
    NOTIFICATION CREATION (FR-6.1):
    ========================================================================
    When a user is assigned to a task, we use Notification.create_task_assigned()
    This creates an in-app notification with:
    - Type: "task_assigned"
    - Title: "New task assigned: [task title]"
    - Message: "[assignor] assigned you to task '[task title]'"
    - Payload: {task_id, task_title, assigned_by_id, assigned_by_name}
    - Click action: Link to the task
    - Icon: "📋"
    
    Request Body:
        {
            "user_id": 2  // ID of user to assign
        }
    
    Returns:
        201: User assigned successfully
        400: User already assigned
        401: User not authenticated
        403: Access denied
        404: Task or user not found
    """
    # ============================================================
    # STEP 1: Get the current user (the person making the assignment)
    # ============================================================
    current_user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # ============================================================
    # STEP 2: Get the task and check access
    # ============================================================
    task = get_task_or_404(task_id, current_user)
    
    # If task doesn't exist or user can't access it, return 404
    if not task:
        return jsonify({'error': 'Task not found or access denied'}), 404
    
    # ============================================================
    # STEP 3: Check if current user has permission to assign
    # ============================================================
    # Any project member can assign tasks
    if not task.column.board.project.is_member(current_user):
        return jsonify({'error': 'You do not have permission to assign tasks'}), 403
    
    # ============================================================
    # STEP 4: Get the request data
    # ============================================================
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # ============================================================
    # STEP 5: Find the user to assign
    # ============================================================
    user_to_assign = User.query.get(user_id)
    if not user_to_assign:
        return jsonify({'error': 'User not found'}), 404
    
    # ============================================================
    # STEP 6: Check if the user is a member of the project
    # ============================================================
    # Security check: Can't assign someone who isn't in the project
    if not task.column.board.project.is_member(user_to_assign):
        return jsonify({'error': 'User is not a member of this project'}), 400
    
    # ============================================================
    # STEP 7: Check if user is already assigned
    # ============================================================
    # Prevent duplicate assignments
    if task.is_assigned_to_user(user_to_assign):
        return jsonify({'error': 'User is already assigned to this task'}), 400
    
    # ============================================================
    # STEP 8: Assign the user
    # ============================================================
    # task.assign_user() creates the TaskAssignment record
    # It also sets is_active=True by default
    assignment = task.assign_user(
        user=user_to_assign,
        assigned_by=current_user
    )
    
    # ============================================================
    # STEP 9: Create notification (FR-6.1)
    # ============================================================
    # This is where FR-6.1 is implemented:
    # "Create an in-app notification when a user is assigned a task"
    notification = Notification.create_task_assigned(
        user=user_to_assign,  # Who receives the notification
        task=task,            # What task they were assigned to
        assigned_by=current_user  # Who assigned them
    )
    db.session.add(notification)
    
    # ============================================================
    # STEP 10: Save everything to the database
    # ============================================================
    db.session.commit()
    
    # ============================================================
    # STEP 11: Return success
    # ============================================================
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
    
    ========================================================================
    HOW IT WORKS:
    ========================================================================
    1. Get the current user (the person removing the assignment)
    2. Get the task and check access
    3. Check if current user has permission
    4. Find the user to unassign
    5. Check if user is actually assigned
    6. Remove the assignment (soft delete via is_active=False)
    7. Save to database
    8. Return success
    
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
    
    # Step 6: Remove assignment (soft delete)
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
    
    ========================================================================
    HOW IT WORKS:
    ========================================================================
    1. Get the current user
    2. Get the task and check access
    3. Get all active assignees
    4. Return the list
    
    SRS Reference:
        FR-3.3: Task assignment listing
    
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
    
    ========================================================================
    WHY WE NEED THIS:
    ========================================================================
    - Frontend needs to show if a user is already assigned
    - Avoids duplicate assignments
    - Shows assignment status in UI
    
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
