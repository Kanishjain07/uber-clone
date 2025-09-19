"""
Authentication API endpoints
"""
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

from app.models.user import User
from app.models.rider import Rider
from app.models.driver import Driver
from app.utils.validation import validate_email, validate_password, validate_phone
from app.utils.decorators import handle_errors

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@handle_errors
def register():
    """User registration endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'user_type']
    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'missing_fields': missing_fields
        }), 400

    # Validate data
    validation_errors = {}

    # Email validation
    if not validate_email(data['email']):
        validation_errors['email'] = 'Invalid email format'

    # Password validation
    if not validate_password(data['password']):
        validation_errors['password'] = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'

    # Phone validation
    if not validate_phone(data['phone']):
        validation_errors['phone'] = 'Invalid phone number format'

    # User type validation
    if data['user_type'] not in ['rider', 'driver']:
        validation_errors['user_type'] = 'User type must be either "rider" or "driver"'

    # Driver-specific validation
    if data['user_type'] == 'driver':
        if not data.get('vehicle_info'):
            validation_errors['vehicle_info'] = 'Vehicle information is required for drivers'
        else:
            vehicle_required = ['make', 'model', 'year', 'license_plate', 'vehicle_type']
            missing_vehicle = [field for field in vehicle_required if not data['vehicle_info'].get(field)]
            if missing_vehicle:
                validation_errors['vehicle_info'] = f'Missing vehicle fields: {", ".join(missing_vehicle)}'

    if validation_errors:
        return jsonify({'error': 'Validation failed', 'details': validation_errors}), 422

    # Check for existing users
    existing_user = User.find_by_email(data['email'])
    if existing_user:
        return jsonify({'error': 'User with this email already exists'}), 409

    existing_phone = User.find_by_phone(data['phone'])
    if existing_phone:
        return jsonify({'error': 'User with this phone number already exists'}), 409

    try:
        # Create user
        user_data = {
            'email': data['email'].lower().strip(),
            'password': data['password'],
            'first_name': data['first_name'].strip(),
            'last_name': data['last_name'].strip(),
            'phone': data['phone'].strip(),
            'user_type': data['user_type'],
            'profile_picture': data.get('profile_picture'),
            'date_of_birth': data.get('date_of_birth'),
            'gender': data.get('gender'),
            'address': data.get('address'),
            'emergency_contact': data.get('emergency_contact')
        }

        user = User.create_user(user_data)

        # Create profile based on user type
        if data['user_type'] == 'rider':
            rider_data = {
                'preferred_payment_method': data.get('preferred_payment_method', 'card')
            }
            Rider.create_rider(user._id, rider_data)

        else:  # driver
            driver_data = {
                'vehicle_info': data['vehicle_info'],
                'driver_license': data.get('driver_license', ''),
                'insurance_info': data.get('insurance_info', ''),
                'license_expiry': data.get('license_expiry'),
                'insurance_expiry': data.get('insurance_expiry'),
                'vehicle_registration_expiry': data.get('vehicle_registration_expiry')
            }
            Driver.create_driver(user._id, driver_data)

        # Generate tokens
        access_token = create_access_token(
            identity=user._id,
            additional_claims={'user_type': user.user_type}
        )
        refresh_token = create_refresh_token(identity=user._id)

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_json(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201

    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
@handle_errors
def login():
    """User login endpoint"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    # Find user
    user = User.find_by_email(email)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    # Check if user is active
    if not getattr(user, 'is_active', True):
        return jsonify({'error': 'Account is deactivated'}), 401

    # Verify password
    if not user.verify_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Update last login
    user.update_last_login()

    # Generate tokens
    access_token = create_access_token(
        identity=user._id,
        additional_claims={'user_type': user.user_type}
    )
    refresh_token = create_refresh_token(identity=user._id)

    return jsonify({
        'message': 'Login successful',
        'user': user.to_json(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@handle_errors
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()

    # Verify user still exists and is active
    user = User.find_by_id(current_user_id)
    if not user or not getattr(user, 'is_active', True):
        return jsonify({'error': 'User not found or inactive'}), 401

    # Generate new access token
    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims={'user_type': user.user_type}
    )

    return jsonify({
        'access_token': new_access_token
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@handle_errors
def logout():
    """Logout endpoint"""
    # In a real application, you might want to blacklist the token
    # For now, we'll just return a success message
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
@handle_errors
def get_profile():
    """Get user profile"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    user_type = claims.get('user_type')

    user = User.find_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile_data = user.to_json()

    # Get additional profile data based on user type
    if user_type == 'rider':
        rider = Rider.find_by_user_id(current_user_id)
        if rider:
            profile_data['rider_profile'] = rider.to_json()

    elif user_type == 'driver':
        driver = Driver.find_by_user_id(current_user_id)
        if driver:
            profile_data['driver_profile'] = driver.to_json()

    return jsonify({'user': profile_data}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
@handle_errors
def update_profile():
    """Update user profile"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user = User.find_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Update user profile
    if user.update_profile(data):
        return jsonify({'message': 'Profile updated successfully'}), 200
    else:
        return jsonify({'error': 'No valid fields to update'}), 400


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@handle_errors
def change_password():
    """Change user password"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400

    # Validate new password
    if not validate_password(new_password):
        return jsonify({
            'error': 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'
        }), 422

    user = User.find_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Verify current password
    if not user.verify_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401

    # Change password
    if user.change_password(new_password):
        return jsonify({'message': 'Password changed successfully'}), 200
    else:
        return jsonify({'error': 'Failed to change password'}), 500


@auth_bp.route('/verify-email', methods=['POST'])
@jwt_required()
@handle_errors
def verify_email():
    """Verify email address"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    verification_code = data.get('verification_code') if data else None

    # In a real application, you would:
    # 1. Check the verification code against stored code
    # 2. Verify the code hasn't expired
    # 3. Mark email as verified

    user = User.find_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # For now, just mark as verified
    if user.verify_email():
        return jsonify({'message': 'Email verified successfully'}), 200
    else:
        return jsonify({'error': 'Failed to verify email'}), 500


@auth_bp.route('/verify-phone', methods=['POST'])
@jwt_required()
@handle_errors
def verify_phone():
    """Verify phone number"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    verification_code = data.get('verification_code') if data else None

    # In a real application, you would:
    # 1. Check the verification code against stored code
    # 2. Verify the code hasn't expired
    # 3. Mark phone as verified

    user = User.find_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # For now, just mark as verified
    if user.verify_phone():
        return jsonify({'message': 'Phone verified successfully'}), 200
    else:
        return jsonify({'error': 'Failed to verify phone'}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@handle_errors
def forgot_password():
    """Initiate password reset"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').lower().strip()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = User.find_by_email(email)

    # Always return success to prevent email enumeration
    # In a real application, you would:
    # 1. Generate a password reset token
    # 2. Send reset email if user exists
    # 3. Store token with expiration

    return jsonify({
        'message': 'If an account with that email exists, a password reset link has been sent'
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
@handle_errors
def reset_password():
    """Reset password with token"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    reset_token = data.get('reset_token')
    new_password = data.get('new_password')

    if not reset_token or not new_password:
        return jsonify({'error': 'Reset token and new password are required'}), 400

    # Validate new password
    if not validate_password(new_password):
        return jsonify({
            'error': 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'
        }), 422

    # In a real application, you would:
    # 1. Validate the reset token
    # 2. Check if token hasn't expired
    # 3. Find user by token
    # 4. Update password

    return jsonify({'message': 'Password reset functionality not implemented'}), 501


@auth_bp.route('/deactivate', methods=['POST'])
@jwt_required()
@handle_errors
def deactivate_account():
    """Deactivate user account"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    password = data.get('password') if data else None

    if not password:
        return jsonify({'error': 'Password confirmation required'}), 400

    user = User.find_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Verify password before deactivation
    if not user.verify_password(password):
        return jsonify({'error': 'Incorrect password'}), 401

    if user.deactivate():
        return jsonify({'message': 'Account deactivated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to deactivate account'}), 500