"""
Column Model

This module defines the Column model for the TeamUp application.
A column is a vertical section within a board that holds tasks at a specific stage.

SRS References:
- FR-2.2: Board with custom columns (To Do, In Progress, Done)
- FR-3.2: Drag-and-drop reordering of tasks within and across columns
- Section 6.2: Columns table schema
- Section 6.1: Board (1) --- (M) Column (1) --- (M) Task
"""

from datetime import datetime
from app.extensions import db


class Column(db.Model):
    """
    Column model representing a vertical section within a board.
    
    This model maps to the 'columns' table in PostgreSQL.
    
    SRS Section 6.2: columns table with columns:
    - id (PK): Unique column identifier
    - board_id (FK): Board this column belongs to
    - name: Column name (e.g., "To Do", "In Progress", "Done")
    - position: Order of columns within a board
    - color: Optional color coding for the column
    - is_archived: Soft-delete flag
    - created_at: When the column was created
    - updated_at: Last time column was updated
    
    Relationships:
    - board: Board this column belongs to
    - tasks: Tasks within this column
    """
    
    # ============================================================
    # TABLE NAME
    # ============================================================
    __tablename__ = 'columns'
    
    # ============================================================
    # COLUMNS (SRS Section 6.2)
    # ============================================================
    
    # Primary Key: Unique identifier for each column
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key: Board this column belongs to
    # db.ForeignKey('boards.id'): References the boards table
    # nullable=False: Every column must belong to a board
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    
    # Column Name: Display name for the column
    # String(50): Reasonable length for column names
    # nullable=False: Name is required
    # Examples: "To Do", "In Progress", "Review", "Done"
    name = db.Column(db.String(50), nullable=False)
    
    # Position: Order of columns within a board
    # Integer: Lower numbers appear first (left to right)
    # default=0: New columns appear at the right end
    # Why? FR-3.2: Drag-and-drop reordering requires ordering
    position = db.Column(db.Integer, default=0)
    
    # Color: Optional color coding for visual distinction
    # String(20): Hex color code or color name
    # default=None: No specific color
    # Example: "#FF6B6B" for red, "#4ECDC4" for teal
    color = db.Column(db.String(20), nullable=True)
    
    # Max Tasks: Optional limit on number of tasks
    # Integer: Maximum tasks allowed in this column
    # default=None: No limit
    # Why? Work in progress (WIP) limits
    max_tasks = db.Column(db.Integer, nullable=True)
    
    # Soft Delete: Mark column as archived instead of deleting
    # default=False: New columns are not archived
    is_archived = db.Column(db.Boolean, default=False, index=True)
    
    # Timestamps: Track when records were created/updated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ============================================================
    # RELATIONSHIPS (SRS Section 6.1)
    # ============================================================
    
    # Board relationship (Many-to-One)
    # back_populates: Links to Board.columns
    # lazy='joined': Load board when column is loaded
    board = db.relationship(
        'Board',
        back_populates='columns',
        lazy='joined'
    )
    
    # Tasks in this column (One-to-Many)
    # cascade='all, delete-orphan': Delete tasks when column is deleted
    # back_populates: Links to Task.column
    # lazy='dynamic': Returns a query object (can be filtered)
    # order_by: Sort tasks by position
    # Why? FR-3.2: Tasks within columns can be reordered
    tasks = db.relationship(
        'Task',
        back_populates='column',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='Task.position'
    )
    
    # ============================================================
    # INSTANCE METHODS
    # ============================================================
    
    def archive(self):
        """Archive the column (soft delete)."""
        self.is_archived = True
        self.updated_at = datetime.utcnow()
    
    def unarchive(self):
        """Restore an archived column."""
        self.is_archived = False
        self.updated_at = datetime.utcnow()
    
    def add_task(self, title, **kwargs):
        """
        Add a new task to this column.
        
        Args:
            title: Task title (required)
            **kwargs: Additional task fields (description, due_date, etc.)
        
        Returns:
            Task: The created task object
        
        SRS Reference:
        - FR-3.1: "Create tasks with title, description, labels, due date"
        """
        from app.models.task import Task
        
        task = Task(
            column_id=self.id,
            title=title,
            position=self.tasks.count(),  # Add to the end
            **kwargs
        )
        db.session.add(task)
        return task
    
    def get_task_count(self):
        """
        Get the number of tasks in this column.
        
        Returns:
            int: Number of active tasks
        
        SRS Reference:
        - Section 6.1: Column (1) --- (M) Task
        """
        return self.tasks.filter_by(is_archived=False).count()
    
    def is_full(self):
        """
        Check if the column has reached its maximum task limit.
        
        Returns:
            bool: True if column is full, False otherwise
        
        Example:
            if not column.is_full():
                column.add_task("New Task")
        """
        if self.max_tasks is None:
            return False
        return self.get_task_count() >= self.max_tasks
    
    def reorder_tasks(self, task_order):
        """
        Reorder tasks within this column.
        
        Args:
            task_order: List of task IDs in the desired order
        
        SRS Reference:
        - FR-3.2: "Drag-and-drop reordering of tasks within and across columns"
        """
        for position, task_id in enumerate(task_order):
            task = self.tasks.filter_by(id=task_id).first()
            if task:
                task.position = position
                task.updated_at = datetime.utcnow()
    
    def move_task_to(self, task, target_column, position=None):
        """
        Move a task to a different column.
        
        Args:
            task: Task object to move
            target_column: Column to move the task to
            position: Optional position in the target column
        
        SRS Reference:
        - FR-3.2: "Drag-and-drop reordering of tasks within and across columns"
        
        Example:
            # Move task to "Done" column at position 2
            done_column = board.get_column_by_name("Done")
            column.move_task_to(task, done_column, position=2)
        """
        # Remove task from current column's task list
        # The task will still exist, just with a new column_id
        
        # Set the new column
        task.column_id = target_column.id
        
        # Set position if specified
        if position is not None:
            task.position = position
        else:
            # Move to the end of the target column
            task.position = target_column.tasks.count()
        
        task.updated_at = datetime.utcnow()
    
    def to_dict(self, include_tasks=False):
        """
        Convert column to dictionary for API responses.
        
        Args:
            include_tasks: Include task details
        
        Returns:
            dict: Column data
        
        SRS Reference:
        - Section 7.1: REST API returns column data
        """
        data = {
            'id': self.id,
            'board_id': self.board_id,
            'name': self.name,
            'position': self.position,
            'color': self.color,
            'max_tasks': self.max_tasks,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': self.get_task_count(),
            'is_full': self.is_full()
        }
        
        if include_tasks:
            data['tasks'] = [
                task.to_dict() 
                for task in self.tasks.filter_by(is_archived=False).all()
            ]
        
        return data
    
    # ============================================================
    # REPRESENTATION METHODS
    # ============================================================
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<Column(id={self.id}, name={self.name}, board_id={self.board_id})>'
    
    def __str__(self):
        """Human-readable string representation."""
        return f'{self.name} (Board: {self.board.name if self.board else "Unknown"})'
