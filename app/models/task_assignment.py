"""
Task Assignment Model

This module defines the TaskAssignment model for the TeamUp application.
It handles the many-to-many relationship between tasks and users.

SRS References:
- FR-3.3: Assigning a task to one or more project members
- Section 6.2: task_assignments table schema
- Section 6.1: Task (M) --- (M) User [via TaskAssignment]
"""

from datetime import datetime
from app.extensions import db


class TaskAssignment(db.Model):
    """
    TaskAssignment model representing a user assigned to a task.
    """
    
    __tablename__ = 'task_assignments'
    
    # Columns (SRS Section 6.2)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    task = db.relationship('Task', back_populates='assignments', lazy='joined')
    
    # FIXED: Specify foreign_keys explicitly for both relationships
    user = db.relationship(
        'User',
        back_populates='assigned_tasks',
        lazy='joined',
        foreign_keys=[user_id]
    )
    assigned_by = db.relationship(
        'User',
        lazy='joined',
        foreign_keys=[assigned_by_id],
        backref='assigned_tasks_by_me'
    )
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('task_id', 'user_id', name='unique_task_user_assignment'),
    )
    
    def deactivate(self):
        """Deactivate this assignment."""
        self.is_active = False
    
    def reactivate(self):
        """Reactivate a deactivated assignment."""
        self.is_active = True
    
    def get_assigned_by_display(self):
        """Get a display name for who made the assignment."""
        if self.assigned_by:
            return f"Assigned by {self.assigned_by.full_name}"
        return "Assigned by System"
    
    def to_dict(self):
        """Convert assignment to dictionary for API responses."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'assigned_by_id': self.assigned_by_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'is_active': self.is_active,
            'task_title': self.task.title if self.task else None,
            'user_name': self.user.full_name if self.user else None,
            'assigned_by_name': self.assigned_by.full_name if self.assigned_by else None,
            'assigned_by_display': self.get_assigned_by_display()
        }
    
    def __repr__(self):
        return f'<TaskAssignment(id={self.id}, task_id={self.task_id}, user_id={self.user_id}, is_active={self.is_active})>'
    
    def __str__(self):
        return f'Task "{self.task.title[:30] if self.task else "Unknown"}" → User "{self.user.full_name if self.user else "Unknown"}" ({self.get_assigned_by_display()})'
