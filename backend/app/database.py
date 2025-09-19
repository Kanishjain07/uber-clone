"""
Database connection and management
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager"""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None

    def init_app(self, app):
        """Initialize database with Flask app"""
        try:
            mongo_uri = app.config.get('MONGO_URI')
            db_name = app.config.get('MONGO_DB_NAME', 'uber_clone')

            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )

            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            self.db = self.client[db_name]

            # Initialize collections and indexes
            self._init_collections()
            self._init_indexes()

            app.db = self

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def _init_collections(self):
        """Initialize database collections"""
        collections = [
            'users',
            'riders',
            'drivers',
            'rides',
            'payments',
            'notifications',
            'driver_locations',
            'ride_requests',
            'ride_history',
            'driver_earnings',
            'feedback_ratings'
        ]

        existing_collections = self.db.list_collection_names()
        for collection_name in collections:
            if collection_name not in existing_collections:
                self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")

    def _init_indexes(self):
        """Initialize database indexes for better performance"""
        try:
            # Users collection indexes
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            self.db.users.create_index([("phone", ASCENDING)], unique=True)
            self.db.users.create_index([("user_type", ASCENDING)])
            self.db.users.create_index([("is_active", ASCENDING)])

            # Riders collection indexes
            self.db.riders.create_index([("user_id", ASCENDING)], unique=True)
            self.db.riders.create_index([("current_location", "2dsphere")])

            # Drivers collection indexes
            self.db.drivers.create_index([("user_id", ASCENDING)], unique=True)
            self.db.drivers.create_index([("current_location", "2dsphere")])
            self.db.drivers.create_index([("status", ASCENDING)])
            self.db.drivers.create_index([("is_online", ASCENDING)])
            self.db.drivers.create_index([("vehicle_type", ASCENDING)])

            # Rides collection indexes
            self.db.rides.create_index([("rider_id", ASCENDING)])
            self.db.rides.create_index([("driver_id", ASCENDING)])
            self.db.rides.create_index([("status", ASCENDING)])
            self.db.rides.create_index([("created_at", DESCENDING)])
            self.db.rides.create_index([("pickup_location", "2dsphere")])
            self.db.rides.create_index([("destination_location", "2dsphere")])

            # Ride requests collection indexes
            self.db.ride_requests.create_index([("rider_id", ASCENDING)])
            self.db.ride_requests.create_index([("status", ASCENDING)])
            self.db.ride_requests.create_index([("created_at", DESCENDING)])
            self.db.ride_requests.create_index([("pickup_location", "2dsphere")])

            # Driver locations collection indexes
            self.db.driver_locations.create_index([("driver_id", ASCENDING)], unique=True)
            self.db.driver_locations.create_index([("location", "2dsphere")])
            self.db.driver_locations.create_index([("updated_at", DESCENDING)])

            # Payments collection indexes
            self.db.payments.create_index([("ride_id", ASCENDING)], unique=True)
            self.db.payments.create_index([("rider_id", ASCENDING)])
            self.db.payments.create_index([("driver_id", ASCENDING)])
            self.db.payments.create_index([("status", ASCENDING)])

            # Notifications collection indexes
            self.db.notifications.create_index([("user_id", ASCENDING)])
            self.db.notifications.create_index([("is_read", ASCENDING)])
            self.db.notifications.create_index([("created_at", DESCENDING)])

            # Feedback and ratings indexes
            self.db.feedback_ratings.create_index([("ride_id", ASCENDING)], unique=True)
            self.db.feedback_ratings.create_index([("rider_id", ASCENDING)])
            self.db.feedback_ratings.create_index([("driver_id", ASCENDING)])

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def get_collection(self, name: str):
        """Get a specific collection"""
        if self.db is None:
            raise Exception("Database not initialized")
        return self.db[name]

    def health_check(self) -> bool:
        """Check database health"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

    # Utility methods for common operations
    def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document"""
        document['created_at'] = datetime.utcnow()
        document['updated_at'] = datetime.utcnow()
        result = self.db[collection].insert_one(document)
        return str(result.inserted_id)

    def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        result = self.db[collection].find_one(filter_dict)
        if result and '_id' in result:
            result['_id'] = str(result['_id'])
        return result

    def find_many(self, collection: str, filter_dict: Dict[str, Any],
                  sort: Optional[List] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        cursor = self.db[collection].find(filter_dict)

        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)

        results = list(cursor)
        for result in results:
            if '_id' in result:
                result['_id'] = str(result['_id'])
        return results

    def update_one(self, collection: str, filter_dict: Dict[str, Any],
                   update_dict: Dict[str, Any]) -> bool:
        """Update a single document"""
        update_dict['updated_at'] = datetime.utcnow()
        result = self.db[collection].update_one(filter_dict, {'$set': update_dict})
        return result.modified_count > 0

    def delete_one(self, collection: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document"""
        result = self.db[collection].delete_one(filter_dict)
        return result.deleted_count > 0

    def count_documents(self, collection: str, filter_dict: Dict[str, Any]) -> int:
        """Count documents matching filter"""
        return self.db[collection].count_documents(filter_dict)

    def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform aggregation operation"""
        results = list(self.db[collection].aggregate(pipeline))
        for result in results:
            if '_id' in result and isinstance(result['_id'], ObjectId):
                result['_id'] = str(result['_id'])
        return results