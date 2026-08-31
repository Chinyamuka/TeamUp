"""
Permissions Utility Module

This module handles all role-based access control checks.
It provides functions to check if a user has permission to perform actions.

SRS References:
- FR-1.3: Role-based access control (Owner, Admin, Member)
- FR-2.4: Only Owners/Admins can remove members or delete boards
- Section 9: Role checks enforced server-side
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User, Project, ProjectMembership


# ============================================================
# ROLE DEFINITIONS
# ============================================================

ROLES = {
    'owner': 4,    # Full control
    'admin': 3,    # Can manage project
    'member': 2,   # Can create/edit tasks
    'viewer': 1    # Read-only
}


def get_user_from_token():
    """Get current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_user_role(user, project):
    """
    Get a user's role in a project.
    
    Returns:
        str: 'owner', 'admin', 'member', 'viewer', or None if not a member
    
    Role hierarchy:
        owner > admin > member > viewer
    """
    if not user or not project:
        return None
    
    # Check if user is the project owner
    if project.owner_id == user.id:
        return 'owner'
    
    # Check project membership
    membership = ProjectMembership.query.filter_by(
        project_id=project.id,
        user_id=user.id
    ).first()
    
    if membership:
        return membership.role
    
    return None


def has_role(user, project, required_role):
    """
    Check if a user has a specific role or higher in a project.
    
    Args:
        user: User object
        project: Project object
        required_role: 'owner', 'admin', 'member', or 'viewer'
    
    Returns:
        bool: True if user has the required role or higher
    
    Example:
        if has_role(user, project, 'admin'):
            # User is admin or owner
    """
    user_role = get_user_role(user, project)
    
    if not user_role:
        return False
    
    return ROLES.get(user_role, 0) >= ROLES.get(required_role, 0)


def require_role(required_role):
    """
    Decorator to require a specific role for an endpoint.
    
    Usage:
        @require_role('admin')
        def delete_board(board_id):
            # Only admins and owners can delete boards
            pass
    
    SRS Reference:
        FR-2.4: "Only Owners/Admins can remove members or delete boards"
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get current user
            user = get_user_from_token()
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            # Get project_id from kwargs or request
            project_id = kwargs.get('project_id')
            if not project_id:
                # Try to get from request body
                data = request.get_json()
                if data:
                    project_id = data.get('project_id')
            
            if not project_id:
                return jsonify({'error': 'Project ID required'}), 400
            
            # Get project
            project = Project.query.get(project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            # Check role
            if not has_role(user, project, required_role):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_role': required_role,
                    'your_role': get_user_role(user, project)
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============================================================
# PERMISSION CHECK FUNCTIONS
# ============================================================

def can_manage_project(user, project):
    """
    Check if user can manage project settings.
    
    Allowed: owner, admin
    Not allowed: member, viewer
    """
    return has_role(user, project, 'admin')


def can_delete_project(user, project):
    """
    Check if user can delete the project.
    
    Allowed: owner only
    Not allowed: admin, member, viewer
    """
    return has_role(user, project, 'owner')


def can_manage_members(user, project):
    """
    Check if user can add/remove members.
    
    SRS Reference:
        FR-2.4: "Only Owners/Admins can remove members"
    
    Allowed: owner, admin
    Not allowed: member, viewer
    """
    return has_role(user, project, 'admin')


def can_manage_boards(user, project):
    """
    Check if user can create/edit/delete boards.
    
    Allowed: owner, admin
    Not allowed: member, viewer
    """
    return has_role(user, project, 'admin')


def can_create_task(user, project):
    """
    Check if user can create tasks.
    
    Allowed: owner, admin, member
    Not allowed: viewer
    """
    return has_role(user, project, 'member')


def can_edit_task(user, project):
    """
    Check if user can edit tasks.
    
    Allowed: owner, admin, member
    Not allowed: viewer
    """
    return has_role(user, project, 'member')


def can_delete_task(user, project):
    """
    Check if user can delete tasks.
    
    Allowed: owner, admin, member
    Not allowed: viewer
    """
    return has_role(user, project, 'member')


def can_view_project(user, project):
    """
    Check if user can view the project.
    
    Allowed: everyone with any role
    Not allowed: no role (not a member)
    """
    return get_user_role(user, project) is not None


def can_add_member(user, project):
    """
    Check if user can add a new member.
    
    SRS Reference:
        FR-2.3: "Inviting members to a project by email"
    
    Allowed: owner, admin
    Not allowed: member, viewer
    """
    return has_role(user, project, 'admin')


def can_remove_member(user, project, target_user):
    """
    Check if user can remove a member.
    
    SRS Reference:
        FR-2.4: "Only Owners/Admins can remove members"
    
    Allowed: owner, admin
    Not allowed: member, viewer
    
    Special: Owner cannot be removed by anyone
    """
    # First check if user has permission to remove members
    if not can_manage_members(user, project):
        return False
    
    # Check if target is the owner
    if project.owner_id == target_user.id:
        return False
    
    return True


def can_change_role(user, project, target_user, new_role):
    """
    Check if user can change a member's role.
    
    Allowed: owner (can change anyone except themselves)
             admin (can change members to admin or member, but not owner)
    Not allowed: member, viewer
    """
    # Only owner and admin can change roles
    if not can_manage_members(user, project):
        return False
    
    # Owner cannot be changed by anyone
    if project.owner_id == target_user.id:
        return False
    
    # If user is admin, they cannot set someone to owner
    if get_user_role(user, project) == 'admin' and new_role == 'owner':
        return False
    
    return True


def can_edit_comment(user, comment):
    """
    Check if user can edit a comment.
    
    Allowed: The author of the comment
    Not allowed: Others (unless admin)
    """
    if user.id == comment.author_id:
        return True
    
    # Admin can edit any comment in their project
    project = comment.task.column.board.project
    return has_role(user, project, 'admin')


def can_delete_comment(user, comment):
    """
    Check if user can delete a comment.
    
    Allowed: The author of the comment, or admin
    """
    if user.id == comment.author_id:
        return True
    
    project = comment.task.column.board.project
    return has_role(user, project, 'admin')


# ============================================================
# UI HELPER FUNCTIONS
# ============================================================

def get_user_role_display(user, project):
    """
    Get a display-friendly role name.
    
    Returns:
        str: 'Owner', 'Admin', 'Member', 'Viewer', or 'Not a member'
    """
    role = get_user_role(user, project)
    
    if not role:
        return 'Not a member'
    
    return role.capitalize()


def get_role_color(user, project):
    """
    Get a color for the role badge.
    
    Returns:
        str: CSS color class
    """
    role = get_user_role(user, project)
    
    colors = {
        'owner': 'bg-amber-urgency text-black',
        'admin': 'bg-logic-blue text-white',
        'member': 'bg-mint-success text-white',
        'viewer': 'bg-text-muted text-white'
    }
    
    return colors.get(role, 'bg-gray-200 text-gray-600')


def can_user_perform_action(user, project, action):
    """
    Check if a user can perform a specific action.
    
    Actions:
        - 'view': Can view project
        - 'create_task': Can create tasks
        - 'edit_task': Can edit tasks
        - 'delete_task': Can delete tasks
        - 'manage_boards': Can manage boards
        - 'manage_members': Can manage members
        - 'manage_project': Can manage project
        - 'delete_project': Can delete project
    """
    action_map = {
        'view': can_view_project,
        'create_task': can_create_task,
        'edit_task': can_edit_task,
        'delete_task': can_delete_task,
        'manage_boards': can_manage_boards,
        'manage_members': can_manage_members,
        'manage_project': can_manage_project,
        'delete_project': can_delete_project
    }
    
    func = action_map.get(action)
    if not func:
        return False
    
    return func(user, project)
