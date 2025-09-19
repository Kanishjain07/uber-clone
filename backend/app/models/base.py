"""
Base model with common functionality
"""
from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from flask import current_app


class BaseModel:
    """Base model class with common CRUD operations"""

    collection_name = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def get_collection(cls):
        """Get MongoDB collection for this model"""
        if not cls.collection_name:
            raise ValueError("collection_name must be defined")
        return current_app.db.get_collection(cls.collection_name)

    @classmethod
    def create(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create a new document"""
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()

        collection = cls.get_collection()
        result = collection.insert_one(data)

        data['_id'] = str(result.inserted_id)
        return cls(**data)

    @classmethod
    def find_by_id(cls, object_id: str) -> Optional['BaseModel']:
        """Find document by ID"""
        try:
            collection = cls.get_collection()
            doc = collection.find_one({'_id': ObjectId(object_id)})
            if doc:
                doc['_id'] = str(doc['_id'])
                return cls(**doc)
            return None
        except Exception:
            return None

    @classmethod
    def find_one(cls, filter_dict: Dict[str, Any]) -> Optional['BaseModel']:
        """Find one document by filter"""
        collection = cls.get_collection()
        doc = collection.find_one(filter_dict)
        if doc:
            doc['_id'] = str(doc['_id'])
            return cls(**doc)
        return None

    @classmethod
    def find_many(cls, filter_dict: Dict[str, Any] = None,
                  sort: Optional[list] = None, limit: Optional[int] = None) -> list:
        """Find multiple documents"""
        if filter_dict is None:
            filter_dict = {}

        collection = cls.get_collection()
        cursor = collection.find(filter_dict)

        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)

        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(cls(**doc))

        return results

    def save(self) -> bool:
        """Save the current instance"""
        try:
            data = self.to_dict()
            data['updated_at'] = datetime.utcnow()

            collection = self.get_collection()

            if hasattr(self, '_id') and self._id:
                # Update existing document
                filter_dict = {'_id': ObjectId(self._id)}
                result = collection.update_one(filter_dict, {'$set': data})
                return result.modified_count > 0
            else:
                # Create new document
                data['created_at'] = datetime.utcnow()
                result = collection.insert_one(data)
                self._id = str(result.inserted_id)
                return True

        except Exception as e:
            print(f"Error saving document: {e}")
            return False

    def update(self, update_data: Dict[str, Any]) -> bool:
        """Update the document with new data"""
        try:
            if not hasattr(self, '_id') or not self._id:
                return False

            update_data['updated_at'] = datetime.utcnow()

            collection = self.get_collection()
            result = collection.update_one(
                {'_id': ObjectId(self._id)},
                {'$set': update_data}
            )

            if result.modified_count > 0:
                # Update the instance attributes
                for key, value in update_data.items():
                    setattr(self, key, value)
                return True

            return False

        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    def delete(self) -> bool:
        """Delete the document"""
        try:
            if not hasattr(self, '_id') or not self._id:
                return False

            collection = self.get_collection()
            result = collection.delete_one({'_id': ObjectId(self._id)})
            return result.deleted_count > 0

        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary"""
        data = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                data[key] = value
        return data

    def to_json(self) -> Dict[str, Any]:
        """Convert instance to JSON-serializable dictionary"""
        data = self.to_dict()

        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        return data

    @classmethod
    def count(cls, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents matching filter"""
        if filter_dict is None:
            filter_dict = {}

        collection = cls.get_collection()
        return collection.count_documents(filter_dict)

    @classmethod
    def aggregate(cls, pipeline: list) -> list:
        """Perform aggregation operation"""
        collection = cls.get_collection()
        results = list(collection.aggregate(pipeline))

        # Convert ObjectId to string
        for result in results:
            if '_id' in result and isinstance(result['_id'], ObjectId):
                result['_id'] = str(result['_id'])

        return results