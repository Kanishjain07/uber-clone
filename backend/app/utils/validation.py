"""
Validation utilities
"""
import re
from typing import Any


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip()))


def validate_password(password: str) -> bool:
    """
    Validate password strength
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if not password or not isinstance(password, str):
        return False

    if len(password) < 8:
        return False

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False

    # Check for at least one digit
    if not re.search(r'\d', password):
        return False

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone or not isinstance(phone, str):
        return False

    # Remove all non-digit characters except +
    cleaned_phone = re.sub(r'[^\d+]', '', phone.strip())

    # Check for valid patterns
    patterns = [
        r'^\+?1?\d{10}$',  # US format: +1234567890 or 1234567890
        r'^\+\d{10,15}$',  # International format: +123456789012
    ]

    return any(re.match(pattern, cleaned_phone) for pattern in patterns)


def validate_location(location: Any) -> bool:
    """Validate location coordinates"""
    if not isinstance(location, dict):
        return False

    required_keys = ['latitude', 'longitude']
    if not all(key in location for key in required_keys):
        return False

    try:
        lat = float(location['latitude'])
        lng = float(location['longitude'])

        # Check valid latitude range (-90 to 90)
        if not -90 <= lat <= 90:
            return False

        # Check valid longitude range (-180 to 180)
        if not -180 <= lng <= 180:
            return False

        return True

    except (ValueError, TypeError):
        return False


def validate_vehicle_type(vehicle_type: str) -> bool:
    """Validate vehicle type"""
    valid_types = [
        'standard', 'premium', 'luxury', 'suv', 'van',
        'motorcycle', 'bicycle', 'scooter'
    ]
    return vehicle_type.lower() in valid_types


def validate_payment_method(payment_method: str) -> bool:
    """Validate payment method"""
    valid_methods = ['cash', 'card', 'wallet', 'bank_transfer', 'digital_wallet']
    return payment_method.lower() in valid_methods


def validate_rating(rating: Any) -> bool:
    """Validate rating value (1-5)"""
    try:
        rating_value = float(rating)
        return 1.0 <= rating_value <= 5.0
    except (ValueError, TypeError):
        return False


def validate_currency_amount(amount: Any) -> bool:
    """Validate currency amount (positive number)"""
    try:
        amount_value = float(amount)
        return amount_value >= 0
    except (ValueError, TypeError):
        return False


def validate_distance(distance: Any) -> bool:
    """Validate distance value (positive number)"""
    try:
        distance_value = float(distance)
        return distance_value >= 0
    except (ValueError, TypeError):
        return False


def validate_duration(duration: Any) -> bool:
    """Validate duration in minutes (positive integer)"""
    try:
        duration_value = int(duration)
        return duration_value >= 0
    except (ValueError, TypeError):
        return False


def validate_license_plate(license_plate: str) -> bool:
    """Validate license plate format"""
    if not license_plate or not isinstance(license_plate, str):
        return False

    # Remove spaces and convert to uppercase
    plate = license_plate.replace(' ', '').upper()

    # Basic validation: 2-8 alphanumeric characters
    return bool(re.match(r'^[A-Z0-9]{2,8}$', plate))


def validate_year(year: Any) -> bool:
    """Validate vehicle year"""
    try:
        year_value = int(year)
        current_year = 2025  # Update this as needed
        return 1900 <= year_value <= current_year + 1
    except (ValueError, TypeError):
        return False


def sanitize_string(value: str, max_length: int = None) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        return ''

    # Strip whitespace
    sanitized = value.strip()

    # Remove any potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)

    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_ride_status(status: str) -> bool:
    """Validate ride status"""
    valid_statuses = [
        'requested', 'accepted', 'driver_arriving', 'driver_arrived',
        'in_progress', 'completed', 'cancelled', 'timeout'
    ]
    return status.lower() in valid_statuses


def validate_driver_status(status: str) -> bool:
    """Validate driver status"""
    valid_statuses = ['offline', 'online', 'busy', 'break']
    return status.lower() in valid_statuses


def validate_notification_type(notification_type: str) -> bool:
    """Validate notification type"""
    valid_types = [
        'ride_request', 'ride_accepted', 'ride_cancelled', 'ride_completed',
        'driver_assigned', 'driver_arriving', 'driver_arrived',
        'payment_completed', 'promotion', 'system_update'
    ]
    return notification_type.lower() in valid_types