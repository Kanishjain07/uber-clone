from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId
import logging
from models.db import get_db
from utils.security import validate_location

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

riders_bp = Blueprint('riders', __name__)

@riders_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_rider_profile():
    """Get rider profile"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'rider':
            return jsonify({'error': 'Only riders can access this endpoint'}), 403
        
        # Get rider profile
        rider = db.riders.find_one({'user_id': current_user_id})
        if not rider:
            return jsonify({'error': 'Rider profile not found'}), 404
        
        # Get active ride if any
        active_ride = db.rides.find_one({
            'rider_id': current_user_id,
            'status': {'$in': ['requested', 'accepted', 'enroute', 'started']}
        })
        
        profile_response = {
            'user': {
                'id': str(user['_id']),
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email': user['email'],
                'phone': user['phone'],
                'profile_picture': user.get('profile_picture')
            },
            'rider_stats': {
                'total_rides': rider.get('total_rides', 0),
                'rating': rider.get('rating', 5.0),
                'preferred_payment_method': rider.get('preferred_payment_method', 'card')
            },
            'current_location': rider.get('current_location'),
            'active_ride': None
        }
        
        if active_ride:
            profile_response['active_ride'] = {
                'id': str(active_ride['_id']),
                'status': active_ride['status'],
                'pickup': active_ride['pickup_location'],
                'destination': active_ride['destination_location'],
                'estimated_fare': active_ride['estimated_fare']
            }
        
        return jsonify(profile_response), 200
        
    except Exception as e:
        logger.error(f"❌ Get rider profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@riders_bp.route('/location', methods=['PUT'])
@jwt_required()
def update_rider_location():
    """Update rider's current location"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'rider':
            return jsonify({'error': 'Only riders can update location'}), 403
        
        # Validate location data
        if not data.get('location') or not validate_location(data['location']):
            return jsonify({'error': 'Invalid location data'}), 400
        
        # Update rider location
        result = db.riders.update_one(
            {'user_id': current_user_id},
            {
                '$set': {
                    'current_location': data['location'],
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"📍 Rider {current_user_id} location updated")
            return jsonify({'message': 'Location updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made'}), 200
        
    except Exception as e:
        logger.error(f"❌ Update rider location error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@riders_bp.route('/rides/active', methods=['GET'])
@jwt_required()
def get_active_ride():
    """Get rider's active ride"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'rider':
            return jsonify({'error': 'Only riders can access this endpoint'}), 403
        
        # Get active ride
        active_ride = db.rides.find_one({
            'rider_id': current_user_id,
            'status': {'$in': ['requested', 'accepted', 'enroute', 'started']}
        })
        
        if not active_ride:
            return jsonify({'message': 'No active ride found'}), 200
        
        # Get driver info if ride is accepted
        driver_info = None
        if active_ride.get('driver_id'):
            driver_user = db.users.find_one({'_id': ObjectId(active_ride['driver_id'])})
            driver_profile = db.drivers.find_one({'user_id': active_ride['driver_id']})
            
            if driver_user and driver_profile:
                driver_info = {
                    'id': str(driver_user['_id']),
                    'name': f"{driver_user['first_name']} {driver_user['last_name']}",
                    'phone': driver_user['phone'],
                    'rating': driver_profile.get('rating', 5.0),
                    'vehicle': driver_profile.get('vehicle_type', 'sedan'),
                    'current_location': driver_profile.get('current_location')
                }
        
        ride_response = {
            'id': str(active_ride['_id']),
            'status': active_ride['status'],
            'pickup': active_ride['pickup_location'],
            'destination': active_ride['destination_location'],
            'pickup_address': active_ride.get('pickup_address', ''),
            'destination_address': active_ride.get('destination_address', ''),
            'ride_type': active_ride['ride_type'],
            'passengers': active_ride.get('passengers', 1),
            'distance_km': active_ride['distance_km'],
            'estimated_fare': active_ride['estimated_fare'],
            'created_at': active_ride['created_at'].isoformat(),
            'driver_info': driver_info
        }
        
        return jsonify(ride_response), 200
        
    except Exception as e:
        logger.error(f"❌ Get active ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@riders_bp.route('/rides/available-drivers', methods=['GET'])
@jwt_required()
def get_available_drivers():
    """Get available drivers near rider's location"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'rider':
            return jsonify({'error': 'Only riders can access this endpoint'}), 403
        
        # Get rider's current location
        rider = db.riders.find_one({'user_id': current_user_id})
        if not rider or not rider.get('current_location'):
            return jsonify({'error': 'Rider location not set'}), 400
        
        rider_location = rider['current_location']
        
        # Find available drivers within 5km radius
        available_drivers = list(db.drivers.find({
            'is_online': True,
            'current_ride_id': None,
            'current_location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [rider_location['lng'], rider_location['lat']]
                    },
                    '$maxDistance': 5000  # 5km in meters
                }
            }
        }).limit(10))
        
        drivers_response = []
        for driver in available_drivers:
            driver_user = db.users.find_one({'_id': ObjectId(driver['user_id'])})
            if driver_user:
                drivers_response.append({
                    'id': str(driver['_id']),
                    'name': f"{driver_user['first_name']} {driver_user['last_name']}",
                    'rating': driver.get('rating', 5.0),
                    'vehicle_type': driver.get('vehicle_type', 'sedan'),
                    'distance_km': round(driver.get('distance_km', 0), 2),
                    'eta_minutes': driver.get('eta_minutes', 5)
                })
        
        return jsonify({
            'available_drivers': drivers_response,
            'count': len(drivers_response)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get available drivers error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@riders_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_rider_profile():
    """Update rider profile"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'rider':
            return jsonify({'error': 'Only riders can update profile'}), 403
        
        # Fields that can be updated
        allowed_fields = ['preferred_payment_method']
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update rider profile
        result = db.riders.update_one(
            {'user_id': current_user_id},
            {
                '$set': {
                    **update_data,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"👤 Rider profile updated for user: {current_user_id}")
            return jsonify({'message': 'Profile updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made'}), 200
        
    except Exception as e:
        logger.error(f"❌ Update rider profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
