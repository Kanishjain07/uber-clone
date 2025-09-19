"""
User model
"""
from datetime import datetime
from typing import Dict, Any, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from .base import BaseModel


class User(BaseModel):
    """User model for both riders and drivers"""

    collection_name = 'users'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def create_user(cls, user_data: Dict[str, Any]) -> 'User':
        """Create a new user with hashed password"""
        # Hash password before storing
        if 'password' in user_data:
            user_data['password'] = generate_password_hash(user_data['password'])

        # Set default values
        user_data.setdefault('is_active', True)
        user_data.setdefault('email_verified', False)
        user_data.setdefault('phone_verified', False)
        user_data.setdefault('profile_picture', None)
        user_data.setdefault('last_login', None)

        return cls.create(user_data)

    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email address"""
        return cls.find_one({'email': email.lower()})

    @classmethod
    def find_by_phone(cls, phone: str) -> Optional['User']:
        """Find user by phone number"""
        return cls.find_one({'phone': phone})

    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        if not hasattr(self, 'password') or not self.password:
            return False
        return check_password_hash(self.password, password)

    def change_password(self, new_password: str) -> bool:
        """Change user password"""
        hashed_password = generate_password_hash(new_password)
        return self.update({'password': hashed_password})

    def update_last_login(self) -> bool:
        """Update last login timestamp"""
        return self.update({'last_login': datetime.utcnow()})

    def deactivate(self) -> bool:
        """Deactivate user account"""
        return self.update({'is_active': False})

    def activate(self) -> bool:
        """Activate user account"""
        return self.update({'is_active': True})

    def verify_email(self) -> bool:
        """Mark email as verified"""
        return self.update({'email_verified': True})

    def verify_phone(self) -> bool:
        """Mark phone as verified"""
        return self.update({'phone_verified': True})

    def update_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information"""
        # Filter allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'profile_picture',
            'date_of_birth', 'gender', 'address', 'emergency_contact'
        ]

        update_data = {
            key: value for key, value in profile_data.items()
            if key in allowed_fields
        }

        if not update_data:
            return False

        return self.update(update_data)

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON, excluding sensitive data"""
        data = super().to_json()

        # Remove sensitive fields
        sensitive_fields = ['password']
        for field in sensitive_fields:
            data.pop(field, None)

        return data

    def get_full_name(self) -> str:
        """Get user's full name"""
        first = getattr(self, 'first_name', '')
        last = getattr(self, 'last_name', '')
        return f"{first} {last}".strip()

    def is_rider(self) -> bool:
        """Check if user is a rider"""
        return getattr(self, 'user_type', '') == 'rider'

    def is_driver(self) -> bool:
        """Check if user is a driver"""
        return getattr(self, 'user_type', '') == 'driver'

    @classmethod
    def get_active_users(cls, user_type: Optional[str] = None) -> list:
        """Get all active users, optionally filtered by type"""
        filter_dict = {'is_active': True}
        if user_type:
            filter_dict['user_type'] = user_type

        return cls.find_many(filter_dict)

    @classmethod
    def search_users(cls, query: str, user_type: Optional[str] = None) -> list:
        """Search users by name, email, or phone"""
        filter_dict = {
            '$and': [
                {'is_active': True},
                {
                    '$or': [
                        {'first_name': {'$regex': query, '$options': 'i'}},
                        {'last_name': {'$regex': query, '$options': 'i'}},
                        {'email': {'$regex': query, '$options': 'i'}},
                        {'phone': {'$regex': query, '$options': 'i'}}
                    ]
                }
            ]
        }

        if user_type:
            filter_dict['$and'].append({'user_type': user_type})

        return cls.find_many(filter_dict)

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Validate user data and return errors if any"""
        errors = {}

        # Required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'user_type']
        for field in required_fields:
            if not data.get(field):
                errors[field] = f'{field.replace("_", " ").title()} is required'

        # Email validation
        email = data.get('email', '')
        if email and '@' not in email:
            errors['email'] = 'Invalid email format'

        # Phone validation
        phone = data.get('phone', '')
        if phone and len(phone) < 10:
            errors['phone'] = 'Phone number must be at least 10 digits'

        # User type validation
        user_type = data.get('user_type', '')
        if user_type and user_type not in ['rider', 'driver']:
            errors['user_type'] = 'User type must be either "rider" or "driver"'

        # Check for existing email and phone
        if data.get('email'):
            existing_user = self.find_by_email(data['email'])
            if existing_user and (not hasattr(self, '_id') or existing_user._id != self._id):
                errors['email'] = 'Email already exists'

        if data.get('phone'):
            existing_phone = self.find_by_phone(data['phone'])
            if existing_phone and (not hasattr(self, '_id') or existing_phone._id != self._id):
                errors['phone'] = 'Phone number already exists'

        return errors