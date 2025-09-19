"""
Rider model
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from .base import BaseModel


class Rider(BaseModel):
    """Rider model for passengers"""

    collection_name = 'riders'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def create_rider(cls, user_id: str, rider_data: Dict[str, Any] = None) -> 'Rider':
        """Create a new rider profile"""
        if rider_data is None:
            rider_data = {}

        rider_data.update({
            'user_id': user_id,
            'current_location': None,
            'preferred_payment_method': rider_data.get('preferred_payment_method', 'card'),
            'rating': 5.0,
            'total_rides': 0,
            'total_spent': 0.0,
            'saved_addresses': [],
            'emergency_contacts': [],
            'ride_preferences': {
                'vehicle_type': 'any',
                'temperature_preference': 'normal',
                'music_preference': 'no_preference',
                'conversation_preference': 'no_preference'
            }
        })

        return cls.create(rider_data)

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional['Rider']:
        """Find rider by user ID"""
        return cls.find_one({'user_id': user_id})

    def update_location(self, location: Dict[str, float]) -> bool:
        """Update rider's current location"""
        location_data = {
            'type': 'Point',
            'coordinates': [location['longitude'], location['latitude']]
        }
        return self.update({'current_location': location_data})

    def add_saved_address(self, address: Dict[str, Any]) -> bool:
        """Add a saved address"""
        saved_addresses = getattr(self, 'saved_addresses', [])

        # Check if address already exists
        for saved_addr in saved_addresses:
            if saved_addr.get('label') == address.get('label'):
                return False  # Address label already exists

        saved_addresses.append({
            'label': address['label'],
            'address': address['address'],
            'location': {
                'type': 'Point',
                'coordinates': [address['longitude'], address['latitude']]
            },
            'created_at': datetime.utcnow()
        })

        return self.update({'saved_addresses': saved_addresses})

    def remove_saved_address(self, label: str) -> bool:
        """Remove a saved address by label"""
        saved_addresses = getattr(self, 'saved_addresses', [])
        updated_addresses = [addr for addr in saved_addresses if addr.get('label') != label]

        if len(updated_addresses) < len(saved_addresses):
            return self.update({'saved_addresses': updated_addresses})
        return False

    def update_payment_method(self, payment_method: str) -> bool:
        """Update preferred payment method"""
        valid_methods = ['cash', 'card', 'wallet', 'bank_transfer']
        if payment_method not in valid_methods:
            return False

        return self.update({'preferred_payment_method': payment_method})

    def update_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update ride preferences"""
        current_prefs = getattr(self, 'ride_preferences', {})

        valid_keys = ['vehicle_type', 'temperature_preference', 'music_preference', 'conversation_preference']
        updated_prefs = {key: value for key, value in preferences.items() if key in valid_keys}

        if updated_prefs:
            current_prefs.update(updated_prefs)
            return self.update({'ride_preferences': current_prefs})
        return False

    def add_emergency_contact(self, contact: Dict[str, str]) -> bool:
        """Add emergency contact"""
        emergency_contacts = getattr(self, 'emergency_contacts', [])

        # Validate contact data
        required_fields = ['name', 'phone']
        if not all(field in contact for field in required_fields):
            return False

        emergency_contacts.append({
            'name': contact['name'],
            'phone': contact['phone'],
            'relationship': contact.get('relationship', ''),
            'created_at': datetime.utcnow()
        })

        return self.update({'emergency_contacts': emergency_contacts})

    def complete_ride(self, ride_amount: float) -> bool:
        """Update rider stats after completing a ride"""
        total_rides = getattr(self, 'total_rides', 0) + 1
        total_spent = getattr(self, 'total_spent', 0.0) + ride_amount

        return self.update({
            'total_rides': total_rides,
            'total_spent': total_spent
        })

    def update_rating(self, new_rating: float) -> bool:
        """Update rider's average rating"""
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

    @classmethod
    def get_nearby_riders(cls, location: Dict[str, float], radius_km: float = 10) -> List['Rider']:
        """Find riders near a location"""
        pipeline = [
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
            }
        ]

        results = cls.aggregate(pipeline)
        return [cls(**doc) for doc in results]

    @classmethod
    def get_top_riders(cls, limit: int = 10) -> List['Rider']:
        """Get top riders by rating and ride count"""
        return cls.find_many(
            {},
            sort=[('rating', -1), ('total_rides', -1)],
            limit=limit
        )

    def get_ride_history_summary(self) -> Dict[str, Any]:
        """Get rider's ride statistics summary"""
        from .ride import Ride

        completed_rides = Ride.find_many({'rider_id': self._id, 'status': 'completed'})

        return {
            'total_rides': len(completed_rides),
            'total_spent': getattr(self, 'total_spent', 0.0),
            'average_rating': getattr(self, 'rating', 5.0),
            'favorite_destinations': self._get_favorite_destinations(completed_rides),
            'most_used_vehicle_type': self._get_most_used_vehicle_type(completed_rides)
        }

    def _get_favorite_destinations(self, rides: List) -> List[str]:
        """Get most frequent destinations"""
        destination_counts = {}

        for ride in rides:
            dest = ride.get('destination_address', '')
            if dest:
                destination_counts[dest] = destination_counts.get(dest, 0) + 1

        # Sort by frequency and return top 5
        sorted_destinations = sorted(destination_counts.items(), key=lambda x: x[1], reverse=True)
        return [dest[0] for dest in sorted_destinations[:5]]

    def _get_most_used_vehicle_type(self, rides: List) -> str:
        """Get most frequently used vehicle type"""
        vehicle_counts = {}

        for ride in rides:
            vehicle_type = ride.get('vehicle_type', 'standard')
            vehicle_counts[vehicle_type] = vehicle_counts.get(vehicle_type, 0) + 1

        if vehicle_counts:
            return max(vehicle_counts, key=vehicle_counts.get)
        return 'standard'

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON with additional computed fields"""
        data = super().to_json()

        # Add computed fields
        data['ride_summary'] = self.get_ride_history_summary()

        return data