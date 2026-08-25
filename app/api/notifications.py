"""
Notifications API Routes

This module handles in-app notification management:
- List user's notifications
- Mark as read individually or in bulk
- Get unread count
- Delete notifications

SRS References:
- FR-6.1: In-app notification when user is assigned a task
- FR-6.2: Notification when user is @mentioned in a comment
- FR-6.4: Mark notifications as read individually or in bulk
- Section 6.2: notifications table schema
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Notification

# Create blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


def get_user_from_token():
    """Get the current user from JWT token."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


# ============================================================
# ENDPOINT 1: LIST NOTIFICATIONS
# ============================================================
# GET /api/notifications

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def list_notifications():
    """
    List all notifications for the current user.
    
    SRS Reference:
        FR-6.4: List notifications
    
    Query Parameters:
        limit: Number of notifications per page (default: 20)
        offset: Pagination offset (default: 0)
        unread_only: Show only unread notifications (default: false)
    
    Returns:
        200: List of notifications
        401: User not authenticated
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get query parameters
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    # Step 3: Build the query
    query = Notification.query.filter_by(user_id=user.id)
    
    if unread_only:
        query = query.filter_by(read_at=None)
    
    # Step 4: Order by newest first and paginate
    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    # Step 5: Get total count
    total_count = query.count()
    
    # Step 6: Get unread count
    unread_count = Notification.query.filter_by(
        user_id=user.id,
        read_at=None
    ).count()
    
    # Step 7: Return notifications
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'count': len(notifications),
        'total': total_count,
        'unread_count': unread_count
    }), 200


# ============================================================
# ENDPOINT 2: MARK NOTIFICATION AS READ
# ============================================================
# PUT /api/notifications/<notification_id>/read

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """
    Mark a single notification as read.
    
    SRS Reference:
        FR-6.4: "Mark notifications as read individually"
    
    Returns:
        200: Notification updated
        401: User not authenticated
        403: Access denied
        404: Notification not found
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the notification
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Step 3: Check if user owns this notification
    if notification.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Step 4: Mark as read
    notification.mark_as_read()
    db.session.commit()
    
    # Step 5: Return updated notification
    return jsonify({
        'message': 'Notification marked as read',
        'notification': notification.to_dict()
    }), 200


# ============================================================
# ENDPOINT 3: MARK ALL NOTIFICATIONS AS READ
# ============================================================
# PUT /api/notifications/read-all

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """
    Mark all notifications for the current user as read.
    
    SRS Reference:
        FR-6.4: "Mark notifications as read in bulk"
    
    Returns:
        200: All notifications marked as read
        401: User not authenticated
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get all unread notifications
    unread_count = Notification.query.filter_by(
        user_id=user.id,
        read_at=None
    ).count()
    
    if unread_count > 0:
        # Step 3: Mark all as read
        Notification.mark_all_as_read(user.id)
        db.session.commit()
    
    # Step 4: Return success
    return jsonify({
        'message': 'All notifications marked as read',
        'marked_count': unread_count
    }), 200


# ============================================================
# ENDPOINT 4: GET UNREAD COUNT
# ============================================================
# GET /api/notifications/unread-count

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """
    Get the number of unread notifications for the current user.
    
    Returns:
        200: Unread count
        401: User not authenticated
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Count unread notifications
    unread_count = Notification.query.filter_by(
        user_id=user.id,
        read_at=None
    ).count()
    
    # Step 3: Return count
    return jsonify({
        'unread_count': unread_count
    }), 200


# ============================================================
# ENDPOINT 5: DELETE NOTIFICATION
# ============================================================
# DELETE /api/notifications/<notification_id>

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """
    Delete a notification.
    
    Returns:
        200: Notification deleted
        401: User not authenticated
        403: Access denied
        404: Notification not found
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the notification
    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    # Step 3: Check if user owns this notification
    if notification.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Step 4: Delete the notification
    db.session.delete(notification)
    db.session.commit()
    
    # Step 5: Return success
    return jsonify({
        'message': 'Notification deleted successfully'
    }), 200


# ============================================================
# ENDPOINT 6: BULK OPERATIONS
# ============================================================
# POST /api/notifications/bulk

@notifications_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_operation():
    """
    Perform bulk operations on notifications.
    
    SRS Reference:
        FR-6.4: Bulk operations
    
    Request Body:
        {
            "notification_ids": [1, 2, 3],
            "action": "mark_read"  # or "delete"
        }
    
    Returns:
        200: Bulk operation completed
        401: User not authenticated
        400: Invalid request
    """
    # Step 1: Get the current user
    user = get_user_from_token()
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    notification_ids = data.get('notification_ids', [])
    action = data.get('action')
    
    if not notification_ids:
        return jsonify({'error': 'No notification IDs provided'}), 400
    
    if action not in ['mark_read', 'delete']:
        return jsonify({'error': 'Invalid action. Use "mark_read" or "delete"'}), 400
    
    # Step 3: Get notifications
    notifications = Notification.query.filter(
        Notification.id.in_(notification_ids),
        Notification.user_id == user.id
    ).all()
    
    # Step 4: Perform action
    if action == 'mark_read':
        for notification in notifications:
            if not notification.is_read:
                notification.mark_as_read()
    elif action == 'delete':
        for notification in notifications:
            db.session.delete(notification)
    
    db.session.commit()
    
    # Step 5: Return success
    return jsonify({
        'message': f'Bulk {action} completed',
        'processed_count': len(notifications)
    }), 200
