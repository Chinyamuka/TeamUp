"""
Project API Routes

This module handles project management endpoints with Role-Based Access Control (RBAC).

SRS References:
- FR-2.1: Project creation, renaming, archival
- FR-2.3: Inviting members to a project
- FR-2.4: Only Owners/Admins can remove members or delete boards
- FR-1.3: Role-based access control (Owner, Admin, Member)
- Section 9: Server-side authorization enforcement
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, Project, ProjectMembership
from app.utils.permissions import (
    get_user_role,
    has_role,
    can_view_project,
    can_manage_project,
    can_delete_project,
    can_manage_members,
    can_add_member,
    can_remove_member,
    can_change_role,
    get_user_role_display,
    get_role_color
)

# Create blueprint
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_project_or_404(project_id, user):
    """
    Get a project by ID and check if user has access.
    
    Returns:
        Project: The project object
    
    Raises:
        404: Project not found or user doesn't have access
    """
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return None
    
    # Check if user has access (owner or member)
    if not project.is_member(user):
        return None
    
    return project


# ============================================================
# ENDPOINTS WITH RBAC
# ============================================================

@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    """
    List all projects for the current user.
    
    SRS Reference:
        FR-2.1: "System shall allow creation, renaming, and archival of projects"
        Section 7.1: GET /api/projects
    
    Returns:
        200: List of projects
        401: Not authenticated
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Get projects where user is owner or member
    owned_projects = Project.query.filter_by(
        owner_id=user.id,
        is_archived=False
    ).all()
    
    member_project_ids = db.session.query(ProjectMembership.project_id).filter_by(
        user_id=user.id
    )
    member_projects = Project.query.filter(
        Project.id.in_(member_project_ids),
        Project.is_archived == False
    ).all()
    
    # Combine and remove duplicates
    project_ids = set()
    all_projects = []
    
    for project in owned_projects:
        if project.id not in project_ids:
            project_ids.add(project.id)
            all_projects.append(project)
    
    for project in member_projects:
        if project.id not in project_ids:
            project_ids.add(project.id)
            all_projects.append(project)
    
    # Add role information to each project
    projects_data = []
    for project in all_projects:
        project_dict = project.to_dict(include_owner=True)
        project_dict['user_role'] = get_user_role(user, project)
        projects_data.append(project_dict)
    
    return jsonify({
        'projects': projects_data,
        'count': len(projects_data)
    }), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """
    Create a new project.
    
    SRS Reference:
        FR-2.1: "System shall allow creation, renaming, and archival of projects"
        Section 7.1: POST /api/projects
    
    Returns:
        201: Project created
        400: Validation error
        401: Not authenticated
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    
    # Create project with user as owner
    project = Project(
        name=name,
        description=description,
        owner_id=user.id
    )
    db.session.add(project)
    db.session.flush()  # Get project ID
    
    # Add owner as a member with 'owner' role
    membership = ProjectMembership(
        project_id=project.id,
        user_id=user.id,
        role='owner'
    )
    db.session.add(membership)
    
    # Create default board with columns
    from app.models import Board, Column
    
    board = Board(
        project_id=project.id,
        name='Default Board',
        position=0
    )
    db.session.add(board)
    db.session.flush()
    
    default_columns = [
        Column(name='To Do', position=0, board_id=board.id),
        Column(name='In Progress', position=1, board_id=board.id),
        Column(name='Done', position=2, board_id=board.id)
    ]
    
    for column in default_columns:
        db.session.add(column)
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Failed to create project'}), 500
    
    project_dict = project.to_dict(include_owner=True)
    project_dict['user_role'] = 'owner'
    
    return jsonify({
        'message': 'Project created successfully',
        'project': project_dict
    }), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """
    Get a specific project by ID.
    
    SRS Reference:
        Section 7.1: GET /api/projects/:id
        FR-1.3: Role-based access control
    
    Returns:
        200: Project details
        403: User doesn't have access
        404: Project not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Check if user can view this project (FR-1.3)
    if not can_view_project(user, project):
        return jsonify({'error': 'You do not have access to this project'}), 403
    
    project_dict = project.to_dict(include_owner=True, include_members=True)
    project_dict['user_role'] = get_user_role(user, project)
    
    return jsonify({
        'project': project_dict
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """
    Update a project.
    
    SRS Reference:
        FR-2.1: "System shall allow creation, renaming, and archival of projects"
        FR-2.4: Only Owners/Admins can remove members or delete boards
    
    Returns:
        200: Project updated
        403: User doesn't have permission
        404: Project not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Check if user can manage project (FR-2.4)
    if not can_manage_project(user, project):
        return jsonify({
            'error': 'You do not have permission to update this project',
            'your_role': get_user_role(user, project),
            'required_role': 'admin'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    description = data.get('description')
    is_archived = data.get('is_archived')
    
    if name is not None:
        project.name = name
    
    if description is not None:
        project.description = description
    
    if is_archived is not None:
        if is_archived:
            project.archive()
        else:
            project.unarchive()
    
    db.session.commit()
    
    project_dict = project.to_dict(include_owner=True)
    project_dict['user_role'] = get_user_role(user, project)
    
    return jsonify({
        'message': 'Project updated successfully',
        'project': project_dict
    }), 200


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def archive_project(project_id):
    """
    Archive (soft delete) a project.
    
    SRS Reference:
        FR-2.1: "System shall allow creation, renaming, and archival of projects"
        FR-2.4: Only Owners/Admins can remove members or delete boards
    
    Returns:
        200: Project archived
        403: User doesn't have permission (only owner)
        404: Project not found
    """
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Check if user can delete project (owner only - FR-2.4)
    if not can_delete_project(user, project):
        return jsonify({
            'error': 'Only the project owner can delete this project',
            'your_role': get_user_role(user, project),
            'required_role': 'owner'
        }), 403
    
    project.archive()
    db.session.commit()
    
    return jsonify({
        'message': 'Project archived successfully'
    }), 200


@projects_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    """
    Add a member to a project.
    
    SRS Reference:
        FR-2.3: "System shall allow inviting members to a project by email"
        FR-2.4: Only Owners/Admins can remove members or delete boards
    
    Request Body:
        {
            "email": "user@example.com",
            "role": "member"  # or "admin"
        }
    
    Returns:
        201: Member added
        403: User doesn't have permission
        404: Project or user not found
        409: User is already a member
    """
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Check if user can add members (FR-2.4)
    if not can_add_member(current_user, project):
        return jsonify({
            'error': 'You do not have permission to add members',
            'your_role': get_user_role(current_user, project),
            'required_role': 'admin'
        }), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    role = data.get('role', 'member')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    if role not in ['member', 'admin', 'viewer']:
        return jsonify({'error': 'Role must be "member", "admin", or "viewer"'}), 400
    
    # Find user by email
    user_to_add = User.query.filter_by(email=email).first()
    if not user_to_add:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is already a member
    if project.is_member(user_to_add):
        return jsonify({'error': 'User is already a member of this project'}), 409
    
    # Add user to project
    membership = project.add_member(
        user=user_to_add,
        role=role,
        invited_by=current_user
    )
    
    db.session.commit()
    
    return jsonify({
        'message': 'Member added successfully',
        'membership': membership.to_dict()
    }), 201


@projects_bp.route('/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, user_id):
    """
    Remove a member from a project.
    
    SRS Reference:
        FR-2.4: "Only Owners/Admins can remove members or delete boards"
    
    Returns:
        200: Member removed
        403: User doesn't have permission
        404: Project or member not found
        400: Cannot remove owner
    """
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    user_to_remove = User.query.get(user_id)
    if not user_to_remove:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user can remove members (FR-2.4)
    if not can_remove_member(current_user, project, user_to_remove):
        return jsonify({
            'error': 'You do not have permission to remove this user',
            'your_role': get_user_role(current_user, project),
            'required_role': 'admin'
        }), 403
    
    # Check if user is the owner (cannot remove owner)
    if project.is_owner(user_to_remove):
        return jsonify({'error': 'Cannot remove the project owner'}), 400
    
    # Check if user is a member
    if not project.is_member(user_to_remove):
        return jsonify({'error': 'User is not a member of this project'}), 404
    
    project.remove_member(user_to_remove)
    db.session.commit()
    
    return jsonify({
        'message': 'Member removed successfully'
    }), 200


@projects_bp.route('/<int:project_id>/members', methods=['GET'])
@jwt_required()
def list_members(project_id):
    """
    List all members of a project with their roles.
    
    Returns:
        200: List of members with roles
        403: User doesn't have access
        404: Project not found
    """
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Check if user can view this project
    if not can_view_project(current_user, project):
        return jsonify({'error': 'You do not have access to this project'}), 403
    
    # Get all members with their roles
    members = project.get_members()
    members_data = []
    
    for member in members:
        member_dict = member.to_dict()
        member_dict['role'] = get_user_role(member, project)
        members_data.append(member_dict)
    
    return jsonify({
        'members': members_data,
        'count': len(members_data),
        'your_role': get_user_role(current_user, project)
    }), 200


@projects_bp.route('/<int:project_id>/members/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def change_member_role(project_id, user_id):
    """
    Change a member's role in a project.
    
    SRS Reference:
        FR-1.3: Role-based access control (Owner, Admin, Member)
        FR-2.4: Only Owners/Admins can remove members or delete boards
    
    Request Body:
        {
            "role": "admin"  # or "member" or "viewer"
        }
    
    Returns:
        200: Role updated
        403: User doesn't have permission
        404: Project or user not found
    """
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    new_role = data.get('role')
    if not new_role:
        return jsonify({'error': 'Role is required'}), 400
    
    if new_role not in ['member', 'admin', 'viewer']:
        return jsonify({'error': 'Role must be "member", "admin", or "viewer"'}), 400
    
    # Check if user can change roles (FR-2.4)
    if not can_change_role(current_user, project, target_user, new_role):
        return jsonify({
            'error': 'You do not have permission to change this user\'s role',
            'your_role': get_user_role(current_user, project),
            'target_role': get_user_role(target_user, project),
            'required_role': 'admin'
        }), 403
    
    # Update the role
    membership = ProjectMembership.query.filter_by(
        project_id=project.id,
        user_id=target_user.id
    ).first()
    
    if not membership:
        return jsonify({'error': 'User is not a member of this project'}), 404
    
    membership.role = new_role
    db.session.commit()
    
    return jsonify({
        'message': 'Role updated successfully',
        'user': target_user.to_dict(),
        'new_role': new_role
    }), 200
