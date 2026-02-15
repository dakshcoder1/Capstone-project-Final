# =============================================================================
# Part 6: Authentication Helpers (with @token_required decorator)
# =============================================================================

import jwt
from datetime import datetime, timedelta
# Note: We don't need 'wraps' anymore since we're not using decorators
from flask import request, jsonify
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
SECRET_KEY = "your-secret-key-change-in-production"
TOKEN_EXPIRATION_HOURS = 24


# =============================================================================
# PASSWORD FUNCTIONS
# =============================================================================

def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


# =============================================================================
# JWT TOKEN FUNCTIONS
# =============================================================================

def create_token(user_id, is_admin=False):
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    
    except:
        return None


# =============================================================================
# GET CURRENT USER (Helper Function)
# =============================================================================
# This function checks the token and returns the logged-in user.
# We use a simple function instead of a decorator for easier understanding.
#
# Returns:
#   - (user, None) if token is valid
#   - (None, error_response) if token is invalid

def get_current_user():
    """
    Validates JWT token and returns current user.

    How it works:
    1. Checks for Authorization header
    2. Extracts and validates the JWT token
    3. Fetches user from database
    4. Returns (user, None) or (None, error_response)
    """

    # ✅ CHANGE 1: Use request.headers.get() (safer than direct indexing)
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None, (jsonify({'error': 'Token is missing'}), 401)

    print("========================================")
    print("Authorization header found.")
    print(request.headers)
    print(auth_header)
    print("\n\n")

    # Step 2: Extract token from "Bearer <token>"
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({'error': 'Invalid token format'}), 401)

    print("Split with (' ')")
    print(auth_header.split(' '))
    print("\n\n")

    # ✅ CHANGE 2: safer split (prevents index error)
    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None, (jsonify({'error': 'Invalid token format'}), 401)

    token = parts[1]

    # Step 3: Decode and validate token
    data = decode_token(token)

    print("Decoded token data:")
    print(data)

    if not data:
        return None, (jsonify({'error': 'Token is invalid or expired'}), 401)

    # Step 4: Get user from database
    current_user = User.query.get(data['user_id'])
    if not current_user:
        return None, (jsonify({'error': 'User not found'}), 401)

    # ✅ SUCCESS: Always return EXACTLY 2 values
    return current_user, None

# =============================================================================
# GET ADMIN USER (Helper Function)
# =============================================================================
# Same as get_current_user but also checks if user is admin

def get_admin_user():
    """
    Validates JWT token and returns current user IF they are admin.
    Returns: (user, None) on success, (None, error_response) on failure
    """
    # First, get the current user
    current_user, error = get_current_user()
    if error:
        return None, error

    # Then check if they are admin
    if not current_user.is_admin:
        return None, (jsonify({'error': 'Admin access required'}), 403)

    return current_user, None
