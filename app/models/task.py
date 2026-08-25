"""
Task Model

This module defines the Task model for the TeamUp application.
"""

from datetime import datetime
from app.extensions import db


class Task(db.Model):
    """Task model representing an atomic unit of work."""
    
    __tablename__ = 'tasks'
    
    # Columns (SRS Section 6.2)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    column_id = db.Column(db.Integer, db.ForeignKey('columns.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True, index=True)
    position = db.Column(db.Integer, default=0)
    priority = db.Column(db.String(20), default='medium')
    labels = db.Column(db.JSON, default=list)
    estimated_hours = db.Column(db.Float, nullable=True)
    actual_hours = db.Column(db.Float, default=0.0)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (SRS Section 6.1)
    column = db.relationship('Column', back_populates='tasks', lazy='joined')
    assignments = db.relationship('TaskAssignment', back_populates='task', cascade='all, delete-orphan', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='task', cascade='all, delete-orphan', lazy='dynamic', order_by='Comment.created_at')
    
    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date and not self.is_archived
    
    @property
    def days_until_due(self):
        """Calculate days until the task is due."""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days
    
    def archive(self):
        """Archive the task (soft delete)."""
        self.is_archived = True
        self.updated_at = datetime.utcnow()
    
    def unarchive(self):
        """Restore an archived task."""
        self.is_archived = False
        self.updated_at = datetime.utcnow()
    
    def assign_user(self, user, assigned_by=None):
        """Assign a user to this task (FR-3.3)."""
        from app.models.task_assignment import TaskAssignment
        
        if self.is_assigned_to_user(user):
            raise ValueError(f"User {user.email} is already assigned to this task")
        
        assignment = TaskAssignment(
            task=self,
            user=user,
            assigned_by_id=assigned_by.id if assigned_by else None
        )
        db.session.add(assignment)
        return assignment
    
    def remove_user(self, user):
        """Remove a user's assignment to this task."""
        assignment = self.assignments.filter_by(user_id=user.id, is_active=True).first()
        if not assignment:
            raise ValueError(f"User {user.email} is not assigned to this task")
        
        # Soft delete by deactivating
        assignment.deactivate()
    
    def is_assigned_to_user(self, user):
        """
        Check if a user is assigned to this task.
        
        Args:
            user: User object to check
        
        Returns:
            bool: True if user is assigned, False otherwise
        """
        return self.assignments.filter_by(
            user_id=user.id,
            is_active=True
        ).first() is not None
    
    def get_assignees(self):
        """
        Get all users assigned to this task.
        
        Returns:
            list: List of User objects
        """
        from app.models import User
        from app.models.task_assignment import TaskAssignment
        
        # Get all active assignments for this task
        assignments = self.assignments.filter_by(is_active=True).all()
        
        # Get the user IDs from assignments
        user_ids = [assignment.user_id for assignment in assignments]
        
        if not user_ids:
            return []
        
        # Return the users
        return User.query.filter(User.id.in_(user_ids)).all()
    
    def add_comment(self, author, body, parent_id=None):
        """Add a comment to this task (FR-3.4)."""
        from app.models.comment import Comment
        comment = Comment(
            task_id=self.id,
            author_id=author.id,
            body=body,
            parent_comment_id=parent_id
        )
        db.session.add(comment)
        return comment
    
    def add_label(self, label):
        """Add a label to the task (FR-3.1)."""
        if label not in self.labels:
            self.labels.append(label)
            self.updated_at = datetime.utcnow()
    
    def remove_label(self, label):
        """Remove a label from the task."""
        if label in self.labels:
            self.labels.remove(label)
            self.updated_at = datetime.utcnow()
    
    def move_to_column(self, target_column, position=None):
        """Move the task to a different column (FR-3.2)."""
        self.column_id = target_column.id
        if position is not None:
            self.position = position
        else:
            self.position = target_column.tasks.count()
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Task(id={self.id}, title={self.title[:30]}...)>'
    
    def to_dict(self, include_assignees=False, include_comments=False):
        """Convert task to dictionary for API responses."""
        data = {
            'id': self.id,
            'column_id': self.column_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'position': self.position,
            'priority': self.priority,
            'labels': self.labels,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'is_archived': self.is_archived,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_assignees:
            data['assignees'] = [user.to_dict() for user in self.get_assignees()]
        
        if include_comments:
            data['comments'] = [comment.to_dict() for comment in self.comments.all()]
        
        return data
