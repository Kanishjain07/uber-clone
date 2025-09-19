"""
Driver API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId
from flask import current_app
import logging

logger = logging.getLogger(__name__)
drivers_bp = Blueprint('drivers', __name__)

@drivers_bp.route('/online', methods=['POST'])
@jwt_required()
def go_online():
    """Set driver status to online"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find driver profile
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})
        if not driver:
            # Create driver profile if it doesn't exist
            driver_data = {
                'user_id': ObjectId(user_id),
                'current_location': None,
                'is_online': False,
                'current_ride_id': None,
                'vehicle_type': 'standard',
                'rating': 5.0,
                'total_rides': 0,
                'earnings': 0.0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            result = db.drivers.insert_one(driver_data)
            driver = db.drivers.find_one({'_id': result.inserted_id})

        # Update driver status
        update_data = {
            'is_online': True,
            'last_seen': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # Update location if provided
        if 'latitude' in data and 'longitude' in data:
            update_data['current_location'] = {
                'latitude': float(data['latitude']),
                'longitude': float(data['longitude']),
                'updated_at': datetime.utcnow()
            }

        result = db.drivers.update_one(
            {'_id': driver['_id']},
            {'$set': update_data}
        )

        if result.modified_count > 0:
            logger.info(f"Driver {driver['_id']} went online")
            return jsonify({'message': 'Driver is now online', 'status': 'online'}), 200
        else:
            return jsonify({'error': 'Failed to update driver status'}), 500

    except Exception as e:
        logger.error(f"Go online error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/offline', methods=['POST'])
@jwt_required()
def go_offline():
    """Set driver status to offline"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find driver profile
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        # Check if driver has active ride
        if driver.get('current_ride_id'):
            return jsonify({'error': 'Cannot go offline with active ride'}), 409

        # Update driver status
        result = db.drivers.update_one(
            {'_id': driver['_id']},
            {
                '$set': {
                    'is_online': False,
                    'last_seen': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Driver {driver['_id']} went offline")
            return jsonify({'message': 'Driver is now offline', 'status': 'offline'}), 200
        else:
            return jsonify({'error': 'Failed to update driver status'}), 500

    except Exception as e:
        logger.error(f"Go offline error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/location', methods=['POST'])
@jwt_required()
def update_location():
    """Update driver's current location"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Missing latitude or longitude'}), 400

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find driver profile
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        # Update location
        result = db.drivers.update_one(
            {'_id': driver['_id']},
            {
                '$set': {
                    'current_location': {
                        'latitude': float(data['latitude']),
                        'longitude': float(data['longitude']),
                        'updated_at': datetime.utcnow()
                    },
                    'last_seen': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({'message': 'Location updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update location'}), 500

    except Exception as e:
        logger.error(f"Update location error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/status', methods=['GET'])
@jwt_required()
def get_driver_status():
    """Get driver's current status and statistics"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find driver profile with user info
        driver_data = list(db.drivers.aggregate([
            {'$match': {'user_id': ObjectId(user_id)}},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {'$unwind': '$user'}
        ]))

        if not driver_data:
            return jsonify({'error': 'Driver profile not found'}), 404

        driver = driver_data[0]

        # Get today's earnings
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_rides = list(db.rides.find({
            'driver_id': driver['_id'],
            'status': 'completed',
            'completed_at': {'$gte': today_start}
        }))

        today_earnings = sum(ride.get('final_fare', 0) for ride in today_rides)
        today_rides_count = len(today_rides)

        # Get current active ride
        active_ride = db.rides.find_one({
            'driver_id': driver['_id'],
            'status': {'$in': ['accepted', 'in_progress']}
        })

        response_data = {
            'driver_id': str(driver['_id']),
            'name': f"{driver['user']['first_name']} {driver['user']['last_name']}",
            'email': driver['user']['email'],
            'phone': driver['user'].get('phone', ''),
            'is_online': driver.get('is_online', False),
            'current_location': driver.get('current_location'),
            'vehicle_type': driver.get('vehicle_type', 'standard'),
            'rating': driver.get('rating', 5.0),
            'total_rides': driver.get('total_rides', 0),
            'total_earnings': driver.get('earnings', 0.0),
            'today_rides': today_rides_count,
            'today_earnings': today_earnings,
            'active_ride_id': str(active_ride['_id']) if active_ride else None,
            'last_seen': driver.get('last_seen'),
            'created_at': driver.get('created_at')
        }

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Get driver status error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/available-rides', methods=['GET'])
@jwt_required()
def get_available_rides():
    """Get available ride requests for the driver"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find driver profile
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        if not driver.get('is_online'):
            return jsonify({'error': 'Driver must be online to see available rides'}), 400

        if driver.get('current_ride_id'):
            return jsonify({'error': 'Driver already has an active ride'}), 409

        # Get driver's current location
        driver_location = driver.get('current_location')
        if not driver_location:
            return jsonify({'error': 'Driver location not available'}), 400

        # Find nearby ride requests (within 10km radius)
        # In production, you'd use MongoDB geospatial queries for better performance
        available_rides = list(db.rides.aggregate([
            {
                '$match': {
                    'status': 'requested',
                    'driver_id': None
                }
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'rider_id',
                    'foreignField': '_id',
                    'as': 'rider'
                }
            },
            {'$unwind': '$rider'},
            {'$sort': {'created_at': 1}}  # Oldest requests first
        ]))

        # Calculate distance and filter nearby rides
        from app.api.rides import calculate_distance

        nearby_rides = []
        for ride in available_rides:
            pickup_location = ride['pickup_location']
            distance = calculate_distance(
                driver_location['latitude'], driver_location['longitude'],
                pickup_location['latitude'], pickup_location['longitude']
            )

            if distance <= 10.0:  # Within 10km
                eta_minutes = max(1, int((distance / 30) * 60))  # Assuming 30 km/h

                nearby_rides.append({
                    'ride_id': str(ride['_id']),
                    'rider_name': f"{ride['rider']['first_name']} {ride['rider']['last_name']}",
                    'pickup_address': pickup_location['address'],
                    'destination_address': ride['destination_location']['address'],
                    'distance_to_pickup_km': round(distance, 2),
                    'eta_to_pickup_minutes': eta_minutes,
                    'estimated_fare': ride['estimated_fare'],
                    'estimated_duration': ride['estimated_duration'],
                    'passenger_count': ride.get('passenger_count', 1),
                    'special_requests': ride.get('special_requests', ''),
                    'created_at': ride['created_at']
                })

        # Sort by distance to pickup
        nearby_rides.sort(key=lambda x: x['distance_to_pickup_km'])

        return jsonify({
            'available_rides': nearby_rides[:5],  # Limit to 5 closest rides
            'count': len(nearby_rides)
        }), 200

    except Exception as e:
        logger.error(f"Get available rides error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_earnings_summary():
    """Get driver's earnings summary"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find driver profile
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        # Get earnings by time period
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start.replace(day=today_start.day - today_start.weekday())
        month_start = today_start.replace(day=1)

        # Today's earnings
        today_rides = list(db.rides.find({
            'driver_id': driver['_id'],
            'status': 'completed',
            'completed_at': {'$gte': today_start}
        }))

        # This week's earnings
        week_rides = list(db.rides.find({
            'driver_id': driver['_id'],
            'status': 'completed',
            'completed_at': {'$gte': week_start}
        }))

        # This month's earnings
        month_rides = list(db.rides.find({
            'driver_id': driver['_id'],
            'status': 'completed',
            'completed_at': {'$gte': month_start}
        }))

        earnings_summary = {
            'today': {
                'rides': len(today_rides),
                'earnings': sum(ride.get('final_fare', 0) for ride in today_rides),
                'hours_online': 8.5  # This would be calculated from actual online time
            },
            'this_week': {
                'rides': len(week_rides),
                'earnings': sum(ride.get('final_fare', 0) for ride in week_rides),
                'days_active': len(set(ride['completed_at'].date() for ride in week_rides))
            },
            'this_month': {
                'rides': len(month_rides),
                'earnings': sum(ride.get('final_fare', 0) for ride in month_rides),
                'days_active': len(set(ride['completed_at'].date() for ride in month_rides))
            },
            'all_time': {
                'rides': driver.get('total_rides', 0),
                'earnings': driver.get('earnings', 0.0),
                'rating': driver.get('rating', 5.0)
            }
        }

        return jsonify(earnings_summary), 200

    except Exception as e:
        logger.error(f"Get earnings summary error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/vehicle', methods=['GET'])
@jwt_required()
def get_vehicle_info():
    """Get driver's vehicle information"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find user and get vehicle info from registration
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user or user.get('user_type') != 'driver':
            return jsonify({'error': 'Driver not found'}), 404

        vehicle_info = user.get('vehicle_info', {})

        return jsonify({
            'vehicle_info': vehicle_info,
            'driver_license': user.get('driver_license', ''),
            'insurance_info': user.get('insurance_info', {})
        }), 200

    except Exception as e:
        logger.error(f"Get vehicle info error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@drivers_bp.route('/vehicle', methods=['PUT'])
@jwt_required()
def update_vehicle_info():
    """Update driver's vehicle information"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Update user's vehicle info
        update_data = {}
        if 'vehicle_info' in data:
            update_data['vehicle_info'] = data['vehicle_info']
        if 'driver_license' in data:
            update_data['driver_license'] = data['driver_license']
        if 'insurance_info' in data:
            update_data['insurance_info'] = data['insurance_info']

        if not update_data:
            return jsonify({'error': 'No vehicle information provided'}), 400

        result = db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )

        if result.modified_count > 0:
            # Also update vehicle type in driver profile if provided
            if 'vehicle_info' in data and 'vehicle_type' in data['vehicle_info']:
                db.drivers.update_one(
                    {'user_id': ObjectId(user_id)},
                    {'$set': {'vehicle_type': data['vehicle_info']['vehicle_type']}}
                )

            logger.info(f"Vehicle info updated for driver {user_id}")
            return jsonify({'message': 'Vehicle information updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made'}), 200

    except Exception as e:
        logger.error(f"Update vehicle info error: {e}")
        return jsonify({'error': 'Internal server error'}), 500