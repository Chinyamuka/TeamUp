"""
Comments API Routes

This module handles comment operations on tasks:
- Add comments to tasks
- Reply to comments (threaded discussions)
- Edit comments
- Delete comments
- List comments on a task

SRS References:
- FR-3.4: "Support comments and an activity/audit log per task"
- FR-6.2: "Create a notification when a user is @mentioned in a comment"
- Section 6.2: comments table schema
- Section 6.1: Task (1) --- (M) Comment

================================================================================
HOW COMMENTS WORK:
================================================================================

Comments are threaded, meaning they can have replies:

    Task: "Fix login bug"
    │
    ├── Comment 1: "Let's discuss this approach"
    │   │
    │   ├── Reply 1.1: "I agree, let's do it"
    │   │
    │   └── Reply 1.2: "Has anyone tested this?"
    │
    └── Comment 2: "I've updated the PR"

Threading is achieved using parent_comment_id:
- parent_comment_id = NULL → Top-level comment
- parent_comment_id = 1 → Reply to comment 1

================================================================================
@MENTIONS (FR-6.2):
================================================================================
When a user types @username in a comment:
1. We extract all @mentions using regex
2. We check if the mentioned user is a project member
3. If found and not the author, we create a notification
4. The mentioned user receives an in-app alert

Example:
    Comment: "Hey @Don, can you review this?"
    → Don receives a notification: "You were mentioned by John"
"""

import re  # Regular expressions for finding @mentions
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Task, Comment
from app.models.notification import Notification

# ============================================================
# CREATE BLUEPRINT
# ============================================================
# url_prefix='/api' means routes are under /api
# So /api/tasks/1/comments becomes: comments on task 1
# And /api/comments/1 becomes: get comment 1
comments_bp = Blueprint('comments', __name__, url_prefix='/api')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def get_task_or_404(task_id, user):
    """
    Get a task by ID and check if user has access.
    
    ========================================================================
    SECURITY:
    ========================================================================
    - Users can only comment on tasks in projects they're members of
    - This function checks both existence and access
    
    Args:
        task_id: Task ID
        user: Current user
    
    Returns:
        Task object if found and accessible, None otherwise
    """
    task = Task.query.filter_by(id=task_id, is_archived=False).first()
    if not task:
        return None
    if not task.column.board.project.is_member(user):
        return None
    return task


# ============================================================
# ENDPOINT 1: ADD COMMENT TO TASK
# ============================================================
# POST /api/tasks/<task_id>/comments

@comments_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    """
    Add a comment to a task.
    
    SRS References:
        FR-3.4: "Comments on tasks"
        FR-6.2: "Create a notification when a user is @mentioned in a comment"
    
    ========================================================================
    THE FLOW:
    ========================================================================
    1. Get the current user
    2. Get the task and check access
    3. Check if user is a project member
    4. Get request data (body, parent_comment_id)
    5. If replying, check parent comment exists
    6. Create the comment
    7. Check for @mentions in the comment body (FR-6.2)
    8. Create notifications for each mentioned user
    9. Save everything
    10. Return the created comment
    
    ========================================================================
    @MENTION DETECTION (FR-6.2):
    ========================================================================
    Pattern: @username
    Example: "Hey @Don, can you help?"
    → Extracts ['Don']
    
    For each mention:
    1. Check if the user exists in the project
    2. If found and not the author, create notification
    3. Notification includes the comment context
    
    Request Body:
        {
            "body": "This is my comment",
            "parent_comment_id": null  # Optional: for replies
        }
    
    Returns:
        201: Comment added successfully
        400: Invalid request
        401: User not authenticated
        403: Access denied
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
    
    # Step 3: Check if user is a member of the project
    if not task.column.board.project.is_member(current_user):
        return jsonify({'error': 'You do not have permission to comment'}), 403
    
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
    
    # ============================================================
    # STEP 7: Check for @mentions (FR-6.2)
    # ============================================================
    # Find all @mentions in the comment body
    # Pattern: @ followed by word characters (letters, numbers, underscore)
    # Example: @Don, @Sarah, @John_Doe
    mention_pattern = r'@(\w+)'
    mentions = re.findall(mention_pattern, body)
    
    # Get all project members (to validate mentioned users)
    project = task.column.board.project
    members = project.get_members()
    
    # ============================================================
    # STEP 8: Create notifications for each mention
    # ============================================================
    for username in mentions:
        # Find the user by full_name (simple matching)
        # Note: In production, you'd want a dedicated username field
        mentioned_user = None
        for member in members:
            if member.full_name.lower() == username.lower():
                mentioned_user = member
                break
        
        # If found and not the author, create notification
        if mentioned_user and mentioned_user.id != current_user.id:
            # Notification.create_mention() creates a notification
            # with type "task_mention"
            notification = Notification.create_mention(
                user=mentioned_user,      # Who receives the notification
                comment=comment,          # The comment they were mentioned in
                mentioned_by=current_user # Who mentioned them
            )
            db.session.add(notification)
    
    # ============================================================
    # STEP 9: Save everything to the database
    # ============================================================
    db.session.commit()
    
    # ============================================================
    # STEP 10: Return the created comment
    # ============================================================
    return jsonify({
        'message': 'Comment added successfully',
        'comment': comment.to_dict(include_replies=True)
    }), 201


# ============================================================
# ENDPOINT 2: LIST COMMENTS ON A TASK
# ============================================================
# GET /api/tasks/<task_id>/comments

@comments_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def list_comments(task_id):
    """
    List all comments on a task (top-level only).
    
    ========================================================================
    WHY TOP-LEVEL ONLY:
    ========================================================================
    - We return only top-level comments (parent_comment_id = NULL)
    - Each comment includes its replies via to_dict(include_replies=True)
    - This creates a nested structure: comments with replies inside
    
    Returns:
        200: List of comments
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
    
    # Step 3: Get all top-level comments (no parent)
    comments = Comment.query.filter_by(
        task_id=task.id,
        parent_comment_id=None
    ).order_by(Comment.created_at).all()
    
    # Step 4: Return comments with replies
    return jsonify({
        'comments': [comment.to_dict(include_replies=True) for comment in comments],
        'count': len(comments)
    }), 200


# ============================================================
# ENDPOINT 3: GET A SPECIFIC COMMENT
# ============================================================
# GET /api/comments/<comment_id>

@comments_bp.route('/comments/<int:comment_id>', methods=['GET'])
@jwt_required()
def get_comment(comment_id):
    """
    Get a specific comment with its replies.
    
    Returns:
        200: Comment details
        401: User not authenticated
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Step 3: Check access
    if not comment.task.column.board.project.is_member(current_user):
        return jsonify({'error': 'Access denied'}), 403
    
    # Step 4: Return comment with replies
    return jsonify({
        'comment': comment.to_dict(include_replies=True)
    }), 200


# ============================================================
# ENDPOINT 4: EDIT A COMMENT
# ============================================================
# PUT /api/comments/<comment_id>

@comments_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def edit_comment(comment_id):
    """
    Edit a comment.
    
    ========================================================================
    EDIT TRACKING:
    ========================================================================
    When a comment is edited:
    - is_edited = True
    - edited_at = current timestamp
    - body = new body
    - updated_at = current timestamp
    
    This provides an audit trail of changes.
    
    Returns:
        200: Comment updated
        401: User not authenticated
        403: Not the author
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Step 3: Check access
    if not comment.task.column.board.project.is_member(current_user):
        return jsonify({'error': 'Access denied'}), 403
    
    # Step 4: Check if user is the author
    if comment.author_id != current_user.id:
        return jsonify({'error': 'You can only edit your own comments'}), 403
    
    # Step 5: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    body = data.get('body')
    if not body:
        return jsonify({'error': 'Comment body is required'}), 400
    
    # Step 6: Update the comment (sets is_edited=True, edited_at=now)
    comment.edit(body)
    db.session.commit()
    
    # Step 7: Return updated comment
    return jsonify({
        'message': 'Comment updated successfully',
        'comment': comment.to_dict(include_replies=True)
    }), 200


# ============================================================
# ENDPOINT 5: DELETE A COMMENT
# ============================================================
# DELETE /api/comments/<comment_id>

@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """
    Delete a comment.
    
    ========================================================================
    CASCADE DELETE:
    ========================================================================
    When a comment is deleted, all its replies are also deleted.
    This is configured in the model with cascade='all, delete-orphan'.
    
    ========================================================================
    PERMISSIONS:
    ========================================================================
    - Author can delete their own comments
    - Project admins can delete any comment in the project
    - This prevents spam and inappropriate content
    
    Returns:
        200: Comment deleted
        401: User not authenticated
        403: Not the author or admin
        404: Comment not found
    """
    # Step 1: Get the current user
    current_user = get_user_from_token()
    if not current_user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the comment
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Step 3: Check access
    if not comment.task.column.board.project.is_member(current_user):
        return jsonify({'error': 'Access denied'}), 403
    
    # Step 4: Check if user is the author or a project admin
    project = comment.task.column.board.project
    
    if comment.author_id != current_user.id:
        # Check if user is a project admin
        if not current_user.has_permission(project, 'admin'):
            return jsonify({'error': 'You can only delete your own comments'}), 403
    
    # Step 5: Delete the comment (and its replies via cascade)
    db.session.delete(comment)
    db.session.commit()
    
    # Step 6: Return success
    return jsonify({
        'message': 'Comment deleted successfully'
    }), 200
