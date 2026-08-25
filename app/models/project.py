"""
Project Model

This module defines the Project model for the TeamUp application.
"""

from datetime import datetime
from app.extensions import db


class Project(db.Model):
    """
    Project model representing a workspace in the system.
    """
    
    __tablename__ = 'projects'
    
    # Columns (SRS Section 6.2)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('User', back_populates='projects', lazy='joined')
    boards = db.relationship('Board', back_populates='project', cascade='all, delete-orphan', lazy='dynamic', order_by='Board.position')
    memberships = db.relationship('ProjectMembership', back_populates='project', cascade='all, delete-orphan', lazy='dynamic')
    
    def archive(self):
        """Archive the project (soft delete)."""
        self.is_archived = True
        self.updated_at = datetime.utcnow()
    
    def unarchive(self):
        """Restore an archived project."""
        self.is_archived = False
        self.updated_at = datetime.utcnow()
    
    def is_owner(self, user):
        """Check if a user is the owner of this project."""
        return self.owner_id == user.id
    
    def is_admin(self, user):
        """Check if a user is an admin of this project."""
        membership = self.memberships.filter_by(user_id=user.id).first()
        if not membership:
            return False
        return membership.role in ['admin', 'owner']
    
    def is_member(self, user):
        """Check if a user is a member of this project."""
        if self.is_owner(user):
            return True
        return self.memberships.filter_by(user_id=user.id).first() is not None
    
    def add_member(self, user, role='member', invited_by=None):
        """Add a user as a member of this project."""
        if self.is_member(user):
            raise ValueError(f"User {user.email} is already a member of this project")
        
        from app.models.project_membership import ProjectMembership
        
        membership = ProjectMembership(
            project=self,
            user=user,
            role=role,
            invited_by_id=invited_by.id if invited_by else None
        )
        db.session.add(membership)
        return membership
    
    def remove_member(self, user):
        """Remove a user from the project."""
        if self.is_owner(user):
            raise ValueError("Cannot remove the project owner!")
        
        membership = self.memberships.filter_by(user_id=user.id).first()
        if not membership:
            raise ValueError(f"User {user.email} is not a member of this project")
        
        db.session.delete(membership)
    
    def get_member_role(self, user):
        """Get a user's role in this project."""
        if self.is_owner(user):
            return 'owner'
        
        membership = self.memberships.filter_by(user_id=user.id).first()
        if membership:
            return membership.role
        
        return None
    
    def get_members(self, role=None):
        """
        Get all members of this project, optionally filtered by role.
        
        ========================================================================
        WHY WE SPECIFY FOREIGN KEYS EXPLICITLY:
        ========================================================================
        The project_memberships table has two foreign keys to users:
        - user_id: The user who is a member
        - invited_by_id: The user who invited them
        
        SQLAlchemy needs to know which one to use when joining.
        We specify foreign_keys=ProjectMembership.user_id to use the user_id column.
        """
        from app.models.project_membership import ProjectMembership
        from app.models.user import User
        
        # Use the user relationship with proper foreign key
        # This tells SQLAlchemy to join using user_id, not invited_by_id
        query = User.query.join(
            ProjectMembership,
            ProjectMembership.user_id == User.id  # Specify the foreign key explicitly
        ).filter(
            ProjectMembership.project_id == self.id
        )
        
        if role == 'owner':
            # The owner is not in project_memberships, so we query them directly
            return User.query.filter_by(id=self.owner_id).all()
        elif role:
            query = query.filter(ProjectMembership.role == role)
        else:
            users = query.all()
            # Add owner if not already in the list
            if self.owner not in users:
                users.append(self.owner)
            return users
        
        return query.all()
    
    def get_board_count(self):
        """Get the number of boards in this project."""
        return self.boards.filter_by(is_archived=False).count()
    
    def get_member_count(self):
        """Get the number of members in this project."""
        return self.memberships.count() + 1  # +1 for owner
    
    def __repr__(self):
        return f'<Project(id={self.id}, name={self.name}, owner_id={self.owner_id})>'
    
    def __str__(self):
        return f'{self.name} (Owner: {self.owner.full_name if self.owner else "Unknown"})'
    
    def to_dict(self, include_owner=False, include_members=False):
        """Convert project to dictionary for API responses."""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'board_count': self.get_board_count(),
            'member_count': self.get_member_count()
        }
        
        if include_owner and self.owner:
            data['owner'] = self.owner.to_dict()
        
        if include_members:
            data['members'] = [
                member.to_dict() for member in self.get_members()
            ]
        
        return data
