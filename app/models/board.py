"""
Board Model

This module defines the Board model for the TeamUp application.
A board is a Kanban-style container within a project that holds columns and tasks.

SRS References:
- FR-2.2: Board with custom columns (To Do, In Progress, Done)
- Section 6.2: Boards table schema
- Section 6.1: Project (1) --- (M) Board relationship
"""

from datetime import datetime
from app.extensions import db


class Board(db.Model):
    """
    Board model representing a Kanban board within a project.
    
    This model maps to the 'boards' table in PostgreSQL.
    
    SRS Section 6.2: boards table with columns:
    - id (PK): Unique board identifier
    - project_id (FK): Project this board belongs to
    - name: Board name (e.g., "Sprint 1", "Product Roadmap")
    - description: Optional board description
    - position: Order of boards within a project
    - is_archived: Soft-delete flag
    - created_at: When the board was created
    - updated_at: Last time board was updated
    
    Relationships:
    - project: Project this board belongs to
    - columns: Columns within this board
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'boards'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each board
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key: Project this board belongs to
    # db.ForeignKey('projects.id'): References the projects table
    # nullable=False: Every board must belong to a project
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=0)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================================
    # RELATIONSHIPS (SRS Section 6.1)
    # ============================================================
    
    # Project relationship (Many-to-One)
    # back_populates: Links to Project.boards
    # lazy='joined': Load project when board is loaded
    project = db.relationship(
        'Project',
        back_populates='boards',
        lazy='joined'
    )
    
    # Columns in this board (One-to-Many)
    # cascade='all, delete-orphan': Delete columns when board is deleted
    # back_populates: Links to Column.board
    # lazy='dynamic': Returns a query object (can be filtered)
    # order_by: Sort columns by position
    # Why? FR-2.2: "Board to define custom columns"
    columns = db.relationship(
        'Column',
        back_populates='board',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='Column.position'
    )
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def archive(self):
        """Archive the board (soft delete)."""
        self.is_archived = True
        self.updated_at = datetime.utcnow()
    
    def unarchive(self):
        """Restore an archived board."""
        self.is_archived = False
        self.updated_at = datetime.utcnow()
    
    def create_default_columns(self):
        """
        Create default columns for a new board.
        
        SRS Reference:
        - FR-2.2: "Board to define custom columns (e.g., To Do, In Progress, Done)"
        
        This method creates the standard Kanban columns:
        - To Do
        - In Progress
        - Done
        
        Returns:
            list: The created Column objects
        """
        from app.models.column import Column
        
        # Define default columns with positions
        default_columns = [
            {'name': 'To Do', 'position': 0},
            {'name': 'In Progress', 'position': 1},
            {'name': 'Done', 'position': 2}
        ]
        
        created_columns = []
        for col_data in default_columns:
            column = Column(
                board_id=self.id,
                name=col_data['name'],
                position=col_data['position']
            )
            db.session.add(column)
            created_columns.append(column)
        
        return created_columns
    
    def get_column_by_name(self, name):
        """
        Get a column by its name.
        
        Args:
            name: Column name to search for
        
        Returns:
            Column: The column object, or None if not found
        """
        return self.columns.filter_by(name=name).first()
    
    def get_task_count(self):
        """
        Get the total number of tasks across all columns in this board.
        
        Returns:
            int: Total task count
        
        SRS Reference:
        - Section 6.1: Board (1) --- (M) Column (1) --- (M) Task
        """
        from app.models.task import Task
        
        # Join through columns to count tasks
        # Subquery: get all column IDs for this board
        column_ids = [col.id for col in self.columns.all()]
        if not column_ids:
            return 0
        
        return Task.query.filter(
            Task.column_id.in_(column_ids),
            Task.is_archived == False
        ).count()
    
    def get_column_count(self):
        """
        Get the number of columns in this board.
        
        Returns:
            int: Number of columns
        """
        return self.columns.filter_by(is_archived=False).count()
    
    def reorder_columns(self, column_order):
        """
        Reorder columns in this board.
        
        Args:
            column_order: List of column IDs in the desired order
        
        SRS Reference:
        - FR-3.2: "Drag-and-drop reordering of tasks within and across columns"
        """
        for position, column_id in enumerate(column_order):
            column = self.columns.filter_by(id=column_id).first()
            if column:
                column.position = position
                column.updated_at = datetime.utcnow()
    
    def to_dict(self, include_columns=False):
        """
        Convert board to dictionary for API responses.
        
        Args:
            include_columns: Include column details
        
        Returns:
            dict: Board data
        
        SRS Reference:
        - Section 7.1: REST API returns board data
        """
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'position': self.position,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'column_count': self.get_column_count(),
            'task_count': self.get_task_count()
        }
        
        if include_columns:
            data['columns'] = [
                column.to_dict(include_tasks=True) 
                for column in self.columns.filter_by(is_archived=False).all()
            ]
        
        return data
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<Board(id={self.id}, name={self.name}, project_id={self.project_id})>'
    
    def __str__(self):
        """Human-readable string representation."""
        return f'{self.name} (Project: {self.project.name if self.project else "Unknown"})'
