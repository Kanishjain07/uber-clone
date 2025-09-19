"""
Configuration settings for Uber Clone application
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'uber-clone-secret-key-dev')
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'uber-clone-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'

    # Database
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'uber_clone')

    # Redis (for caching and sessions)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # API Configuration
    API_TITLE = 'Uber Clone API'
    API_VERSION = 'v1'
    API_PREFIX = '/api/v1'

    # Google Maps
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

    # Pricing Configuration
    BASE_FARE = float(os.getenv('BASE_FARE', '2.50'))
    COST_PER_KM = float(os.getenv('COST_PER_KM', '1.20'))
    COST_PER_MINUTE = float(os.getenv('COST_PER_MINUTE', '0.25'))

    # Driver Matching
    MAX_SEARCH_RADIUS_KM = float(os.getenv('MAX_SEARCH_RADIUS_KM', '10.0'))
    DRIVER_ASSIGNMENT_TIMEOUT = int(os.getenv('DRIVER_ASSIGNMENT_TIMEOUT', '300'))  # 5 minutes

    # Real-time Updates
    LOCATION_UPDATE_INTERVAL = int(os.getenv('LOCATION_UPDATE_INTERVAL', '10'))  # seconds

    # Security
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', '12'))

    # Email Configuration (for notifications)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    # Twilio (for SMS notifications)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 15

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGO_DB_NAME = 'uber_clone_test'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, config_map['default'])