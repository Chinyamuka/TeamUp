"""
Comments API Routes with Role-Based Access Control (RBAC)

This module handles comment operations with permission checks.

SRS References:
- FR-3.4: "Support comments and an activity/audit log per task"
- FR-1.3: Role-based access control (Owner, Admin, Member)
- Section 9: Server-side authorization enforcement

Permissions:
- Anyone with project access can view comments
- Members+ can add comments
- Authors can edit/delete their own comments
- Admins+ can delete any comment in their project
"""

import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Task, Comment
from app.models.notification import Notification
from app.utils.permissions import (
    get_user_role,
    has_role,
    can_view_project,
    can_edit_comment,
    can_delete_comment,
    get_user_role_display
)

# Create blueprint
comments_bp = Blueprint('comments', __name__, url_prefix='/api')


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


def get_comment_or_404(comment_id, user):
    """Get a comment by ID and check if user has access."""
    comment = Comment.query.get(comment_id)
    if not comment:
        return None
    
    # Check if user has access to the task's project
    if not comment.task.column.board.project.is_member(user):
        return None
    
    return comment


def extract_mentions(text):
    """Extract @mentioned usernames from text."""
    pattern = r'@(\w+)'
    return re.findall(pattern, text)


# ============================================================
# COMMENT ENDPOINTS WITH RBAC
# ============================================================

@comments_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    """
    Add a comment to a task.
    
    SRS Reference:
        FR-3.4: "Comments on tasks"
        FR-6.2: "Create a notification when a user is @mentioned in a comment"
    
    Request Body:
        {
            "body": "This is my comment",
            "parent_comment_id": null  # Optional: for replies
        }
    
    Returns:
        201: Comment added successfully
        403: User doesn't have permission
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
    
    # Step 3: Check if user can comment (member+)
    if not has_role(current_user, task.column.board.project, 'member'):
        return jsonify({
            'error': 'You do not have permission to comment on this task',
            'your_role': get_user_role(current_user, task.column.board.project),
            'required_role': 'member'
        }), 403
    
    # Step 4: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    body = data.get('body')
    if not body:
        return jsonify({'error': 'Comment body is required'}), 400
    
    parent_comment_id = data.get('parent_comment_id')
    
    # Step 5: If replying, check parent comment exists
    if parent_comment_id:
        parent_comment = Comment.query.get(parent_comment_id)
        if not parent_comment:
            return jsonify({'error': 'Parent comment not found'}), 404
        if parent_comment.task_id != task.id:
            return jsonify({'error': 'Parent comment is on a different task'}), 400
    
    # Step 6: Create the comment
    comment = Comment(
        task_id=task.id,
        author_id=current_user.id,
        body=body,
        parent_comment_id=parent_comment_id
    )
    db.session.add(comment)
    
    # Step 7: Check for @mentions and create notifications (FR-6.2)
    mentions = extract_mentions(body)
    project = task.column.board.project
    members = project.get_members()
    
    for username in mentions:
        mentioned_user = None
        for member in members:
            if member.full_name.lower() == username.lower():
                mentioned_user = member
                break
        
        if mentioned_user and mentioned_user.id != current_user.id:
            notification = Notification.create_mention(
                user=mentioned_user,
                comment=comment,
                mentioned_by=current_user
            )
            db.session.add(notification)
    
    db.session.commit()
    
    # Step 8: Return the created comment
    comment_dict = comment.to_dict(include_replies=True)
    comment_dict['user_role'] = get_user_role(current_user, project)
    
    return jsonify({
        'message': 'Comment added successfully',
        'comment': comment_dict
    }), 201


@comments_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def list_comments(task_id):
    """
    List all comments on a task (top-level only).
    
    SRS Reference:
        FR-3.4: "Comments on tasks"
    
    Returns:
        200: List of comments
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
    
    # Step 4: Get all top-level comments (no parent)
    comments = Comment.query.filter_by(
        task_id=task.id,
        parent_comment_id=None
    ).order_by(Comment.created_at).all()
    
    # Step 5: Return comments with replies
    comments_data = []
    for comment in comments:
        comment_dict = comment.to_dict(include_replies=True)
        comment_dict['user_role'] = get_user_role(current_user, task.column.board.project)
        comments_data.append(comment_dict)
    
    return jsonify({
        'comments': comments_data,
        'count': len(comments_data)
    }), 200


@comments_bp.route('/comments/<int:comment_id>', methods=['GET'])
@jwt_required()
def get_comment(comment_id):
    """
    Get a specific comment with its replies.
    
    Returns:
        200: Comment details
        403: User doesn't have access
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = get_comment_or_404(comment_id, current_user)
    if not comment:
        return jsonify({'error': 'Comment not found or access denied'}), 404
    
    # Step 3: Check if user can view this comment
    if not has_role(current_user, comment.task.column.board.project, 'viewer'):
        return jsonify({'error': 'You do not have access to this comment'}), 403
    
    comment_dict = comment.to_dict(include_replies=True)
    comment_dict['user_role'] = get_user_role(current_user, comment.task.column.board.project)
    
    return jsonify({
        'comment': comment_dict
    }), 200


@comments_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def edit_comment(comment_id):
    """
    Edit a comment.
    
    SRS Reference:
        FR-3.4: Comments can be edited
    
    Request Body:
        {
            "body": "Updated comment text"
        }
    
    Returns:
        200: Comment updated
        403: User doesn't have permission (not author or admin)
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = get_comment_or_404(comment_id, current_user)
    if not comment:
        return jsonify({'error': 'Comment not found or access denied'}), 404
    
    # Step 3: Check if user can edit this comment
    if not can_edit_comment(current_user, comment):
        return jsonify({
            'error': 'You do not have permission to edit this comment',
            'your_role': get_user_role(current_user, comment.task.column.board.project),
            'required_role': 'author or admin'
        }), 403
    
    # Step 4: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    body = data.get('body')
    if not body:
        return jsonify({'error': 'Comment body is required'}), 400
    
    # Step 5: Update the comment
    comment.edit(body)
    db.session.commit()
    
    comment_dict = comment.to_dict(include_replies=True)
    comment_dict['user_role'] = get_user_role(current_user, comment.task.column.board.project)
    
    return jsonify({
        'message': 'Comment updated successfully',
        'comment': comment_dict
    }), 200


@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """
    Delete a comment.
    
    SRS Reference:
        FR-3.4: Comments can be deleted
    
    Permission Rules:
        - Author can delete their own comments
        - Admins+ can delete any comment in their project
    
    Returns:
        200: Comment deleted
        403: User doesn't have permission
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = get_comment_or_404(comment_id, current_user)
    if not comment:
        return jsonify({'error': 'Comment not found or access denied'}), 404
    
    # Step 3: Check if user can delete this comment
    if not can_delete_comment(current_user, comment):
        return jsonify({
            'error': 'You do not have permission to delete this comment',
            'your_role': get_user_role(current_user, comment.task.column.board.project),
            'required_role': 'author or admin'
        }), 403
    
    # Step 4: Delete the comment (and its replies via cascade)
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'Comment deleted successfully'
    }), 200


@comments_bp.route('/comments/<int:comment_id>/permissions', methods=['GET'])
@jwt_required()
def get_comment_permissions(comment_id):
    """
    Get the current user's permissions for a comment.
    
    Returns:
        200: Permission summary
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = get_comment_or_404(comment_id, current_user)
    if not comment:
        return jsonify({'error': 'Comment not found or access denied'}), 404
    
    user_role = get_user_role(current_user, comment.task.column.board.project)
    
    return jsonify({
        'comment_id': comment_id,
        'user_role': user_role,
        'is_author': comment.author_id == current_user.id,
        'permissions': {
            'can_view': has_role(current_user, comment.task.column.board.project, 'viewer'),
            'can_edit': can_edit_comment(current_user, comment),
            'can_delete': can_delete_comment(current_user, comment)
        }
    }), 200
