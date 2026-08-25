"""
Project API Routes

This module handles project management endpoints:
- Create, read, update, archive projects
- Add/remove project members
- Role-based access control

SRS References:
- FR-2.1: Project creation, renaming, archival
- FR-2.3: Inviting members to a project
- FR-2.4: Role-based access control (Owner, Admin, Member)
- Section 7.1: REST API endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, Project, ProjectMembership

# Create blueprint
projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    return user


def get_project_or_404(project_id, user):
    """Get a project by ID and check if user has access."""
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    if not project:
        return None
    
    if not project.is_member(user):
        return None
    
    return project


# ============================================================
# ENDPOINTS
# ============================================================

@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    """List all projects for the current user."""
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Get projects where user is owner or member
    owned_projects = Project.query.filter_by(owner_id=user.id, is_archived=False)
    member_project_ids = db.session.query(ProjectMembership.project_id).filter_by(user_id=user.id)
    member_projects = Project.query.filter(
        Project.id.in_(member_project_ids),
        Project.is_archived == False
    )
    
    # Combine and remove duplicates
    project_ids = set()
    all_projects = []
    
    for project in owned_projects.all():
        if project.id not in project_ids:
            project_ids.add(project.id)
            all_projects.append(project)
    
    for project in member_projects.all():
        if project.id not in project_ids:
            project_ids.add(project.id)
            all_projects.append(project)
    
    return jsonify({
        'projects': [project.to_dict(include_owner=True) for project in all_projects],
        'count': len(all_projects)
    }), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project."""
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
    
    # Create project
    project = Project(
        name=name,
        description=description,
        owner_id=user.id
    )
    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        'message': 'Project created successfully',
        'project': project.to_dict(include_owner=True)
    }), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get a specific project by ID."""
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    return jsonify({
        'project': project.to_dict(include_owner=True, include_members=True)
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a project."""
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    if not user.has_permission(project, 'admin'):
        return jsonify({'error': 'You do not have permission to update this project'}), 403
    
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
    
    return jsonify({
        'message': 'Project updated successfully',
        'project': project.to_dict(include_owner=True)
    }), 200


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def archive_project(project_id):
    """Archive (soft delete) a project."""
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    if not user.has_permission(project, 'admin'):
        return jsonify({'error': 'You do not have permission to archive this project'}), 403
    
    project.archive()
    db.session.commit()
    
    return jsonify({
        'message': 'Project archived successfully',
        'project': project.to_dict(include_owner=True)
    }), 200


@projects_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    """Add a member to a project."""
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, current_user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    if not current_user.has_permission(project, 'admin'):
        return jsonify({'error': 'You do not have permission to add members'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    role = data.get('role', 'member')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    if role not in ['member', 'admin']:
        return jsonify({'error': 'Role must be "member" or "admin"'}), 400
    
    user_to_add = User.query.filter_by(email=email).first()
    if not user_to_add:
        return jsonify({'error': 'User not found'}), 404
    
    if project.is_member(user_to_add):
        return jsonify({'error': 'User is already a member of this project'}), 409
    
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
    """Remove a member from a project."""
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, current_user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    if not current_user.has_permission(project, 'admin'):
        return jsonify({'error': 'You do not have permission to remove members'}), 403
    
    user_to_remove = User.query.get(user_id)
    if not user_to_remove:
        return jsonify({'error': 'User not found'}), 404
    
    if project.is_owner(user_to_remove):
        return jsonify({'error': 'Cannot remove the project owner'}), 400
    
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
    """List all members of a project."""
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    project = get_project_or_404(project_id, current_user)
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    members = project.get_members()
    
    return jsonify({
        'members': [member.to_dict() for member in members],
        'count': len(members)
    }), 200
