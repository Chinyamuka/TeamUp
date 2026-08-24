"""
Project Model

This module defines the Project model for the TeamUp application.
A project is a container for boards and tasks, representing a workspace
where teams collaborate.

SRS References:
- FR-2.1: Project creation, renaming, and archival
- FR-2.3: Inviting members to projects
- FR-2.4: Role-based access control (Owner, Admin, Member)
- Section 6.2: Projects table schema
"""

from datetime import datetime
from app.extensions import db


class Project(db.Model):
    """
    Project model representing a workspace in the system.
    
    This model maps to the 'projects' table in PostgreSQL.
    
    SRS Section 6.2: projects table with columns:
    - id (PK): Unique project identifier
    - name: Project name
    - owner_id (FK): User who created/owns the project
    - description: Project description
    - is_archived: Soft-delete flag (SRS FR-2.1)
    - created_at: When the project was created
    - updated_at: Last time project was updated
    
    Relationships:
    - owner: User who owns the project
    - boards: Boards belonging to this project
    - memberships: Users who are members of this project
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'projects'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each project
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Project Name: Display name for the project
    # String(100): Reasonable length for a project name
    # nullable=False: Name is required
    name = db.Column(db.String(100), nullable=False)
    
    # Project Description: Optional detailed description
    # Text: Can be longer than String
    # nullable=True: Description is optional
    description = db.Column(db.Text, nullable=True)
    
    # Owner ID: Foreign key to the user who owns this project
    # db.ForeignKey('users.id'): References the users table
    # nullable=False: Every project must have an owner
    # Why? FR-2.4: "Owners/Admins can remove members"
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Soft Delete: Mark project as archived instead of deleting
    # This preserves data and allows recovery (SRS FR-2.1)
    # default=False: New projects are not archived
    # Why soft delete? Prevents accidental data loss
    is_archived = db.Column(db.Boolean, default=False, index=True)
    
    # Timestamps: Track when records were created/updated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================================
    # RELATIONSHIPS (SRS Section 6.1)
    # ============================================================
    
    # Owner relationship (Many-to-One)
    # back_populates: Links to User.projects
    # lazy='joined': Load owner when project is loaded (eager loading)
    owner = db.relationship(
        'User',
        back_populates='projects',
        lazy='joined'
    )
    
    # Boards in this project (One-to-Many)
    # cascade='all, delete-orphan': Delete boards when project is deleted
    # back_populates: Links to Board.project
    # lazy='dynamic': Returns a query object (can be filtered)
    # order_by: Sort boards by position
    # Why? FR-2.2: "Board with custom columns"
    boards = db.relationship(
        'Board',
        back_populates='project',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='Board.position'
    )
    
    # Project memberships (One-to-Many)
    # cascade='all, delete-orphan': Delete memberships when project is deleted
    # back_populates: Links to ProjectMembership.project
    # lazy='dynamic': Returns a query object
    # Why? FR-2.3: "Inviting members to a project"
    memberships = db.relationship(
        'ProjectMembership',
        back_populates='project',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def archive(self):
        """
        Archive the project (soft delete).
        
        SRS Reference:
        - FR-2.1: "System shall allow creation, renaming, and archival of projects"
        
        This method marks the project as archived instead of deleting it.
        Archived projects can be restored or permanently deleted later.
        """
        self.is_archived = True
        self.updated_at = datetime.utcnow()
    
    def unarchive(self):
        """
        Restore an archived project.
        
        This method unarchives a project, making it active again.
        """
        self.is_archived = False
        self.updated_at = datetime.utcnow()
    
    def is_owner(self, user):
        """
        Check if a user is the owner of this project.
        
        Args:
            user: User object to check
        
        Returns:
            bool: True if user is the owner
        
        SRS Reference:
        - FR-2.4: "Only Owners/Admins can remove members or delete boards"
        """
        return self.owner_id == user.id
    
    def is_admin(self, user):
        """
        Check if a user is an admin of this project.
        
        Args:
            user: User object to check
        
        Returns:
            bool: True if user is an admin
        
        SRS Reference:
        - FR-1.3: Role-based access control (Owner, Admin, Member)
        """
        membership = self.memberships.filter_by(user_id=user.id).first()
        if not membership:
            return False
        return membership.role in ['admin', 'owner']
    
    def is_member(self, user):
        """
        Check if a user is a member of this project.
        
        Args:
            user: User object to check
        
        Returns:
            bool: True if user is a member
        
        SRS Reference:
        - FR-2.3: "Inviting members to a project by email"
        """
        if self.is_owner(user):
            return True
        return self.memberships.filter_by(user_id=user.id).first() is not None
    
    def add_member(self, user, role='member', invited_by=None):
        """
        Add a user as a member of this project.
        
        Args:
            user: User to add
            role: 'admin' or 'member' (default: 'member')
            invited_by: User who invited the new member
        
        Returns:
            ProjectMembership: The created membership object
        
        SRS Reference:
        - FR-2.3: "Inviting members to a project by email with a role assignment"
        """
        # Check if user is already a member
        if self.is_member(user):
            raise ValueError(f"User {user.email} is already a member of this project")
        
        # Import here to avoid circular imports
        from app.models.project_membership import ProjectMembership
        
        # Create the membership
        membership = ProjectMembership(
            project=self,
            user=user,
            role=role,
            invited_by_id=invited_by.id if invited_by else None
        )
        
        db.session.add(membership)
        return membership
    
    def remove_member(self, user):
        """
        Remove a user from the project.
        
        Args:
            user: User to remove
        
        SRS Reference:
        - FR-2.4: "Only Owners/Admins can remove members"
        """
        if self.is_owner(user):
            raise ValueError("Cannot remove the project owner!")
        
        membership = self.memberships.filter_by(user_id=user.id).first()
        if not membership:
            raise ValueError(f"User {user.email} is not a member of this project")
        
        db.session.delete(membership)
    
    def get_member_role(self, user):
        """
        Get a user's role in this project.
        
        Args:
            user: User to check
        
        Returns:
            str: 'owner', 'admin', 'member', or None if not a member
        
        SRS Reference:
        - FR-1.3: "Role-based access control at the project level"
        """
        if self.is_owner(user):
            return 'owner'
        
        membership = self.memberships.filter_by(user_id=user.id).first()
        if membership:
            return membership.role
        
        return None
    
    def get_members(self, role=None):
        """
        Get all members of this project, optionally filtered by role.
        
        Args:
            role: Optional role filter ('owner', 'admin', 'member')
        
        Returns:
            list: List of User objects
        
        Example:
            admins = project.get_members(role='admin')
        """
        from app.models.user import User
        
        query = User.query.join(ProjectMembership).filter(
            ProjectMembership.project_id == self.id
        )
        
        if role == 'owner':
            # Owner is not in ProjectMembership
            return User.query.filter_by(id=self.owner_id).all()
        elif role:
            query = query.filter(ProjectMembership.role == role)
        else:
            # All members including owner
            users = query.all()
            # Add owner
            users.append(self.owner)
            return users
        
        return query.all()
    
    def get_board_count(self):
        """
        Get the number of boards in this project.
        
        Returns:
            int: Number of boards
        """
        return self.boards.filter_by(is_archived=False).count()
    
    def get_member_count(self):
        """
        Get the number of members in this project.
        
        Returns:
            int: Number of members (including owner)
        """
        return self.memberships.count() + 1  # +1 for owner
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<Project(id={self.id}, name={self.name}, owner_id={self.owner_id})>'
    
    def __str__(self):
        """Human-readable string representation."""
        return f'{self.name} (Owner: {self.owner.full_name if self.owner else "Unknown"})'
    
    def to_dict(self, include_owner=False, include_members=False):
        """
        Convert project to dictionary for API responses.
        
        Args:
            include_owner: Include owner details
            include_members: Include members list
        
        Returns:
            dict: Project data
        
        SRS Reference:
        - Section 7.1: REST API returns project data
        """
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
