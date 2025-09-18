from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId
import logging
from models.db import get_db
from utils.security import validate_location, validate_vehicle_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

drivers_bp = Blueprint('drivers', __name__)

@drivers_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_driver_profile():
    """Get driver profile"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can access this endpoint'}), 403
        
        # Get driver profile
        driver = db.drivers.find_one({'user_id': current_user_id})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404
        
        # Get active ride if any
        active_ride = None
        if driver.get('current_ride_id'):
            active_ride = db.rides.find_one({'_id': ObjectId(driver['current_ride_id'])})
        
        profile_response = {
            'user': {
                'id': str(user['_id']),
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email': user['email'],
                'phone': user['phone'],
                'profile_picture': user.get('profile_picture'),
                'driver_status': user.get('driver_status', 'pending_verification')
            },
            'driver_stats': {
                'total_rides': driver.get('total_rides', 0),
                'rating': driver.get('rating', 5.0),
                'earnings': driver.get('earnings', 0.0),
                'vehicle_type': driver.get('vehicle_type', 'sedan'),
                'is_online': driver.get('is_online', False)
            },
            'vehicle_info': user.get('vehicle_info', {}),
            'current_location': driver.get('current_location'),
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
        logger.error(f"❌ Get driver profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/status', methods=['PUT'])
@jwt_required()
def update_driver_status():
    """Update driver online/offline status"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can update status'}), 403
        
        # Validate status
        new_status = data.get('is_online')
        if new_status not in [True, False]:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # Check if driver has an active ride
        if new_status and db.rides.find_one({
            'driver_id': current_user_id,
            'status': {'$in': ['accepted', 'enroute', 'started']}
        }):
            return jsonify({'error': 'Cannot go online while on a ride'}), 400
        
        # Update driver status
        result = db.drivers.update_one(
            {'user_id': current_user_id},
            {
                '$set': {
                    'is_online': new_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            status_text = 'online' if new_status else 'offline'
            logger.info(f"🚗 Driver {current_user_id} went {status_text}")
            
            return jsonify({
                'message': f'Driver status updated to {status_text}',
                'is_online': new_status
            }), 200
        else:
            return jsonify({'message': 'No changes made'}), 200
        
    except Exception as e:
        logger.error(f"❌ Update driver status error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/location', methods=['PUT'])
@jwt_required()
def update_driver_location():
    """Update driver's current location"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can update location'}), 403
        
        # Validate location data
        if not data.get('location') or not validate_location(data['location']):
            return jsonify({'error': 'Invalid location data'}), 400
        
        # Update driver location
        result = db.drivers.update_one(
            {'user_id': current_user_id},
            {
                '$set': {
                    'current_location': data['location'],
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Also update driver_locations collection for real-time tracking
        db.driver_locations.update_one(
            {'driver_id': current_user_id},
            {
                '$set': {
                    'location': data['location'],
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )
        
        if result.modified_count > 0:
            logger.info(f"📍 Driver {current_user_id} location updated")
            return jsonify({'message': 'Location updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made'}), 200
        
    except Exception as e:
        logger.error(f"❌ Update driver location error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/available-rides', methods=['GET'])
@jwt_required()
def get_available_rides():
    """Get available ride requests for driver"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can access this endpoint'}), 403
        
        # Check if driver is online
        driver = db.drivers.find_one({'user_id': current_user_id})
        if not driver or not driver.get('is_online'):
            return jsonify({'error': 'Driver must be online to view available rides'}), 400
        
        # Get available ride requests within 10km radius
        driver_location = driver.get('current_location')
        if not driver_location:
            return jsonify({'error': 'Driver location not set'}), 400
        
        available_rides = list(db.rides.find({
            'status': 'requested',
            'pickup_location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [driver_location['lng'], driver_location['lat']]
                    },
                    '$maxDistance': 10000  # 10km in meters
                }
            }
        }).limit(20))
        
        rides_response = []
        for ride in available_rides:
            # Get rider info
            rider = db.users.find_one({'_id': ObjectId(ride['rider_id'])})
            if rider:
                rides_response.append({
                    'id': str(ride['_id']),
                    'pickup': ride['pickup_location'],
                    'destination': ride['destination_location'],
                    'pickup_address': ride.get('pickup_address', ''),
                    'destination_address': ride.get('destination_address', ''),
                    'ride_type': ride['ride_type'],
                    'passengers': ride.get('passengers', 1),
                    'distance_km': ride['distance_km'],
                    'estimated_fare': ride['estimated_fare'],
                    'created_at': ride['created_at'].isoformat(),
                    'rider_info': {
                        'name': f"{rider['first_name']} {rider['last_name']}",
                        'rating': 5.0  # Default rating
                    }
                })
        
        return jsonify({
            'available_rides': rides_response,
            'count': len(rides_response)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get available rides error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_driver_earnings():
    """Get driver earnings and statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can access this endpoint'}), 403
        
        # Get driver profile
        driver = db.drivers.find_one({'user_id': current_user_id})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404
        
        # Get date range from query params
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Build query for rides
        query = {'driver_id': current_user_id, 'status': 'completed'}
        if from_date and to_date:
            try:
                from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                query['completed_at'] = {'$gte': from_dt, '$lte': to_dt}
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        # Get completed rides
        completed_rides = list(db.rides.find(query).sort('completed_at', -1))
        
        # Calculate earnings
        total_earnings = sum(ride.get('final_fare', 0) for ride in completed_rides)
        total_rides = len(completed_rides)
        avg_earnings = total_earnings / total_rides if total_rides > 0 else 0
        
        # Group by date for daily breakdown
        daily_earnings = {}
        for ride in completed_rides:
            date_key = ride['completed_at'].strftime('%Y-%m-%d')
            if date_key not in daily_earnings:
                daily_earnings[date_key] = {'earnings': 0, 'rides': 0}
            daily_earnings[date_key]['earnings'] += ride.get('final_fare', 0)
            daily_earnings[date_key]['rides'] += 1
        
        earnings_response = {
            'total_earnings': round(total_earnings, 2),
            'total_rides': total_rides,
            'average_per_ride': round(avg_earnings, 2),
            'daily_breakdown': daily_earnings,
            'current_balance': driver.get('earnings', 0.0)
        }
        
        return jsonify(earnings_response), 200
        
    except Exception as e:
        logger.error(f"❌ Get driver earnings error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_driver_profile():
    """Update driver profile"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can update profile'}), 403
        
        # Fields that can be updated
        allowed_fields = ['vehicle_type']
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update vehicle info if provided
        if 'vehicle_info' in data:
            if not validate_vehicle_info(data['vehicle_info']):
                return jsonify({'error': 'Invalid vehicle information'}), 400
            
            # Update user's vehicle info
            db.users.update_one(
                {'_id': ObjectId(current_user_id)},
                {'$set': {'vehicle_info': data['vehicle_info']}}
            )
        
        if not update_data and 'vehicle_info' not in data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update driver profile
        if update_data:
            result = db.drivers.update_one(
                {'user_id': current_user_id},
                {
                    '$set': {
                        **update_data,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"👤 Driver profile updated for user: {current_user_id}")
                return jsonify({'message': 'Profile updated successfully'}), 200
            else:
                return jsonify({'message': 'No changes made'}), 200
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"❌ Update driver profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
