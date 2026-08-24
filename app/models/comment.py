"""
Comment Model

This module defines the Comment model for the TeamUp application.
Comments enable team collaboration and discussion on tasks.

SRS References:
- FR-3.4: Comments and activity/audit log per task
- Section 6.2: Comments table schema
- Section 6.1: Task (1) --- (M) Comment
"""

from datetime import datetime
from app.extensions import db


class Comment(db.Model):
    """
    Comment model representing a user's message on a task.
    
    This model maps to the 'comments' table in PostgreSQL.
    
    SRS Section 6.2: comments table with columns:
    - id (PK): Unique comment identifier
    - task_id (FK): Task this comment belongs to
    - author_id (FK): User who wrote the comment
    - parent_comment_id (FK): For threaded/nested comments
    - body: The comment text
    - is_edited: Flag to indicate the comment was edited
    - edited_at: When the comment was last edited
    - created_at: When the comment was created
    - updated_at: Last time comment was updated
    
    Relationships:
    - task: Task this comment belongs to
    - author: User who wrote the comment
    - parent_comment: Parent comment (for threading)
    - replies: Child comments (replies to this comment)
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'comments'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each comment
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key: Task this comment belongs to
    # db.ForeignKey('tasks.id'): References the tasks table
    # nullable=False: Every comment must belong to a task
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    # Foreign Key: User who wrote the comment
    # db.ForeignKey('users.id'): References the users table
    # nullable=False: Every comment must have an author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Foreign Key: Parent comment (for threading)
    # db.ForeignKey('comments.id'): Self-reference for nested comments
    # nullable=True: Top-level comments have no parent
    # Why? Allows threaded discussions (reply to a comment)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    # Comment Body: The actual comment text
    # Text: Can be long with formatting (Markdown)
    # nullable=False: Body is required
    body = db.Column(db.Text, nullable=False)
    
    # Edit Status: Whether the comment was edited
    # default=False: New comments are not edited
    is_edited = db.Column(db.Boolean, default=False)
    
    # Edit Timestamp: When the comment was last edited
    # nullable=True: Only set if comment is edited
    edited_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps: Track when records were created/updated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # Task relationship (Many-to-One)
    # back_populates: Links to Task.comments
    # lazy='joined': Load task when comment is loaded
    task = db.relationship(
        'Task',
        back_populates='comments',
        lazy='joined'
    )
    
    # Author relationship (Many-to-One)
    # back_populates: Links to User.comments
    # lazy='joined': Load author when comment is loaded
    author = db.relationship(
        'User',
        back_populates='comments',
        lazy='joined'
    )
    
    # Parent comment relationship (Self-reference)
    # This allows nested/threaded comments
    # remote_side=[id]: Specifies the column on the parent side
    # back_populates: Links to Comment.replies
    # lazy='joined': Load parent when comment is loaded
    parent_comment = db.relationship(
        'Comment',
        remote_side=[id],
        back_populates='replies',
        lazy='joined'
    )
    
    # Replies (Child comments)
    # cascade='all, delete-orphan': Delete replies when parent is deleted
    # back_populates: Links to Comment.parent_comment
    # lazy='dynamic': Returns a query object (can be filtered)
    # order_by: Show oldest replies first
    replies = db.relationship(
        'Comment',
        back_populates='parent_comment',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='Comment.created_at'
    )
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def is_reply(self):
        """
        Check if this comment is a reply to another comment.
        
        Returns:
            bool: True if this comment has a parent
        """
        return self.parent_comment_id is not None
    
    @property
    def reply_count(self):
        """
        Get the number of replies to this comment.
        
        Returns:
            int: Number of replies
        """
        return self.replies.count()
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def edit(self, new_body):
        """
        Edit the comment body.
        
        Args:
            new_body: New text for the comment
        
        This method updates the comment body and marks it as edited.
        It preserves the original text by updating the body.
        """
        self.body = new_body
        self.is_edited = True
        self.edited_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_reply(self, author, body):
        """
        Add a reply to this comment.
        
        Args:
            author: User object writing the reply
            body: Reply text
        
        Returns:
            Comment: The created reply object
        
        Example:
            parent_comment = Comment.query.get(1)
            reply = parent_comment.add_reply(
                author=current_user,
                body="I agree! Let's do this."
            )
        """
        reply = Comment(
            task_id=self.task_id,
            author_id=author.id,
            parent_comment_id=self.id,
            body=body
        )
        db.session.add(reply)
        return reply
    
    def get_mention_users(self):
        """
        Extract @mentioned users from the comment body.
        
        This is a simple implementation for @mentions.
        Real implementation would be more sophisticated.
        
        Returns:
            list: List of mentioned usernames (strings)
        
        SRS Reference:
        - FR-6.2: "Notification when a user is @mentioned in a comment"
        """
        import re
        # Find all @username patterns
        pattern = r'@(\w+)'
        matches = re.findall(pattern, self.body)
        return matches
    
    def to_dict(self, include_replies=False):
        """
        Convert comment to dictionary for API responses.
        
        Args:
            include_replies: Include replies
        
        Returns:
            dict: Comment data
        
        SRS Reference:
        - Section 7.1: REST API returns comment data
        """
        data = {
            'id': self.id,
            'task_id': self.task_id,
            'author_id': self.author_id,
            'author_name': self.author.full_name if self.author else None,
            'author_email': self.author.email if self.author else None,
            'body': self.body,
            'is_edited': self.is_edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'is_reply': self.is_reply,
            'parent_comment_id': self.parent_comment_id,
            'reply_count': self.reply_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'mentions': self.get_mention_users()
        }
        
        if include_replies:
            data['replies'] = [
                reply.to_dict() for reply in self.replies.all()
            ]
        
        return data
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """String representation for debugging."""
        return (
            f'<Comment(id={self.id}, '
            f'task_id={self.task_id}, '
            f'author_id={self.author_id}, '
            f'body_preview={self.body[:30]}...)>'
        )
    
    def __str__(self):
        """Human-readable string representation."""
        author_name = self.author.full_name if self.author else "Unknown"
        return f'{author_name}: {self.body[:50]}...'
