import re
import hashlib
import secrets
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_password(password):
    """
    Validate password strength
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False
    
    # Check for number
    if not re.search(r'\d', password):
        return False
    
    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True

def validate_email(email):
    """
    Validate email format using regex
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """
    Validate phone number format
    Accepts formats like:
    - +1234567890
    - 1234567890
    - (123) 456-7890
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False
    
    return True

def generate_secure_token(length=32):
    """
    Generate a secure random token
    """
    return secrets.token_urlsafe(length)

def hash_data(data):
    """
    Hash data using SHA-256
    """
    return hashlib.sha256(data.encode()).hexdigest()

def validate_location(location):
    """
    Validate location coordinates
    """
    if not isinstance(location, dict):
        return False
    
    if 'lat' not in location or 'lng' not in location:
        return False
    
    try:
        lat = float(location['lat'])
        lng = float(location['lng'])
        
        # Check if coordinates are within valid ranges
        if not (-90 <= lat <= 90):
            return False
        
        if not (-180 <= lng <= 180):
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False

def sanitize_input(text):
    """
    Basic input sanitization
    Remove potentially dangerous characters
    """
    if not text:
        return text
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove other potentially dangerous patterns
    dangerous_patterns = [
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'onclick=',
        r'onmouseover='
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def validate_ride_data(ride_data):
    """
    Validate ride request data
    """
    required_fields = ['pickup', 'destination', 'ride_type']
    
    for field in required_fields:
        if field not in ride_data:
            return False, f"Missing required field: {field}"
    
    # Validate locations
    if not validate_location(ride_data['pickup']):
        return False, "Invalid pickup location"
    
    if not validate_location(ride_data['destination']):
        return False, "Invalid destination location"
    
    # Validate ride type
    valid_ride_types = ['economy', 'comfort', 'premium', 'xl']
    if ride_data['ride_type'] not in valid_ride_types:
        return False, "Invalid ride type"
    
    return True, "Valid ride data"

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    import math
    
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def calculate_distance_between_locations(location1, location2):
    """
    Calculate distance between two location objects
    Each location should have 'lat' and 'lng' keys
    
    Args:
        location1 (dict): First location with 'lat' and 'lng' keys
        location2 (dict): Second location with 'lat' and 'lng' keys
    
    Returns:
        float: Distance in kilometers
    """
    try:
        if not location1 or not location2:
            return 0.0
        
        lat1 = location1.get('lat', 0)
        lon1 = location1.get('lng', 0)
        lat2 = location2.get('lat', 0)
        lon2 = location2.get('lng', 0)
        
        return calculate_distance(lat1, lon1, lat2, lon2)
    except Exception as e:
        logger.error(f"Error calculating distance between locations: {e}")
        return 0.0

def estimate_ride_fare(distance_km, ride_type, base_fare=2.50, per_km_rate=1.50):
    """
    Estimate ride fare based on distance and ride type
    """
    # Base fare + distance-based fare
    distance_fare = distance_km * per_km_rate
    
    # Ride type multipliers
    multipliers = {
        'economy': 1.0,
        'comfort': 1.3,
        'premium': 1.8,
        'xl': 2.0
    }
    
    multiplier = multipliers.get(ride_type, 1.0)
    
    total_fare = (base_fare + distance_fare) * multiplier
    
    return round(total_fare, 2)

def generate_otp(length=6):
    """
    Generate a numeric OTP (One-Time Password)
    """
    return ''.join(secrets.choice('0123456789') for _ in range(length))

def is_token_expired(token_timestamp, expiry_hours=24):
    """
    Check if a token is expired
    """
    if not token_timestamp:
        return True
    
    try:
        token_time = datetime.fromisoformat(token_timestamp.replace('Z', '+00:00'))
        expiry_time = token_time + timedelta(hours=expiry_hours)
        
        return datetime.utcnow() > expiry_time
        
    except (ValueError, TypeError):
        return True

def validate_vehicle_info(vehicle_info):
    """
    Validate vehicle information for drivers
    """
    if not isinstance(vehicle_info, dict):
        return False
    
    required_fields = ['type', 'model', 'year', 'color', 'license_plate']
    
    for field in required_fields:
        if field not in vehicle_info:
            return False
    
    # Validate vehicle type
    valid_types = ['sedan', 'suv', 'luxury', 'xl', 'motorcycle']
    if vehicle_info['type'] not in valid_types:
        return False
    
    # Validate year (reasonable range)
    try:
        year = int(vehicle_info['year'])
        if year < 1990 or year > datetime.now().year + 1:
            return False
    except (ValueError, TypeError):
        return False
    
    # Validate license plate format (basic check)
    if not vehicle_info['license_plate'] or len(vehicle_info['license_plate']) < 3:
        return False
    
    return True
