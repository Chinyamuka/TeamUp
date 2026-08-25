"""
Authentication API Routes

This module handles all authentication endpoints for TeamUp.

SRS References:
- FR-1.1: Registration with email + password
- FR-1.2: JWT access and refresh tokens on login
- FR-1.3: Role-based access control
- FR-1.4: Token revocation on logout
- FR-1.5: Password reset via signed link
- NFR-11: Passwords hashed with bcrypt, cost ≥ 12
- Section 7.3: Authentication flow

Endpoints:
    POST /api/auth/register - Create new account
    POST /api/auth/login - Login, get tokens
    POST /api/auth/refresh - Refresh access token
    POST /api/auth/logout - Logout, revoke tokens
    POST /api/auth/password-reset - Request password reset
    POST /api/auth/password-reset/confirm - Confirm password reset
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    unset_jwt_cookies
)
from datetime import timedelta, datetime
import re

from app.extensions import db, redis_client
from app.models import User

# ============================================================
# CREATE BLUEPRINT
# ============================================================
# A blueprint groups related routes together
# url_prefix='/api/auth' means all routes start with /api/auth
# 
# Example: /api/auth/register, /api/auth/login
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_email(email):
    """
    Validate email format using regex.
    
    Args:
        email: Email string to validate
    
    Returns:
        bool: True if valid, False otherwise
    
    Example:
        validate_email('user@example.com')  # True
        validate_email('invalid-email')     # False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength.
    
    SRS Reference: NFR-11 - Security requirements
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Returns:
        tuple: (is_valid, error_message)
    
    Example:
        validate_password('Weak')        # (False, "at least 8 characters")
        validate_password('StrongPass1') # (True, "Password is valid")
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"


def is_token_revoked(jwt_payload):
    """
    Check if a JWT token has been revoked.
    
    Args:
        jwt_payload: The JWT payload containing the jti (JWT ID)
    
    Returns:
        bool: True if revoked, False otherwise
    
    SRS Reference:
        FR-1.4: "System shall invalidate refresh tokens on logout"
    
    This is used by Flask-JWT-Extended to check if a token is valid.
    """
    jti = jwt_payload['jti']
    token_key = f'revoked_token:{jti}'
    return redis_client.get(token_key) is not None


# ============================================================
# REGISTER ENDPOINT - FR-1.1
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    SRS Reference:
        FR-1.1: "System shall allow registration with email + password"
        NFR-11: "Passwords hashed with bcrypt, cost ≥ 12"
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "full_name": "John Doe"
        }
    
    Returns:
        201: User created successfully
        400: Validation error
        409: Email already exists
    
    Example Response (201):
        {
            "message": "User registered successfully",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "created_at": "2026-08-24T14:30:00"
            }
        }
    """
    # 1. Get request data
    data = request.get_json()
    
    # 2. Check if data was provided
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # 3. Extract fields
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    # 4. Validate required fields
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    if not full_name:
        return jsonify({'error': 'Full name is required'}), 400
    
    # 5. Validate email format
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # 6. Validate password strength
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # 7. Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 409
    
    # 8. Create new user
    # The password setter will automatically hash it (NFR-11)
    user = User(
        email=email,
        full_name=full_name
    )
    user.password = password  # This triggers the setter with bcrypt
    
    # 9. Save to database
    db.session.add(user)
    db.session.commit()
    
    # 10. Return success response
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


# ============================================================
# LOGIN ENDPOINT - FR-1.2
# ============================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and issue JWT tokens.
    
    SRS Reference:
        FR-1.2: "Issue a short-lived JWT access token and a longer-lived refresh token"
        Section 7.3: "Authentication flow"
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    
    Returns:
        200: Login successful with tokens
        401: Invalid credentials
    
    Example Response (200):
        {
            "message": "Login successful",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe"
            },
            "tokens": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }
    """
    # 1. Get request data
    data = request.get_json()
    
    # 2. Validate input
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    # 3. Find user by email
    user = User.query.filter_by(email=email).first()
    
    # 4. Check if user exists and password matches
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # 5. Check if user is active
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401
    
    # 6. Create JWT tokens
    # access_token: Short-lived (15 minutes as per SRS Section 7.3)
    # refresh_token: Longer-lived (7 days as per SRS Section 7.3)
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(seconds=900)  # 15 minutes
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(seconds=604800)  # 7 days
    )
    
    # 7. Store refresh token in Redis for tracking (FR-1.4)
    # This allows us to revoke tokens on logout
    from flask_jwt_extended import decode_token
    decoded_token = decode_token(refresh_token)
    jti = decoded_token['jti']  # JWT ID
    
    # Store with TTL = token lifetime
    redis_client.set(
        f'refresh_token:{jti}',
        str(user.id),
        ex=604800  # 7 days
    )
    
    # 8. Return success with tokens
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'tokens': {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    }), 200


# ============================================================
# REFRESH ENDPOINT - FR-1.2
# ============================================================

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh the access token using a refresh token.
    
    SRS Reference:
        FR-1.2: "Exchange refresh token for new access token"
        Section 7.3: "When access token expires, call /api/auth/refresh"
    
    Request Body:
        None (uses refresh token from Authorization header)
    
    Returns:
        200: New access token
        401: Invalid or expired refresh token
    
    Example Response (200):
        {
            "message": "Token refreshed successfully",
            "access_token": "eyJhbGciOiJIUzI1NiIs..."
        }
    """
    # 1. Get the current user's identity from the refresh token
    user_id = get_jwt_identity()
    
    # 2. Check if the refresh token has been revoked (FR-1.4)
    from flask_jwt_extended import get_jwt
    jwt_data = get_jwt()
    jti = jwt_data['jti']
    
    if redis_client.get(f'revoked_token:{jti}'):
        return jsonify({'error': 'Token has been revoked'}), 401
    
    # 3. Verify user still exists and is active
    user = User.query.get(int(user_id))
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401
    
    # 4. Create new access token
    new_access_token = create_access_token(
        identity=user_id,
        expires_delta=timedelta(seconds=900)  # 15 minutes
    )
    
    # 5. Return new access token
    return jsonify({
        'message': 'Token refreshed successfully',
        'access_token': new_access_token
    }), 200


# ============================================================
# LOGOUT ENDPOINT - FR-1.4
# ============================================================

@auth_bp.route('/logout', methods=['POST'])
@jwt_required(refresh=True)
def logout():
    """
    Logout user and revoke refresh token.
    
    SRS Reference:
        FR-1.4: "System shall invalidate refresh tokens on logout"
        Section 7.3: "Logout adds the refresh token's ID to the Redis denylist"
    
    Request Body:
        None (uses refresh token from Authorization header)
    
    Returns:
        200: Logout successful
        401: Invalid token
    
    Example Response (200):
        {
            "message": "Logged out successfully"
        }
    """
    # 1. Get the JWT data
    from flask_jwt_extended import get_jwt
    jwt_data = get_jwt()
    jti = jwt_data['jti']  # JWT ID
    user_id = get_jwt_identity()
    
    # 2. Get token expiry time
    exp = jwt_data.get('exp', datetime.utcnow().timestamp() + 604800)
    ttl = int(exp - datetime.utcnow().timestamp())
    
    # 3. Add token to denylist (FR-1.4)
    # This prevents the token from being used again
    redis_client.set(
        f'revoked_token:{jti}',
        user_id,
        ex=ttl if ttl > 0 else 3600  # Minimum 1 hour
    )
    
    # 4. Remove from refresh token tracking
    redis_client.delete(f'refresh_token:{jti}')
    
    # 5. Return success
    return jsonify({'message': 'Logged out successfully'}), 200


# ============================================================
# PASSWORD RESET REQUEST ENDPOINT - FR-1.5
# ============================================================

@auth_bp.route('/password-reset', methods=['POST'])
def request_password_reset():
    """
    Request a password reset email.
    
    SRS Reference:
        FR-1.5: "Support password reset via time-limited signed link"
    
    Request Body:
        {
            "email": "user@example.com"
        }
    
    Returns:
        200: Reset email sent (or user not found)
        400: Email required
    
    Note: This endpoint always returns 200 even if the email doesn't exist
    for security reasons (prevents email enumeration).
    """
    # 1. Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # 2. Find user
    user = User.query.filter_by(email=email).first()
    
    # 3. If user exists, generate reset token
    if user:
        # Generate a signed JWT token for password reset
        # This token has a short lifetime (15 minutes)
        reset_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(minutes=15),
            additional_claims={'type': 'password_reset'}
        )
        
        # In production, send email with reset link:
        # reset_link = f"{base_url}/reset-password?token={reset_token}"
        # send_email(user.email, "Password Reset", reset_link)
        
        # For now, log the token (development only)
        current_app.logger.info(f"Password reset token for {email}: {reset_token}")
        
        # Store token in Redis with expiry
        redis_client.set(
            f'password_reset:{user.id}',
            reset_token,
            ex=900  # 15 minutes
        )
    
    # 4. Always return success (prevents email enumeration)
    return jsonify({
        'message': 'If an account exists with this email, a reset link has been sent'
    }), 200


# ============================================================
# CONFIRM PASSWORD RESET ENDPOINT - FR-1.5
# ============================================================

@auth_bp.route('/password-reset/confirm', methods=['POST'])
def confirm_password_reset():
    """
    Confirm password reset with token and new password.
    
    SRS Reference:
        FR-1.5: "Support password reset via time-limited signed link"
    
    Request Body:
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "new_password": "NewSecurePass123"
        }
    
    Returns:
        200: Password reset successful
        400: Invalid request
        401: Invalid or expired token
    """
    # 1. Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token:
        return jsonify({'error': 'Reset token is required'}), 400
    if not new_password:
        return jsonify({'error': 'New password is required'}), 400
    
    # 2. Validate new password strength
    is_valid, message = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # 3. Verify the token
    from flask_jwt_extended import decode_token
    try:
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']
        token_type = decoded_token.get('type')
        
        # Check if this is a password reset token
        if token_type != 'password_reset':
            return jsonify({'error': 'Invalid token type'}), 401
        
        # Check if token exists in Redis
        stored_token = redis_client.get(f'password_reset:{user_id}')
        if stored_token != token:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
    except Exception as e:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    # 4. Find user
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 5. Update password
    user.password = new_password  # Auto-hashed
    user.updated_at = datetime.utcnow()
    
    # 6. Delete the reset token from Redis
    redis_client.delete(f'password_reset:{user_id}')
    
    # 7. Save changes
    db.session.commit()
    
    # 8. Return success
    return jsonify({'message': 'Password reset successful'}), 200


# ============================================================
# GET CURRENT USER ENDPOINT
# ============================================================

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get the current authenticated user.
    
    Returns:
        200: User details
        401: Not authenticated
    
    Example Response (200):
        {
            "user": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "created_at": "2026-08-24T14:30:00"
            }
        }
    """
    # 1. Get user ID from JWT
    user_id = get_jwt_identity()
    
    # 2. Find user
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 3. Return user data
    return jsonify({
        'user': user.to_dict()
    }), 200
