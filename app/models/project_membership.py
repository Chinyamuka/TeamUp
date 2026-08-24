"""
Project Membership Model

This module defines the ProjectMembership model for the TeamUp application.
It handles the many-to-many relationship between users and projects.

SRS References:
- FR-2.3: Inviting members to a project
- FR-2.4: Role-based access control (Owner, Admin, Member)
- Section 6.2: project_memberships table schema
"""

from datetime import datetime
from app.extensions import db


class ProjectMembership(db.Model):
    """Project membership model for user-project many-to-many relationship."""
    
    __tablename__ = 'project_memberships'
    
    # Columns (SRS Section 6.2)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'admin' or 'member'
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships (SRS Section 6.1)
    project = db.relationship('Project', back_populates='memberships')
    user = db.relationship('User', back_populates='memberships')
    invited_by = db.relationship('User', foreign_keys=[invited_by_id])
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='unique_project_user'),
    )
    
    def __repr__(self):
        return f'<ProjectMembership(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>'
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'role': self.role,
            'invited_by_id': self.invited_by_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'user_name': self.user.full_name if self.user else None,
            'project_name': self.project.name if self.project else None
        }
