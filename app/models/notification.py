"""
Notification Model

This module defines the Notification model for the TeamUp application.
Notifications inform users about events that require their attention.

SRS References:
- FR-6.1: In-app notification when user is assigned a task
- FR-6.2: Notification when user is @mentioned in a comment
- FR-6.3: Daily digest email of due/overdue tasks
- FR-6.4: Mark notifications as read individually or in bulk
- Section 6.2: Notifications table schema
- Section 6.1: User (1) --- (M) Notification
"""

from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    """
    Notification model representing in-app alerts for users.
    
    This model maps to the 'notifications' table in PostgreSQL.
    
    SRS Section 6.2: notifications table with columns:
    - id (PK): Unique notification identifier
    - user_id (FK): User this notification is for
    - type: Notification type (task_assigned, mention, due_reminder, etc.)
    - title: Notification title
    - message: Notification message
    - payload (JSONB): Additional data (task_id, comment_id, etc.)
    - read_at: When the notification was read (NULL = unread)
    - is_read: Boolean flag for read status (for quick filtering)
    - created_at: When the notification was created
    - updated_at: Last time notification was updated
    
    Relationships:
    - user: User this notification belongs to
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'notifications'
    
    # ============================================================
    # NOTIFICATION TYPES (Constants)
    # ============================================================
    TYPE_TASK_ASSIGNED = 'task_assigned'
    TYPE_TASK_MENTION = 'task_mention'
    TYPE_TASK_COMMENT = 'task_comment'
    TYPE_TASK_DUE_SOON = 'task_due_soon'
    TYPE_TASK_OVERDUE = 'task_overdue'
    TYPE_TASK_COMPLETED = 'task_completed'
    TYPE_PROJECT_INVITE = 'project_invite'
    TYPE_PROJECT_ACCEPTED = 'project_accepted'
    TYPE_BOARD_UPDATE = 'board_update'
    TYPE_SYSTEM_ALERT = 'system_alert'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each notification
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key: User this notification belongs to
    # db.ForeignKey('users.id'): References the users table
    # nullable=False: Every notification must belong to a user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification Type: Categorizes the notification
    # String(50): One of the TYPE_* constants
    # nullable=False: Type is required
    type = db.Column(db.String(50), nullable=False, index=True)
    
    # Notification Title: Short summary
    # String(200): Brief title for the notification
    # nullable=False: Title is required
    title = db.Column(db.String(200), nullable=False)
    
    # Notification Message: Detailed message
    # Text: Full notification text
    # nullable=False: Message is required
    message = db.Column(db.Text, nullable=False)
    
    # Payload: Additional data for the notification
    # JSON: Flexible data structure for frontend use
    # Examples:
    #   {'task_id': 1, 'task_title': 'Fix login bug'}
    #   {'comment_id': 2, 'comment_author': 'John'}
    #   {'project_id': 3, 'project_name': 'Sprint 1'}
    # nullable=True: Some notifications don't need extra data
    payload = db.Column(db.JSON, nullable=True)
    
    # Read Status: Whether the notification has been read
    # DateTime: NULL means unread, set when read
    # nullable=True: Notifications start as unread
    # index=True: For faster queries of unread notifications
    read_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Click Action: URL or action for the notification click
    # String(255): Where to navigate when clicked
    # Example: '/tasks/1', '/projects/3'
    # nullable=True: Some notifications don't navigate
    click_action = db.Column(db.String(255), nullable=True)
    
    # Icon: Optional icon for visual distinction
    # String(50): Icon name or emoji
    # nullable=True: Use default icon
    icon = db.Column(db.String(50), nullable=True)
    
    # Timestamps: Track when records were created/updated
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # User relationship (Many-to-One)
    # back_populates: Links to User.notifications
    # lazy='joined': Load user when notification is loaded
    user = db.relationship(
        'User',
        back_populates='notifications',
        lazy='joined'
    )
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_read(self):
        """
        Check if the notification has been read.
        
        Returns:
            bool: True if read_at is not None
        """
        return self.read_at is not None
    
    @property
    def time_ago(self):
        """
        Get a human-readable time difference.
        
        Returns:
            str: Time elapsed since notification was created
        
        Example:
            "5 minutes ago"
            "2 hours ago"
            "3 days ago"
        """
        now = datetime.utcnow()
        delta = now - self.created_at
        
        if delta.days > 30:
            return f"{delta.days // 30} months ago"
        elif delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "Just now"
    
    # ============================================================
    # CLASS METHODS (Factory Methods)
    # ============================================================
    
    @classmethod
    def create_task_assigned(cls, user, task, assigned_by):
        """
        Create a notification for task assignment.
        
        Args:
            user: User being assigned the task
            task: Task being assigned
            assigned_by: User who made the assignment
        
        Returns:
            Notification: Created notification
        
        SRS Reference:
        - FR-6.1: "Create an in-app notification when a user is assigned a task"
        """
        return cls(
            user_id=user.id,
            type=cls.TYPE_TASK_ASSIGNED,
            title=f"New task assigned: {task.title}",
            message=f"{assigned_by.full_name} assigned you to task '{task.title}'",
            payload={
                'task_id': task.id,
                'task_title': task.title,
                'assigned_by_id': assigned_by.id,
                'assigned_by_name': assigned_by.full_name
            },
            click_action=f"/tasks/{task.id}",
            icon="📋"
        )
    
    @classmethod
    def create_mention(cls, user, comment, mentioned_by):
        """
        Create a notification for a @mention in a comment.
        
        Args:
            user: User being mentioned
            comment: Comment containing the mention
            mentioned_by: User who wrote the comment
        
        Returns:
            Notification: Created notification
        
        SRS Reference:
        - FR-6.2: "Create a notification when a user is @mentioned in a comment"
        """
        task = comment.task
        return cls(
            user_id=user.id,
            type=cls.TYPE_TASK_MENTION,
            title=f"Mentioned in comment on '{task.title}'",
            message=f"{mentioned_by.full_name} mentioned you in a comment: '{comment.body[:50]}...'",
            payload={
                'task_id': task.id,
                'task_title': task.title,
                'comment_id': comment.id,
                'comment_body': comment.body,
                'mentioned_by_id': mentioned_by.id,
                'mentioned_by_name': mentioned_by.full_name
            },
            click_action=f"/tasks/{task.id}#comment-{comment.id}",
            icon="💬"
        )
    
    @classmethod
    def create_task_comment(cls, user, comment, commented_by):
        """
        Create a notification for a new comment on a task.
        
        Args:
            user: User who should be notified
            comment: The new comment
            commented_by: User who wrote the comment
        
        Returns:
            Notification: Created notification
        """
        task = comment.task
        return cls(
            user_id=user.id,
            type=cls.TYPE_TASK_COMMENT,
            title=f"New comment on '{task.title}'",
            message=f"{commented_by.full_name} commented: '{comment.body[:50]}...'",
            payload={
                'task_id': task.id,
                'task_title': task.title,
                'comment_id': comment.id,
                'comment_body': comment.body,
                'commented_by_id': commented_by.id,
                'commented_by_name': commented_by.full_name
            },
            click_action=f"/tasks/{task.id}#comment-{comment.id}",
            icon="💭"
        )
    
    @classmethod
    def create_due_soon(cls, user, task):
        """
        Create a notification for a task due soon.
        
        Args:
            user: User assigned to the task
            task: Task that is due soon
        
        Returns:
            Notification: Created notification
        
        SRS Reference:
        - FR-6.3: "Daily digest email of due/overdue tasks"
        """
        days = task.days_until_due
        return cls(
            user_id=user.id,
            type=cls.TYPE_TASK_DUE_SOON,
            title=f"Task due soon: '{task.title}'",
            message=f"Task '{task.title}' is due in {days} days",
            payload={
                'task_id': task.id,
                'task_title': task.title,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'days_until_due': days
            },
            click_action=f"/tasks/{task.id}",
            icon="⏰"
        )
    
    @classmethod
    def create_overdue(cls, user, task):
        """
        Create a notification for an overdue task.
        
        Args:
            user: User assigned to the task
            task: Task that is overdue
        
        Returns:
            Notification: Created notification
        
        SRS Reference:
        - FR-6.3: "Daily digest email of due/overdue tasks"
        """
        return cls(
            user_id=user.id,
            type=cls.TYPE_TASK_OVERDUE,
            title=f"Task overdue: '{task.title}'",
            message=f"Task '{task.title}' is overdue by {abs(task.days_until_due)} days",
            payload={
                'task_id': task.id,
                'task_title': task.title,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'days_overdue': abs(task.days_until_due)
            },
            click_action=f"/tasks/{task.id}",
            icon="🔥"
        )
    
    @classmethod
    def create_project_invite(cls, user, project, invited_by):
        """
        Create a notification for a project invitation.
        
        Args:
            user: User being invited
            project: Project they're invited to
            invited_by: User who sent the invitation
        
        Returns:
            Notification: Created notification
        
        SRS Reference:
        - FR-2.3: "Inviting members to a project by email"
        """
        return cls(
            user_id=user.id,
            type=cls.TYPE_PROJECT_INVITE,
            title=f"Invited to project: {project.name}",
            message=f"{invited_by.full_name} invited you to join '{project.name}'",
            payload={
                'project_id': project.id,
                'project_name': project.name,
                'invited_by_id': invited_by.id,
                'invited_by_name': invited_by.full_name
            },
            click_action=f"/projects/{project.id}",
            icon="🏢"
        )
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def mark_as_read(self):
        """
        Mark the notification as read.
        
        SRS Reference:
        - FR-6.4: "Mark notifications as read individually or in bulk"
        """
        if not self.is_read:
            self.read_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def mark_as_unread(self):
        """
        Mark the notification as unread.
        """
        self.read_at = None
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def mark_all_as_read(cls, user_id):
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: User ID
        
        SRS Reference:
            - FR-6.4: "Mark notifications as read individually or in bulk"
        """
        now = datetime.utcnow()
        cls.query.filter_by(
            user_id=user_id,
            read_at=None
        ).update({
            'read_at': now,
            'updated_at': now
        })
    
    def to_dict(self):
        """
        Convert notification to dictionary for API responses.
        
        Returns:
            dict: Notification data
        
        SRS Reference:
        - Section 7.1: REST API returns notification data
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'payload': self.payload,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'time_ago': self.time_ago,
            'click_action': self.click_action,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """String representation for debugging."""
        return (
            f'<Notification(id={self.id}, '
            f'user_id={self.user_id}, '
            f'type={self.type}, '
            f'read={self.is_read})>'
        )
    
    def __str__(self):
        """Human-readable string representation."""
        status = "Read" if self.is_read else "Unread"
        return f'[{status}] {self.title}: {self.message[:50]}...'
