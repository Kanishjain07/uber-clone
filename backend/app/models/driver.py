"""
Driver model
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base import BaseModel


class Driver(BaseModel):
    """Driver model for ride providers"""

    collection_name = 'drivers'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def create_driver(cls, user_id: str, driver_data: Dict[str, Any]) -> 'Driver':
        """Create a new driver profile"""
        driver_data.update({
            'user_id': user_id,
            'current_location': None,
            'status': 'offline',  # offline, online, busy, break
            'is_online': False,
            'current_ride_id': None,
            'rating': 5.0,
            'total_rides': 0,
            'total_earnings': 0.0,
            'documents_verified': False,
            'vehicle_verified': False,
            'background_check_status': 'pending',  # pending, approved, rejected
            'license_expiry': driver_data.get('license_expiry'),
            'insurance_expiry': driver_data.get('insurance_expiry'),
            'vehicle_registration_expiry': driver_data.get('vehicle_registration_expiry'),
            'bank_details': {},
            'availability_schedule': {},
            'preferences': {
                'max_distance_per_ride': 50.0,  # km
                'preferred_areas': [],
                'ride_types': ['standard'],  # standard, premium, luxury
                'break_intervals': 4  # hours
            }
        })

        return cls.create(driver_data)

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional['Driver']:
        """Find driver by user ID"""
        return cls.find_one({'user_id': user_id})

    def update_location(self, location: Dict[str, float]) -> bool:
        """Update driver's current location"""
        location_data = {
            'type': 'Point',
            'coordinates': [location['longitude'], location['latitude']]
        }

        # Also update in driver_locations collection for real-time tracking
        from flask import current_app
        location_collection = current_app.db.get_collection('driver_locations')

        location_collection.update_one(
            {'driver_id': self._id},
            {
                '$set': {
                    'driver_id': self._id,
                    'location': location_data,
                    'updated_at': datetime.utcnow(),
                    'status': self.status
                }
            },
            upsert=True
        )

        return self.update({'current_location': location_data})

    def go_online(self) -> bool:
        """Set driver status to online"""
        return self.update({
            'status': 'online',
            'is_online': True,
            'last_online_at': datetime.utcnow()
        })

    def go_offline(self) -> bool:
        """Set driver status to offline"""
        return self.update({
            'status': 'offline',
            'is_online': False,
            'last_offline_at': datetime.utcnow()
        })

    def set_busy(self, ride_id: str) -> bool:
        """Set driver as busy with a ride"""
        return self.update({
            'status': 'busy',
            'current_ride_id': ride_id
        })

    def set_available(self) -> bool:
        """Set driver as available (online but not busy)"""
        return self.update({
            'status': 'online',
            'current_ride_id': None
        })

    def take_break(self) -> bool:
        """Set driver on break"""
        return self.update({'status': 'break'})

    def update_vehicle_info(self, vehicle_data: Dict[str, Any]) -> bool:
        """Update vehicle information"""
        vehicle_fields = [
            'make', 'model', 'year', 'color', 'license_plate',
            'vehicle_type', 'seats', 'features'
        ]

        vehicle_info = {
            key: value for key, value in vehicle_data.items()
            if key in vehicle_fields
        }

        if vehicle_info:
            return self.update({'vehicle_info': vehicle_info})
        return False

    def update_documents(self, document_data: Dict[str, Any]) -> bool:
        """Update driver documents"""
        document_fields = [
            'driver_license', 'vehicle_registration', 'insurance_certificate',
            'background_check', 'profile_photo'
        ]

        documents = {
            key: value for key, value in document_data.items()
            if key in document_fields
        }

        if documents:
            return self.update({'documents': documents})
        return False

    def verify_documents(self) -> bool:
        """Mark driver documents as verified"""
        return self.update({
            'documents_verified': True,
            'background_check_status': 'approved'
        })

    def reject_documents(self, reason: str) -> bool:
        """Reject driver documents"""
        return self.update({
            'documents_verified': False,
            'background_check_status': 'rejected',
            'rejection_reason': reason
        })

    def complete_ride(self, ride_amount: float, distance_km: float) -> bool:
        """Update driver stats after completing a ride"""
        total_rides = getattr(self, 'total_rides', 0) + 1
        total_earnings = getattr(self, 'total_earnings', 0.0) + ride_amount
        total_distance = getattr(self, 'total_distance_km', 0.0) + distance_km

        return self.update({
            'total_rides': total_rides,
            'total_earnings': total_earnings,
            'total_distance_km': total_distance
        })

    def update_rating(self, new_rating: float) -> bool:
        """Update driver's average rating"""
        if not 1.0 <= new_rating <= 5.0:
            return False

        current_rating = getattr(self, 'rating', 5.0)
        total_rides = getattr(self, 'total_rides', 0)

        if total_rides == 0:
            average_rating = new_rating
        else:
            # Calculate weighted average
            total_rating_points = current_rating * total_rides
            total_rating_points += new_rating
            average_rating = total_rating_points / (total_rides + 1)

        return self.update({'rating': round(average_rating, 2)})

    def update_bank_details(self, bank_data: Dict[str, str]) -> bool:
        """Update bank account details for payments"""
        required_fields = ['account_number', 'routing_number', 'account_holder_name']

        if not all(field in bank_data for field in required_fields):
            return False

        bank_details = {
            'account_number': bank_data['account_number'],
            'routing_number': bank_data['routing_number'],
            'account_holder_name': bank_data['account_holder_name'],
            'bank_name': bank_data.get('bank_name', ''),
            'updated_at': datetime.utcnow()
        }

        return self.update({'bank_details': bank_details})

    def set_availability_schedule(self, schedule: Dict[str, Any]) -> bool:
        """Set driver's availability schedule"""
        # Schedule format: {"monday": {"start": "08:00", "end": "18:00"}, ...}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        valid_schedule = {}
        for day in days:
            if day in schedule:
                day_schedule = schedule[day]
                if 'start' in day_schedule and 'end' in day_schedule:
                    valid_schedule[day] = day_schedule

        return self.update({'availability_schedule': valid_schedule})

    @classmethod
    def find_available_drivers(cls, location: Dict[str, float], radius_km: float = 10,
                               vehicle_type: str = None) -> List['Driver']:
        """Find available drivers near a location"""
        # Base filter for available drivers
        match_filter = {
            'status': 'online',
            'is_online': True,
            'documents_verified': True,
            'background_check_status': 'approved'
        }

        if vehicle_type:
            match_filter['vehicle_info.vehicle_type'] = vehicle_type

        pipeline = [
            {'$match': match_filter},
            {
                '$geoNear': {
                    'near': {
                        'type': 'Point',
                        'coordinates': [location['longitude'], location['latitude']]
                    },
                    'distanceField': 'distance',
                    'maxDistance': radius_km * 1000,  # Convert to meters
                    'spherical': True
                }
            },
            {'$sort': {'distance': 1, 'rating': -1}}  # Sort by distance, then rating
        ]

        results = cls.aggregate(pipeline)
        return [cls(**doc) for doc in results]

    @classmethod
    def get_top_drivers(cls, limit: int = 10) -> List['Driver']:
        """Get top drivers by rating and ride count"""
        return cls.find_many(
            {'documents_verified': True},
            sort=[('rating', -1), ('total_rides', -1)],
            limit=limit
        )

    @classmethod
    def get_drivers_by_earnings(cls, start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict]:
        """Get drivers sorted by earnings in a time period"""
        pipeline = [
            {
                '$lookup': {
                    'from': 'rides',
                    'localField': '_id',
                    'foreignField': 'driver_id',
                    'as': 'rides'
                }
            },
            {
                '$addFields': {
                    'period_earnings': {
                        '$sum': {
                            '$map': {
                                'input': {
                                    '$filter': {
                                        'input': '$rides',
                                        'cond': {
                                            '$and': [
                                                {'$gte': ['$$this.completed_at', start_date]},
                                                {'$lte': ['$$this.completed_at', end_date]},
                                                {'$eq': ['$$this.status', 'completed']}
                                            ]
                                        }
                                    }
                                },
                                'as': 'ride',
                                'in': '$$ride.driver_earnings'
                            }
                        }
                    }
                }
            },
            {'$sort': {'period_earnings': -1}},
            {'$limit': limit}
        ]

        return cls.aggregate(pipeline)

    def get_earnings_summary(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get driver's earnings summary for a period"""
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()

        from .ride import Ride

        rides = Ride.find_many({
            'driver_id': self._id,
            'status': 'completed',
            'completed_at': {'$gte': start_date, '$lte': end_date}
        })

        total_earnings = sum(ride.get('driver_earnings', 0) for ride in rides)
        total_rides = len(rides)
        total_hours = sum(ride.get('duration_minutes', 0) for ride in rides) / 60

        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_earnings': total_earnings,
            'total_rides': total_rides,
            'total_hours': round(total_hours, 2),
            'average_per_ride': round(total_earnings / max(total_rides, 1), 2),
            'average_per_hour': round(total_earnings / max(total_hours, 1), 2) if total_hours > 0 else 0
        }

    def is_available(self) -> bool:
        """Check if driver is available for rides"""
        return (
            getattr(self, 'status', '') == 'online' and
            getattr(self, 'is_online', False) and
            getattr(self, 'documents_verified', False) and
            getattr(self, 'background_check_status', '') == 'approved'
        )

    def needs_document_renewal(self) -> List[str]:
        """Check which documents need renewal"""
        expiring_docs = []
        warning_days = 30  # Warn 30 days before expiry

        warning_date = datetime.utcnow() + timedelta(days=warning_days)

        if hasattr(self, 'license_expiry') and self.license_expiry:
            if self.license_expiry < warning_date:
                expiring_docs.append('driver_license')

        if hasattr(self, 'insurance_expiry') and self.insurance_expiry:
            if self.insurance_expiry < warning_date:
                expiring_docs.append('insurance')

        if hasattr(self, 'vehicle_registration_expiry') and self.vehicle_registration_expiry:
            if self.vehicle_registration_expiry < warning_date:
                expiring_docs.append('vehicle_registration')

        return expiring_docs

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON with additional computed fields"""
        data = super().to_json()

        # Add computed fields
        data['is_available'] = self.is_available()
        data['expiring_documents'] = self.needs_document_renewal()
        data['earnings_summary'] = self.get_earnings_summary()

        # Hide sensitive information
        if 'bank_details' in data:
            if 'account_number' in data['bank_details']:
                # Mask account number except last 4 digits
                account = data['bank_details']['account_number']
                data['bank_details']['account_number'] = f"****{account[-4:] if len(account) > 4 else account}"

        return data