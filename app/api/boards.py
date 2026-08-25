"""
Board API Routes

This module handles all board-related operations in the TeamUp application.
A board is a Kanban-style container within a project that holds columns and tasks.

SRS References:
- FR-2.2: Board with custom columns (To Do, In Progress, Done)
- FR-3.2: Drag-and-drop reordering of tasks within and across columns
- Section 6.2: boards table schema
- Section 7.1: REST API endpoints

Endpoints:
    GET    /api/boards/project/<project_id>  - List all boards in a project
    POST   /api/boards/project/<project_id>  - Create a new board
    GET    /api/boards/<board_id>            - Get board details
    PUT    /api/boards/<board_id>            - Update a board
    DELETE /api/boards/<board_id>            - Archive a board
    POST   /api/boards/<board_id>/reorder    - Reorder columns
"""

# ============================================================
# IMPORTS
# ============================================================
# Flask imports for routing and request handling
from flask import Blueprint, request, jsonify

# JWT imports for authentication
from flask_jwt_extended import jwt_required, get_jwt_identity

# Database imports
from app.extensions import db

# Model imports - these are our database tables
from app.models import User, Project, Board, Column

# ============================================================
# CREATE BLUEPRINT
# ============================================================
# A Blueprint groups related routes together.
# Think of it like a mini-application within Flask.
# url_prefix='/api/boards' means all routes start with /api/boards
boards_bp = Blueprint('boards', __name__, url_prefix='/api/boards')


# ============================================================
# HELPER FUNCTIONS
# ============================================================
# These functions are used by multiple endpoints.
# They keep our code DRY (Don't Repeat Yourself).

def get_user_from_token():
    """
    Get the current user from the JWT token.
    
    Why do we need this?
    - Every request needs to know who is making it
    - The JWT token contains the user's ID
    - We extract it and fetch the User object from the database
    
    Returns:
        User object if found, None if not found
    
    How it works:
        1. get_jwt_identity() extracts the user ID from the token
        2. We query the database for that user
        3. If found, we return the User object
        4. If not found, we return None (user might have been deleted)
    """
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    
    # Query the database for this user
    # int() converts the string ID to an integer
    user = User.query.get(int(user_id))
    
    return user


def get_project_or_404(project_id, user):
    """
    Get a project by ID and check if the user has access.
    
    Why do we need this?
    - Users should only see projects they are members of
    - We need to check permissions before allowing access
    
    Args:
        project_id: The ID of the project to fetch
        user: The current user (from get_user_from_token)
    
    Returns:
        Project object if found AND user has access, None otherwise
    
    How it works:
        1. Query the project by ID (only non-archived projects)
        2. If project doesn't exist, return None
        3. Check if user is a member of the project
        4. If not a member, return None
        5. Otherwise, return the project
    
    SRS Reference:
        FR-2.4: "Role-based access control at the project level"
    """
    # Query for the project
    # filter_by is a SQLAlchemy method that creates a WHERE clause
    # is_archived=False means we only get active projects
    project = Project.query.filter_by(
        id=project_id,
        is_archived=False
    ).first()
    
    # If project doesn't exist, return None
    if not project:
        return None
    
    # Check if user is a member of this project
    # is_member() is a method on the Project model
    if not project.is_member(user):
        return None
    
    return project


def get_board_or_404(board_id, user):
    """
    Get a board by ID and check if the user has access.
    
    Why do we need this?
    - Boards belong to projects, and users must have access to the project
    - We need to check permissions before allowing access
    
    Args:
        board_id: The ID of the board to fetch
        user: The current user (from get_user_from_token)
    
    Returns:
        Board object if found AND user has access, None otherwise
    
    How it works:
        1. Query the board by ID (only non-archived boards)
        2. If board doesn't exist, return None
        3. Check if the board's project is accessible to the user
        4. If not, return None
        5. Otherwise, return the board
    """
    # Query for the board
    board = Board.query.filter_by(
        id=board_id,
        is_archived=False
    ).first()
    
    # If board doesn't exist, return None
    if not board:
        return None
    
    # Check if user has access to the board's project
    # board.project gives us the project this board belongs to
    if not board.project.is_member(user):
        return None
    
    return board


# ============================================================
# ENDPOINT 1: LIST BOARDS
# ============================================================
# GET /api/boards/project/<project_id>
# Lists all boards in a specific project

@boards_bp.route('/project/<int:project_id>', methods=['GET'])
@jwt_required()  # This endpoint requires authentication
def list_boards(project_id):
    """
    List all boards in a project.
    
    SRS Reference:
        FR-2.2: "Board with custom columns (To Do, In Progress, Done)"
        Section 7.1: GET /api/boards/:id
    
    How it works:
        1. Get the current user from the JWT token
        2. Get the project and check access
        3. Fetch all non-archived boards in the project
        4. Return them as JSON
    
    Returns:
        200: List of boards with their columns
        401: User not authenticated
        404: Project not found or access denied
    """
    # Step 1: Get the current user from the token
    user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the project and check access
    project = get_project_or_404(project_id, user)
    
    # If project doesn't exist or user can't access it, return 404
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Step 3: Fetch all non-archived boards in the project
    # .filter_by(is_archived=False) - only active boards
    # .all() - execute the query and get all results
    boards = project.boards.filter_by(is_archived=False).all()
    
    # Step 4: Convert boards to dictionaries for JSON response
    # to_dict(include_columns=True) includes columns and their tasks
    # This is useful for the frontend to display the full board
    boards_data = [board.to_dict(include_columns=True) for board in boards]
    
    # Step 5: Return the response
    # jsonify automatically converts Python dict to JSON
    return jsonify({
        'boards': boards_data,
        'count': len(boards_data)  # Helpful for pagination
    }), 200  # 200 OK


# ============================================================
# ENDPOINT 2: CREATE BOARD
# ============================================================
# POST /api/boards/project/<project_id>
# Creates a new board in a project with default columns

@boards_bp.route('/project/<int:project_id>', methods=['POST'])
@jwt_required()  # This endpoint requires authentication
def create_board(project_id):
    """
    Create a new board in a project.
    
    SRS Reference:
        FR-2.2: "Board with custom columns (To Do, In Progress, Done)"
    
    Request Body:
        {
            "name": "Sprint 1",
            "description": "First sprint board"
        }
    
    How it works:
        1. Get the current user from the JWT token
        2. Get the project and check access
        3. Validate the request data
        4. Create the board
        5. Create default columns (To Do, In Progress, Done)
        6. Save everything to the database
        7. Return the created board
    
    Returns:
        201: Board created successfully
        400: Invalid request data
        401: User not authenticated
        403: User doesn't have permission
        404: Project not found
    """
    # Step 1: Get the current user from the token
    user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the project and check access
    project = get_project_or_404(project_id, user)
    
    # If project doesn't exist or user can't access it, return 404
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Step 3: Check if user has permission to create boards
    # Any member can create boards (FR-2.4)
    if not project.is_member(user):
        return jsonify({'error': 'You do not have permission to create boards'}), 403
    
    # Step 4: Get and validate the request data
    # request.get_json() parses the JSON body
    data = request.get_json()
    
    # If no data was sent, return 400 Bad Request
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get the board name from the request
    name = data.get('name')
    
    # Board name is required (FR-2.2)
    if not name:
        return jsonify({'error': 'Board name is required'}), 400
    
    # Get description (optional)
    description = data.get('description', '')
    
    # Step 5: Determine the board's position
    # Get the last board in the project (highest position)
    # This ensures new boards appear at the end
    last_board = project.boards.filter_by(
        is_archived=False
    ).order_by(Board.position.desc()).first()
    
    # If there are existing boards, position = last position + 1
    # Otherwise, position = 0 (first board)
    position = (last_board.position + 1) if last_board else 0
    
    # Step 6: Create the board
    board = Board(
        project_id=project.id,
        name=name,
        description=description,
        position=position
    )
    
    # Add the board to the session (staged for saving)
    db.session.add(board)
    
    # Step 7: Flush to get the board ID
    # db.session.flush() sends SQL to the database but doesn't commit
    # This gives us the board.id before we create columns
    db.session.flush()
    
    # Step 8: Create default columns (FR-2.2)
    # Every new board gets these three columns by default
    default_columns = [
        Column(name='To Do', position=0, board_id=board.id),
        Column(name='In Progress', position=1, board_id=board.id),
        Column(name='Done', position=2, board_id=board.id)
    ]
    
    # Add each column to the session
    for column in default_columns:
        db.session.add(column)
    
    # Step 9: Commit everything to the database
    # db.session.commit() saves all changes permanently
    db.session.commit()
    
    # Step 10: Return the created board
    # to_dict(include_columns=True) includes the default columns
    return jsonify({
        'message': 'Board created successfully',
        'board': board.to_dict(include_columns=True)
    }), 201  # 201 Created


# ============================================================
# ENDPOINT 3: GET BOARD
# ============================================================
# GET /api/boards/<board_id>
# Gets a specific board with all its columns and tasks

@boards_bp.route('/<int:board_id>', methods=['GET'])
@jwt_required()  # This endpoint requires authentication
def get_board(board_id):
    """
    Get a specific board by ID with all columns and tasks.
    
    SRS Reference:
        Section 7.1: GET /api/boards/:id
    
    How it works:
        1. Get the current user from the JWT token
        2. Get the board and check access
        3. Return the board with columns and tasks
    
    Returns:
        200: Board details with columns and tasks
        401: User not authenticated
        404: Board not found or access denied
    """
    # Step 1: Get the current user from the token
    user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the board and check access
    board = get_board_or_404(board_id, user)
    
    # If board doesn't exist or user can't access it, return 404
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Step 3: Return the board with columns and tasks
    # to_dict(include_columns=True) recursively includes:
    # - Board details
    # - Each column in the board
    # - Each task in each column
    # This is a complete view of the board
    return jsonify({
        'board': board.to_dict(include_columns=True)
    }), 200  # 200 OK


# ============================================================
# ENDPOINT 4: UPDATE BOARD
# ============================================================
# PUT /api/boards/<board_id>
# Updates a board's properties

@boards_bp.route('/<int:board_id>', methods=['PUT'])
@jwt_required()  # This endpoint requires authentication
def update_board(board_id):
    """
    Update a board.
    
    SRS Reference:
        FR-2.2: Board management
    
    Request Body:
        {
            "name": "New Board Name",
            "description": "New description",
            "position": 1,
            "is_archived": true
        }
    
    How it works:
        1. Get the current user from the JWT token
        2. Get the board and check access
        3. Check if user has admin permission
        4. Update the fields that were provided
        5. Save to the database
        6. Return the updated board
    
    Returns:
        200: Board updated successfully
        401: User not authenticated
        403: User doesn't have permission
        404: Board not found
    """
    # Step 1: Get the current user from the token
    user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the board and check access
    board = get_board_or_404(board_id, user)
    
    # If board doesn't exist or user can't access it, return 404
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Step 3: Check if user has admin permission (FR-2.4)
    # has_permission(project, 'admin') checks if user is admin or owner
    if not user.has_permission(board.project, 'admin'):
        return jsonify({
            'error': 'You do not have permission to update this board'
        }), 403
    
    # Step 4: Get the request data
    data = request.get_json()
    
    # If no data was sent, return 400 Bad Request
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Step 5: Update fields that were provided
    # We only update fields that are sent in the request
    # This allows partial updates (PATCH-like behavior)
    
    name = data.get('name')
    if name is not None:
        board.name = name
        # Updated fields should also update the timestamp
        # Note: SQLAlchemy handles this with onupdate=datetime.utcnow
    
    description = data.get('description')
    if description is not None:
        board.description = description
    
    position = data.get('position')
    if position is not None:
        board.position = position
    
    # Handle archiving/unarchiving (FR-2.1)
    is_archived = data.get('is_archived')
    if is_archived is not None:
        if is_archived:
            board.archive()  # Soft delete
        else:
            board.unarchive()  # Restore from archive
    
    # Step 6: Save all changes to the database
    db.session.commit()
    
    # Step 7: Return the updated board
    return jsonify({
        'message': 'Board updated successfully',
        'board': board.to_dict(include_columns=True)
    }), 200  # 200 OK


# ============================================================
# ENDPOINT 5: ARCHIVE BOARD
# ============================================================
# DELETE /api/boards/<board_id>
# Archives (soft deletes) a board

@boards_bp.route('/<int:board_id>', methods=['DELETE'])
@jwt_required()  # This endpoint requires authentication
def archive_board(board_id):
    """
    Archive (soft delete) a board.
    
    SRS Reference:
        FR-2.2: Board management
        FR-2.4: "Only Owners/Admins can remove members or delete boards"
    
    How it works:
        1. Get the current user from the JWT token
        2. Get the board and check access
        3. Check if user has admin permission
        4. Archive the board (soft delete)
        5. Save to the database
        6. Return success
    
    Returns:
        200: Board archived successfully
        401: User not authenticated
        403: User doesn't have permission
        404: Board not found
    """
    # Step 1: Get the current user from the token
    user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the board and check access
    board = get_board_or_404(board_id, user)
    
    # If board doesn't exist or user can't access it, return 404
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Step 3: Check if user has admin permission (FR-2.4)
    if not user.has_permission(board.project, 'admin'):
        return jsonify({
            'error': 'You do not have permission to archive this board'
        }), 403
    
    # Step 4: Archive the board
    # archive() sets is_archived = True and updates updated_at
    board.archive()
    
    # Step 5: Save to the database
    db.session.commit()
    
    # Step 6: Return success
    return jsonify({
        'message': 'Board archived successfully'
    }), 200  # 200 OK


# ============================================================
# ENDPOINT 6: REORDER COLUMNS
# ============================================================
# POST /api/boards/<board_id>/reorder
# Reorders columns within a board

@boards_bp.route('/<int:board_id>/reorder', methods=['POST'])
@jwt_required()  # This endpoint requires authentication
def reorder_columns(board_id):
    """
    Reorder columns within a board.
    
    SRS Reference:
        FR-3.2: "Drag-and-drop reordering of tasks within and across columns"
    
    Request Body:
        {
            "column_order": [3, 1, 2]  # List of column IDs in desired order
        }
    
    How it works:
        1. Get the current user from the JWT token
        2. Get the board and check access
        3. Check if user has admin permission
        4. Get the new column order from the request
        5. Reorder the columns
        6. Save to the database
        7. Return success
    
    Returns:
        200: Columns reordered successfully
        400: Invalid request data
        401: User not authenticated
        403: User doesn't have permission
        404: Board not found
    """
    # Step 1: Get the current user from the token
    user = get_user_from_token()
    
    # If user doesn't exist, return 401 Unauthorized
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Step 2: Get the board and check access
    board = get_board_or_404(board_id, user)
    
    # If board doesn't exist or user can't access it, return 404
    if not board:
        return jsonify({'error': 'Board not found or access denied'}), 404
    
    # Step 3: Check if user has admin permission (FR-2.4)
    if not user.has_permission(board.project, 'admin'):
        return jsonify({
            'error': 'You do not have permission to reorder columns'
        }), 403
    
    # Step 4: Get the request data
    data = request.get_json()
    
    # If no data was sent, return 400 Bad Request
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get the new column order from the request
    column_order = data.get('column_order')
    
    # If column_order is missing, return 400 Bad Request
    if not column_order:
        return jsonify({'error': 'Column order is required'}), 400
    
    # Step 5: Reorder the columns
    # reorder_columns() is a method on the Board model
    # It updates the position of each column in the list
    board.reorder_columns(column_order)
    
    # Step 6: Save to the database
    db.session.commit()
    
    # Step 7: Return success
    return jsonify({
        'message': 'Columns reordered successfully'
    }), 200  # 200 OK
