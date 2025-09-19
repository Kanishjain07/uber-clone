from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime, timedelta
from models.db import get_db, create_user, find_user_by_email, find_user_by_id
from utils.security import validate_password, validate_email
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'user_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if not validate_password(data['password']):
            return jsonify({'error': 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'}), 400
        
        # Validate phone format
        if not re.match(r'^\+?1?\d{9,15}$', data['phone']):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Validate user type
        if data['user_type'] not in ['rider', 'driver']:
            return jsonify({'error': 'Invalid user type. Must be "rider" or "driver"'}), 400
        
        # Check if user already exists
        existing_user = find_user_by_email(data['email'])
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409

        # Check if phone number already exists
        db = get_db()
        if db is None:
            raise Exception("Database not initialized")

        existing_phone = db.users.find_one({"phone": data['phone']})
        if existing_phone:
            return jsonify({'error': 'User with this phone number already exists'}), 409
        
        # Hash password
        hashed_password = generate_password_hash(data['password'])
        
        # Create user data
        user_data = {
            'email': data['email'].lower(),
            'password': hashed_password,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data['phone'],
            'user_type': data['user_type'],
            'is_active': True,
            'email_verified': False,
            'phone_verified': False
        }
        
        # Add additional fields for drivers
        if data['user_type'] == 'driver':
            if not data.get('vehicle_info'):
                return jsonify({'error': 'Vehicle information required for drivers'}), 400
            
            user_data['vehicle_info'] = data['vehicle_info']
            user_data['driver_license'] = data.get('driver_license', '')
            user_data['insurance_info'] = data.get('insurance_info', '')
            user_data['driver_status'] = 'pending_verification'
        
        # Create user in database
        new_user = create_user(user_data)
        
        # Create user profile in appropriate collection
        db = get_db()
        if db is None:
            raise Exception("Database not initialized")

        if data['user_type'] == 'rider':
            rider_data = {
                'user_id': new_user['_id'],
                'current_location': None,
                'preferred_payment_method': data.get('preferred_payment_method', 'card'),
                'rating': 5.0,
                'total_rides': 0,
                'created_at': datetime.utcnow()
            }
            db.riders.insert_one(rider_data)
        else:
            driver_data = {
                'user_id': new_user['_id'],
                'current_location': None,
                'vehicle_type': data['vehicle_info'].get('type', 'sedan'),
                'rating': 5.0,
                'total_rides': 0,
                'earnings': 0.0,
                'is_online': False,
                'current_ride_id': None,
                'created_at': datetime.utcnow()
            }
            db.drivers.insert_one(driver_data)
        
        # Generate tokens
        access_token = create_access_token(identity=new_user['_id'])
        refresh_token = create_refresh_token(identity=new_user['_id'])
        
        # Remove password from response
        user_response = {k: v for k, v in new_user.items() if k != 'password'}
        
        logger.info(f"New user registered: {new_user['email']} ({new_user['user_type']})")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user_response,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = find_user_by_email(data['email'].lower())
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is active
        if not user.get('is_active', True):
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Verify password
        if not check_password_hash(user['password'], data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate tokens
        access_token = create_access_token(identity=str(user['_id']))
        refresh_token = create_refresh_token(identity=str(user['_id']))
        
        # Update last login
        db = get_db()
        if db is None:
            raise Exception("Database not initialized")

        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Remove password from response
        user_response = {k: v for k, v in user.items() if k != 'password'}
        
        logger.info(f"User logged in: {user['email']}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user_response,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token endpoint"""
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile endpoint"""
    try:
        current_user_id = get_jwt_identity()
        user = find_user_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Remove password from response
        user_response = {k: v for k, v in user.items() if k != 'password'}
        
        return jsonify({
            'user': user_response
        }), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile endpoint"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Fields that can be updated
        allowed_fields = ['first_name', 'last_name', 'phone', 'profile_picture']
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update user in database
        db = get_db()
        if db is None:
            raise Exception("Database not initialized")

        result = db.users.update_one(
            {'_id': current_user_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Profile updated for user: {current_user_id}")
            return jsonify({'message': 'Profile updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made'}), 200
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password endpoint"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Validate new password strength
        if not validate_password(data['new_password']):
            return jsonify({'error': 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'}), 400
        
        # Get user and verify current password
        user = find_user_by_id(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not check_password_hash(user['password'], data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Hash new password and update
        new_hashed_password = generate_password_hash(data['new_password'])
        db = get_db()
        if db is None:
            raise Exception("Database not initialized")

        result = db.users.update_one(
            {'_id': current_user_id},
            {'$set': {'password': new_hashed_password}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Password changed for user: {current_user_id}")
            return jsonify({'message': 'Password changed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update password'}), 500
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint (client should discard tokens)"""
    try:
        # In a real application, you might want to blacklist the token
        # For now, we'll just return a success message
        logger.info(f"User logged out: {get_jwt_identity()}")
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Email verification endpoint"""
    # This would typically involve sending a verification email
    # For now, we'll just return a placeholder response
    return jsonify({'message': 'Email verification endpoint - implementation needed'}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Forgot password endpoint"""
    # This would typically involve sending a reset email
    # For now, we'll just return a placeholder response
    return jsonify({'message': 'Forgot password endpoint - implementation needed'}), 200
