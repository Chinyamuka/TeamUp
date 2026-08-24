"""
User Model

This module defines the User model for the TeamUp application.
It represents users who can register, login, and interact with the system.

SRS References:
- FR-1.1: User registration with email + password
- FR-1.3: Role-based access control (Owner, Admin, Member)
- NFR-11: Passwords hashed with bcrypt, cost ≥ 12
- Section 6.2: Users table schema
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import bcrypt

# Import the database instance from extensions
from app.extensions import db


class User(db.Model):
    """
    User model representing a registered user in the system.
    
    This model maps to the 'users' table in PostgreSQL.
    
    SRS Section 6.2: users table with columns:
    - id (PK): Unique user identifier
    - email (unique): User's email address (used for login)
    - password_hash: Bcrypt hashed password (never stored in plaintext!)
    - created_at: When the user registered
    - updated_at: Last time user record was updated
    - is_active: Whether the user account is active
    - full_name: User's display name
    
    Relationships:
    - projects: Projects owned by this user
    - memberships: Projects this user is a member of
    - assigned_tasks: Tasks assigned to this user
    - notifications: Notifications for this user
    - comments: Comments made by this user
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'users'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each user
    # db.Column() defines a column in the database
    # Integer: Store whole numbers
    # primary_key=True: This column is the primary key
    # autoincrement=True: Automatically increment for new users
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Email: Used for login and communication
    # String(255): Variable-length string, max 255 characters
    # nullable=False: This field is required (can't be empty)
    # unique=True: No two users can have the same email
    # index=True: Create an index for faster lookups (SRS Section 6.2)
    # Why index? FR-1.1: "email + password" login requires fast email lookups
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # Password Hash: Store bcrypt hash, never the actual password!
    # String(255): Enough for bcrypt hash
    # nullable=False: Password is required
    # Why hashed? NFR-11: "Passwords never stored in plaintext"
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Full Name: User's display name
    # String(100): Reasonable length for a name
    # nullable=False: Name is required
    full_name = db.Column(db.String(100), nullable=False)
    
    # Account Status: Whether the user account is active
    # Boolean: True = active, False = inactive/banned
    # default=True: New users are active by default
    # Why? Allows soft-deletion or temporary suspension
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps: Track when records were created/updated
    # DateTime: Date and time with timezone
    # default=datetime.utcnow: Set to current time when created
    # onupdate=datetime.utcnow: Update timestamp when record changes
    # Why? Audit trail, tracking user activity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================================
    # RELATIONSHIPS (SRS Section 6.1)
    # ============================================================
    
    # Projects owned by this user (One-to-Many)
    # backref: Creates a 'owner' property on Project model
    # lazy='dynamic': Returns a query object (can be filtered)
    # Why? FR-2.1: Users create projects
    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    
    # Project memberships (Many-to-Many through ProjectMembership)
    # This creates a relationship through the project_memberships table
    # back_populates: Links to the reverse relationship
    # Why? FR-2.3: Users can be invited to projects
    memberships = db.relationship(
        'ProjectMembership',
        back_populates='user',
        lazy='dynamic'
    )
    
    # Tasks assigned to this user (Many-to-Many through TaskAssignment)
    # This creates a relationship through the task_assignments table
    # back_populates: Links to the reverse relationship
    # Why? FR-3.3: Users can be assigned to tasks
    assigned_tasks = db.relationship(
        'TaskAssignment',
        back_populates='user',
        lazy='dynamic'
    )
    
    # Notifications for this user (One-to-Many)
    # cascade='all, delete-orphan': Delete notifications when user is deleted
    # order_by: Show newest notifications first
    # back_populates: Links to the reverse relationship
    # Why? FR-6.1: Users receive notifications
    notifications = db.relationship(
        'Notification',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='desc(Notification.created_at)'
    )
    
    # Comments made by this user (One-to-Many)
    # cascade='all, delete-orphan': Delete comments when user is deleted
    # back_populates: Links to the reverse relationship
    # Why? FR-3.4: Users can comment on tasks
    comments = db.relationship(
        'Comment',
        back_populates='author',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # ============================================================
    # PROPERTIES
    # ============================================================
    
    @property
    def password(self):
        """
        Prevent password from being accessed directly.
        
        Why? Security - we never want to expose the password.
        This property raises an exception if someone tries to access it.
        """
        raise AttributeError('Password is not a readable attribute.')
    
    @password.setter
    def password(self, password):
        """
        Set the password by hashing it with bcrypt.
        
        This method automatically hashes the password before storing it.
        
        SRS References:
        - NFR-11: "Passwords hashed with bcrypt, cost ≥ 12"
        - Section 9: "bcrypt-hashed passwords"
        
        Args:
            password: Plain text password to hash
        
        Why bcrypt?
        - Designed for password hashing
        - Slow to compute (resistant to brute force)
        - Automatically handles salt
        - Cost factor makes it future-proof
        
        Cost=12 (as required by NFR-11):
        - 2^12 = 4096 iterations
        - Balance between security and performance
        - Takes ~0.3 seconds to hash on modern hardware
        """
        # Generate salt and hash the password
        # bcrypt.gensalt() generates a random salt
        # cost=12 is required by NFR-11
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            salt
        ).decode('utf-8')
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def check_password(self, password):
        """
        Verify a password against the stored hash.
        
        This method is used during login (FR-1.2).
        
        Args:
            password: Plain text password to check
        
        Returns:
            bool: True if password matches, False otherwise
        
        Example:
            user = User.query.get(1)
            if user.check_password('my_password'):
                print("Login successful!")
        
        Why bcrypt.checkpw?
        - Constant-time comparison (resists timing attacks)
        - Automatically extracts salt from stored hash
        - Handles all the complexity of verification
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def get_full_name(self):
        """
        Get the user's full name.
        
        Returns:
            str: Full name of the user
        
        Why? Clean API for displaying user names.
        """
        return self.full_name
    
    def get_email(self):
        """
        Get the user's email.
        
        Returns:
            str: Email of the user
        """
        return self.email
    
    def is_owner_of_project(self, project):
        """
        Check if this user is the owner of a project.
        
        Args:
            project: Project object to check
        
        Returns:
            bool: True if user is owner
        
        SRS Reference:
        - FR-2.4: "Only Owners/Admins can remove members or delete boards"
        """
        return self.id == project.owner_id
    
    def is_member_of_project(self, project):
        """
        Check if this user is a member of a project.
        
        Args:
            project: Project object to check
        
        Returns:
            bool: True if user is a member
        
        SRS Reference:
        - FR-2.3: Users can be invited to projects
        """
        return self.memberships.filter_by(project_id=project.id).first() is not None
    
    def get_project_role(self, project):
        """
        Get the user's role in a project.
        
        Args:
            project: Project object to check
        
        Returns:
            str: 'owner', 'admin', 'member', or None if not a member
        
        SRS Reference:
        - FR-1.3: Role-based access control (Owner, Admin, Member)
        """
        # Check if user is the owner
        if self.is_owner_of_project(project):
            return 'owner'
        
        # Check membership
        membership = self.memberships.filter_by(project_id=project.id).first()
        if membership:
            return membership.role
        
        return None
    
    def has_permission(self, project, required_role):
        """
        Check if user has a specific role or higher in a project.
        
        Args:
            project: Project object
            required_role: 'owner', 'admin', or 'member'
        
        Returns:
            bool: True if user has the required role or higher
        
        Role hierarchy:
            owner > admin > member
        
        Example:
            if user.has_permission(project, 'admin'):
                # User is admin or owner
                delete_project()
        """
        user_role = self.get_project_role(project)
        
        if not user_role:
            return False
        
        # Define role hierarchy
        role_priority = {
            'member': 1,
            'admin': 2,
            'owner': 3
        }
        
        return role_priority.get(user_role, 0) >= role_priority.get(required_role, 0)
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """
        String representation of the user.
        
        This is used for debugging and logging.
        
        Returns:
            str: User representation
        
        Example:
            User(id=1, email='john@example.com', full_name='John Doe')
        """
        return f'<User(id={self.id}, email={self.email}, full_name={self.full_name})>'
    
    def __str__(self):
        """
        Human-readable string representation.
        
        Returns:
            str: User's full name and email
        """
        return f'{self.full_name} ({self.email})'
    
    def to_dict(self):
        """
        Convert user to dictionary for API responses.
        
        This is useful for JSON serialization in API endpoints.
        
        Returns:
            dict: User data without sensitive information (no password hash!)
        
        SRS Reference:
        - Section 7.1: REST API returns user data
        """
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
