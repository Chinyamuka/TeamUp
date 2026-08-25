"""
User Model

This module defines the User model for the TeamUp application.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import bcrypt

from app.extensions import db


class User(db.Model):
    """
    User model representing a registered user in the system.
    
    SRS Section 6.2: users table with columns:
    - id (PK): Unique user identifier
    - email (unique): User's email address
    - password_hash: Bcrypt hashed password
    - full_name: User's display name
    - is_active: Whether the user account is active
    - created_at: When the user registered
    - updated_at: Last time user record was updated
    """
    
    __tablename__ = 'users'
    
    # Columns (SRS Section 6.2)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', back_populates='owner', lazy='dynamic')
    
    # FIXED: Specify foreign_keys for memberships (user_id vs invited_by_id)
    memberships = db.relationship(
        'ProjectMembership',
        back_populates='user',
        lazy='dynamic',
        foreign_keys='ProjectMembership.user_id'
    )
    
    # FIXED: Specify foreign_keys for assigned_tasks (user_id vs assigned_by_id)
    assigned_tasks = db.relationship(
        'TaskAssignment',
        back_populates='user',
        lazy='dynamic',
        foreign_keys='TaskAssignment.user_id'
    )
    
    notifications = db.relationship(
        'Notification',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='desc(Notification.created_at)'
    )
    comments = db.relationship(
        'Comment',
        back_populates='author',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')
    
    @password.setter
    def password(self, password):
        """Set the password by hashing it with bcrypt (NFR-11)."""
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            salt
        ).decode('utf-8')
    
    def check_password(self, password):
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def get_full_name(self):
        return self.full_name
    
    def get_email(self):
        return self.email
    
    def is_owner_of_project(self, project):
        return self.id == project.owner_id
    
    def is_member_of_project(self, project):
        return self.memberships.filter_by(project_id=project.id).first() is not None
    
    def get_project_role(self, project):
        if self.is_owner_of_project(project):
            return 'owner'
        membership = self.memberships.filter_by(project_id=project.id).first()
        if membership:
            return membership.role
        return None
    
    def has_permission(self, project, required_role):
        user_role = self.get_project_role(project)
        if not user_role:
            return False
        role_priority = {'member': 1, 'admin': 2, 'owner': 3}
        return role_priority.get(user_role, 0) >= role_priority.get(required_role, 0)
    
    def __repr__(self):
        return f'<User(id={self.id}, email={self.email}, full_name={self.full_name})>'
    
    def __str__(self):
        return f'{self.full_name} ({self.email})'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
