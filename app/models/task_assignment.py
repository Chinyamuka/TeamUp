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
    
    This model maps to the 'task_assignments' table in PostgreSQL.
    It's a junction table for the many-to-many relationship between Task and User.
    
    SRS Section 6.2: task_assignments table with columns:
    - id (PK): Unique assignment identifier
    - task_id (FK): Task being assigned
    - user_id (FK): User being assigned to the task
    - assigned_by_id (FK): User who made the assignment (optional)
    - assigned_at: When the assignment was made
    - is_active: Whether the assignment is still active
    
    Relationships:
    - task: The task being assigned
    - user: The user assigned to the task
    - assigned_by: The user who made the assignment
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'task_assignments'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each assignment
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key: Task being assigned
    # db.ForeignKey('tasks.id'): References the tasks table
    # nullable=False: Assignment must reference a task
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    # Foreign Key: User being assigned to the task
    # db.ForeignKey('users.id'): References the users table
    # nullable=False: Assignment must reference a user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Foreign Key: User who made the assignment
    # db.ForeignKey('users.id'): References the users table
    # nullable=True: Could be system assignment (e.g., automation)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamp: When the assignment was made
    # default=datetime.utcnow: Set to current time when created
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Active Status: Whether this assignment is still active
    # default=True: New assignments are active
    # Why? Allows soft-deletion of assignments
    is_active = db.Column(db.Boolean, default=True)
    
    # ============================================================
    # UNIQUE CONSTRAINT
    # ============================================================
    # Ensure a user is only assigned once per task
    # This prevents duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('task_id', 'user_id', name='unique_task_user_assignment'),
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # Task relationship (Many-to-One)
    # back_populates: Links to Task.assignments
    # lazy='joined': Load task when assignment is loaded
    task = db.relationship(
        'Task',
        back_populates='assignments',
        lazy='joined'
    )
    
    # User relationship (Many-to-One)
    # back_populates: Links to User.assigned_tasks
    # lazy='joined': Load user when assignment is loaded
    user = db.relationship(
        'User',
        back_populates='assigned_tasks',
        lazy='joined',
        foreign_keys=[user_id]
    )
    
    # Assignor relationship (Many-to-One)
    # This is a self-reference to User for the person who made the assignment
    # lazy='joined': Load assignor when assignment is loaded
    assigned_by = db.relationship(
        'User',
        lazy='joined',
        foreign_keys=[assigned_by_id],
        backref='assigned_tasks_by_me'
    )
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def deactivate(self):
        """
        Deactivate this assignment.
        
        This soft-deletes the assignment without removing the record.
        Useful for auditing and tracking assignment history.
        """
        self.is_active = False
    
    def reactivate(self):
        """
        Reactivate a deactivated assignment.
        
        This restores a previously deactivated assignment.
        """
        self.is_active = True
    
    def get_assigned_by_display(self):
        """
        Get a display name for who made the assignment.
        
        Returns:
            str: Name of the assignor, or "System" if not specified
        
        Example:
            "Assigned by John Doe"
            "Assigned by System"
        """
        if self.assigned_by:
            return f"Assigned by {self.assigned_by.full_name}"
        return "Assigned by System"
    
    def to_dict(self):
        """
        Convert assignment to dictionary for API responses.
        
        Returns:
            dict: Assignment data
        
        SRS Reference:
        - Section 7.1: REST API returns assignment data
        """
        data = {
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
        
        return data
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """String representation for debugging."""
        return (
            f'<TaskAssignment(id={self.id}, '
            f'task_id={self.task_id}, '
            f'user_id={self.user_id}, '
            f'is_active={self.is_active})>'
        )
    
    def __str__(self):
        """Human-readable string representation."""
        return (
            f'Task "{self.task.title[:30] if self.task else "Unknown"}" → '
            f'User "{self.user.full_name if self.user else "Unknown"}" '
            f'({self.get_assigned_by_display()})'
        )
