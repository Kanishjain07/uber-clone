from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from datetime import datetime
import os
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database connection
db = None
client = None

def init_db(app):
    """Initialize database connection"""
    global db, client
    
    try:
        # Get MongoDB URI from app config
        mongo_uri = app.config.get("MONGO_URI")
        
        # Create MongoDB client
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Test connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Get database name (support Atlas URIs without explicit DB path)
        parsed = urlparse(mongo_uri)
        path_db = (parsed.path or '').lstrip('/')
        env_db_name = os.getenv('MONGO_DB_NAME')
        db_name = env_db_name or (path_db if path_db else 'uber_clone')
        db = client[db_name]
        
        # Initialize collections and indexes
        init_collections()
        init_indexes()
        
        logger.info(f"Database '{db_name}' initialized successfully")
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def init_collections():
    """Initialize database collections"""
    collections = [
        'users',
        'riders',
        'drivers',
        'rides',
        'payments',
        'notifications',
        'driver_locations'
    ]
    
    for collection_name in collections:
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            logger.info(f"Created collection: {collection_name}")

def init_indexes():
    """Initialize database indexes for better performance"""
    try:
        # Users collection indexes
        db.users.create_index([("email", 1)], unique=True)
        db.users.create_index([("phone", 1)], unique=True)
        db.users.create_index([("user_type", 1)])
        
        # Riders collection indexes
        db.riders.create_index([("user_id", 1)], unique=True)
        db.riders.create_index([("current_location", "2dsphere")])
        
        # Drivers collection indexes
        db.drivers.create_index([("user_id", 1)], unique=True)
        db.drivers.create_index([("current_location", "2dsphere")])
        db.drivers.create_index([("status", 1)])
        db.drivers.create_index([("vehicle_type", 1)])
        
        # Rides collection indexes
        db.rides.create_index([("rider_id", 1)])
        db.rides.create_index([("driver_id", 1)])
        db.rides.create_index([("status", 1)])
        db.rides.create_index([("created_at", -1)])
        db.rides.create_index([("pickup_location", "2dsphere")])
        db.rides.create_index([("destination_location", "2dsphere")])
        
        # Payments collection indexes
        db.payments.create_index([("ride_id", 1)], unique=True)
        db.payments.create_index([("rider_id", 1)])
        db.payments.create_index([("driver_id", 1)])
        db.payments.create_index([("status", 1)])
        
        # Notifications collection indexes
        db.notifications.create_index([("user_id", 1)])
        db.notifications.create_index([("read", 1)])
        db.notifications.create_index([("created_at", -1)])
        
        # Driver locations collection indexes
        db.driver_locations.create_index([("driver_id", 1)], unique=True)
        db.driver_locations.create_index([("location", "2dsphere")])
        db.driver_locations.create_index([("updated_at", -1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_db():
    """Get database instance"""
    return db

def get_collection(collection_name):
    """Get a specific collection"""
    if db is None:
        raise Exception("Database not initialized")
    return db[collection_name]

def close_db():
    """Close database connection"""
    global db, client
    if client:
        client.close()
        logger.info("Database connection closed")

def health_check():
    """Check database health"""
    try:
        if client:
            client.admin.command('ping')
            return True
        return False
    except Exception:
        return False

# Database utility functions
def create_user(user_data):
    """Create a new user"""
    try:
        database = get_db()
        if database is None:
            raise Exception("Database not initialized")

        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()

        result = database.users.insert_one(user_data)
        user_data['_id'] = str(result.inserted_id)

        logger.info(f"User created: {user_data['email']}")
        return user_data

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

def find_user_by_email(email):
    """Find user by email"""
    try:
        database = get_db()
        if database is None:
            raise Exception("Database not initialized")
        return database.users.find_one({"email": email})
    except Exception as e:
        logger.error(f"Error finding user by email: {e}")
        return None

def find_user_by_id(user_id):
    """Find user by ID"""
    try:
        from bson import ObjectId
        database = get_db()
        if database is None:
            raise Exception("Database not initialized")
        return database.users.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        logger.error(f"Error finding user by ID: {e}")
        return None

def update_user(user_id, update_data):
    """Update user data"""
    try:
        from bson import ObjectId
        database = get_db()
        if database is None:
            raise Exception("Database not initialized")

        update_data['updated_at'] = datetime.utcnow()

        result = database.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return False

def delete_user(user_id):
    """Delete user"""
    try:
        from bson import ObjectId
        database = get_db()
        if database is None:
            raise Exception("Database not initialized")

        result = database.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False
