"""
Ride API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import math
from bson import ObjectId
from flask import current_app
import logging

logger = logging.getLogger(__name__)
rides_bp = Blueprint('rides', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def calculate_fare(distance_km, ride_type='standard'):
    """Calculate ride fare based on distance and type"""
    base_fare = {
        'standard': 3.0,
        'premium': 5.0,
        'luxury': 8.0
    }

    per_km_rate = {
        'standard': 1.5,
        'premium': 2.5,
        'luxury': 4.0
    }

    base = base_fare.get(ride_type, 3.0)
    rate = per_km_rate.get(ride_type, 1.5)

    total_fare = base + (distance_km * rate)
    return round(total_fare, 2)

@rides_bp.route('/estimate', methods=['POST'])
@jwt_required()
def estimate_ride():
    """Estimate ride price and duration"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['pickup_latitude', 'pickup_longitude', 'destination_latitude', 'destination_longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        pickup_lat = float(data['pickup_latitude'])
        pickup_lon = float(data['pickup_longitude'])
        dest_lat = float(data['destination_latitude'])
        dest_lon = float(data['destination_longitude'])
        ride_type = data.get('ride_type', 'standard')

        # Calculate distance
        distance_km = calculate_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)

        # Calculate fare
        estimated_fare = calculate_fare(distance_km, ride_type)

        # Estimate duration (assuming average speed of 30 km/h in city)
        estimated_duration = max(5, int((distance_km / 30) * 60))  # minimum 5 minutes

        return jsonify({
            'distance_km': round(distance_km, 2),
            'estimated_fare': estimated_fare,
            'estimated_duration_minutes': estimated_duration,
            'ride_type': ride_type,
            'currency': 'USD'
        }), 200

    except Exception as e:
        logger.error(f"Estimate ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/request', methods=['POST'])
@jwt_required()
def request_ride():
    """Request a new ride"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        required_fields = [
            'pickup_latitude', 'pickup_longitude', 'pickup_address',
            'destination_latitude', 'destination_longitude', 'destination_address'
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Check if user already has an active ride
        active_ride = db.rides.find_one({
            'rider_id': ObjectId(user_id),
            'status': {'$in': ['requested', 'accepted', 'in_progress']}
        })

        if active_ride:
            return jsonify({'error': 'You already have an active ride'}), 409

        # Calculate distance and fare
        distance_km = calculate_distance(
            float(data['pickup_latitude']), float(data['pickup_longitude']),
            float(data['destination_latitude']), float(data['destination_longitude'])
        )

        ride_type = data.get('ride_type', 'standard')
        estimated_fare = calculate_fare(distance_km, ride_type)

        # Create ride request
        ride_data = {
            'rider_id': ObjectId(user_id),
            'driver_id': None,
            'status': 'requested',
            'ride_type': ride_type,
            'pickup_location': {
                'latitude': float(data['pickup_latitude']),
                'longitude': float(data['pickup_longitude']),
                'address': data['pickup_address']
            },
            'destination_location': {
                'latitude': float(data['destination_latitude']),
                'longitude': float(data['destination_longitude']),
                'address': data['destination_address']
            },
            'distance_km': round(distance_km, 2),
            'estimated_fare': estimated_fare,
            'estimated_duration': max(5, int((distance_km / 30) * 60)),
            'passenger_count': data.get('passenger_count', 1),
            'special_requests': data.get('special_requests', ''),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.rides.insert_one(ride_data)
        ride_data['_id'] = result.inserted_id

        # Convert ObjectId to string for JSON response
        ride_data['_id'] = str(ride_data['_id'])
        ride_data['rider_id'] = str(ride_data['rider_id'])

        logger.info(f"Ride requested by user {user_id}: {result.inserted_id}")

        return jsonify({
            'message': 'Ride requested successfully',
            'ride': ride_data
        }), 201

    except Exception as e:
        logger.error(f"Request ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/nearby-drivers', methods=['POST'])
@jwt_required()
def get_nearby_drivers():
    """Get available drivers near pickup location"""
    try:
        data = request.get_json()

        if 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Missing latitude or longitude'}), 400

        pickup_lat = float(data['latitude'])
        pickup_lon = float(data['longitude'])
        radius_km = data.get('radius_km', 5.0)  # Default 5km radius
        ride_type = data.get('ride_type', 'standard')

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find active drivers within radius
        # This is a simplified version - in production, you'd use geospatial queries
        drivers = list(db.drivers.aggregate([
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {
                '$match': {
                    'is_online': True,
                    'current_ride_id': None,
                    'current_location': {'$ne': None}
                }
            }
        ]))

        nearby_drivers = []
        for driver in drivers:
            if driver.get('current_location'):
                driver_lat = driver['current_location']['latitude']
                driver_lon = driver['current_location']['longitude']

                distance = calculate_distance(pickup_lat, pickup_lon, driver_lat, driver_lon)

                if distance <= radius_km:
                    eta_minutes = max(1, int((distance / 30) * 60))  # Assuming 30 km/h average speed

                    nearby_drivers.append({
                        'driver_id': str(driver['_id']),
                        'name': f"{driver['user'][0]['first_name']} {driver['user'][0]['last_name']}" if driver.get('user') else 'Driver',
                        'rating': driver.get('rating', 5.0),
                        'vehicle_type': driver.get('vehicle_type', 'standard'),
                        'distance_km': round(distance, 2),
                        'eta_minutes': eta_minutes,
                        'location': {
                            'latitude': driver_lat,
                            'longitude': driver_lon
                        }
                    })

        # Sort by distance
        nearby_drivers.sort(key=lambda x: x['distance_km'])

        return jsonify({
            'drivers': nearby_drivers[:10],  # Return top 10 closest drivers
            'count': len(nearby_drivers)
        }), 200

    except Exception as e:
        logger.error(f"Get nearby drivers error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/accept', methods=['POST'])
@jwt_required()
def accept_ride(ride_id):
    """Driver accepts a ride request"""
    try:
        driver_user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find the driver
        driver = db.drivers.find_one({'user_id': ObjectId(driver_user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        # Check if driver is available
        if not driver.get('is_online') or driver.get('current_ride_id'):
            return jsonify({'error': 'Driver is not available'}), 409

        # Find the ride
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404

        if ride['status'] != 'requested':
            return jsonify({'error': 'Ride is no longer available'}), 409

        # Update ride with driver
        update_result = db.rides.update_one(
            {'_id': ObjectId(ride_id), 'status': 'requested'},
            {
                '$set': {
                    'driver_id': driver['_id'],
                    'status': 'accepted',
                    'accepted_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if update_result.modified_count == 0:
            return jsonify({'error': 'Ride was already accepted by another driver'}), 409

        # Update driver status
        db.drivers.update_one(
            {'_id': driver['_id']},
            {'$set': {'current_ride_id': ObjectId(ride_id)}}
        )

        logger.info(f"Ride {ride_id} accepted by driver {driver['_id']}")

        return jsonify({
            'message': 'Ride accepted successfully',
            'ride_id': ride_id
        }), 200

    except Exception as e:
        logger.error(f"Accept ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/start', methods=['POST'])
@jwt_required()
def start_ride(ride_id):
    """Driver starts the ride"""
    try:
        driver_user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find the driver
        driver = db.drivers.find_one({'user_id': ObjectId(driver_user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        # Find and update the ride
        update_result = db.rides.update_one(
            {
                '_id': ObjectId(ride_id),
                'driver_id': driver['_id'],
                'status': 'accepted'
            },
            {
                '$set': {
                    'status': 'in_progress',
                    'started_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if update_result.modified_count == 0:
            return jsonify({'error': 'Ride not found or cannot be started'}), 404

        logger.info(f"Ride {ride_id} started by driver {driver['_id']}")

        return jsonify({
            'message': 'Ride started successfully',
            'ride_id': ride_id
        }), 200

    except Exception as e:
        logger.error(f"Start ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/complete', methods=['POST'])
@jwt_required()
def complete_ride(ride_id):
    """Complete a ride"""
    try:
        driver_user_id = get_jwt_identity()
        data = request.get_json() or {}

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find the driver
        driver = db.drivers.find_one({'user_id': ObjectId(driver_user_id)})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404

        # Find the ride
        ride = db.rides.find_one({
            '_id': ObjectId(ride_id),
            'driver_id': driver['_id'],
            'status': 'in_progress'
        })

        if not ride:
            return jsonify({'error': 'Ride not found or not in progress'}), 404

        # Calculate actual duration
        started_at = ride.get('started_at', ride['created_at'])
        duration_minutes = int((datetime.utcnow() - started_at).total_seconds() / 60)

        # Update ride
        final_fare = data.get('final_fare', ride['estimated_fare'])

        update_result = db.rides.update_one(
            {'_id': ObjectId(ride_id)},
            {
                '$set': {
                    'status': 'completed',
                    'completed_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'actual_duration_minutes': duration_minutes,
                    'final_fare': final_fare
                }
            }
        )

        # Update driver status
        db.drivers.update_one(
            {'_id': driver['_id']},
            {
                '$set': {'current_ride_id': None},
                '$inc': {
                    'total_rides': 1,
                    'earnings': final_fare
                }
            }
        )

        # Update rider stats
        db.riders.update_one(
            {'user_id': ride['rider_id']},
            {'$inc': {'total_rides': 1}}
        )

        logger.info(f"Ride {ride_id} completed by driver {driver['_id']}")

        return jsonify({
            'message': 'Ride completed successfully',
            'ride_id': ride_id,
            'final_fare': final_fare,
            'duration_minutes': duration_minutes
        }), 200

    except Exception as e:
        logger.error(f"Complete ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_ride(ride_id):
    """Cancel a ride"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find the ride
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404

        # Check if user can cancel (rider or assigned driver)
        user_can_cancel = (
            str(ride['rider_id']) == user_id or
            (ride.get('driver_id') and str(ride['driver_id']) == user_id)
        )

        if not user_can_cancel:
            return jsonify({'error': 'Not authorized to cancel this ride'}), 403

        if ride['status'] in ['completed', 'cancelled']:
            return jsonify({'error': 'Ride cannot be cancelled'}), 409

        # Update ride
        db.rides.update_one(
            {'_id': ObjectId(ride_id)},
            {
                '$set': {
                    'status': 'cancelled',
                    'cancelled_at': datetime.utcnow(),
                    'cancelled_by': user_id,
                    'cancellation_reason': data.get('reason', ''),
                    'updated_at': datetime.utcnow()
                }
            }
        )

        # If driver was assigned, free them up
        if ride.get('driver_id'):
            db.drivers.update_one(
                {'_id': ride['driver_id']},
                {'$set': {'current_ride_id': None}}
            )

        logger.info(f"Ride {ride_id} cancelled by user {user_id}")

        return jsonify({
            'message': 'Ride cancelled successfully',
            'ride_id': ride_id
        }), 200

    except Exception as e:
        logger.error(f"Cancel ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/my-rides', methods=['GET'])
@jwt_required()
def get_my_rides():
    """Get user's ride history"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Determine if user is rider or driver
        rider = db.riders.find_one({'user_id': ObjectId(user_id)})
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})

        if rider:
            # Get rides as rider
            rides = list(db.rides.find(
                {'rider_id': ObjectId(user_id)},
                sort=[('created_at', -1)]
            ))
        elif driver:
            # Get rides as driver
            rides = list(db.rides.find(
                {'driver_id': driver['_id']},
                sort=[('created_at', -1)]
            ))
        else:
            return jsonify({'error': 'User profile not found'}), 404

        # Convert ObjectIds to strings
        for ride in rides:
            ride['_id'] = str(ride['_id'])
            ride['rider_id'] = str(ride['rider_id'])
            if ride.get('driver_id'):
                ride['driver_id'] = str(ride['driver_id'])

        return jsonify({
            'rides': rides,
            'count': len(rides)
        }), 200

    except Exception as e:
        logger.error(f"Get my rides error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>', methods=['GET'])
@jwt_required()
def get_ride_details(ride_id):
    """Get detailed information about a specific ride"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Find the ride
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404

        # Check if user is authorized to view this ride
        rider_authorized = str(ride['rider_id']) == user_id
        driver_authorized = (ride.get('driver_id') and
                           db.drivers.find_one({'_id': ride['driver_id'], 'user_id': ObjectId(user_id)}))

        if not (rider_authorized or driver_authorized):
            return jsonify({'error': 'Not authorized to view this ride'}), 403

        # Get additional details
        rider_info = db.users.find_one({'_id': ride['rider_id']})
        driver_info = None
        if ride.get('driver_id'):
            driver_user = db.drivers.aggregate([
                {'$match': {'_id': ride['driver_id']}},
                {'$lookup': {'from': 'users', 'localField': 'user_id', 'foreignField': '_id', 'as': 'user'}},
                {'$unwind': '$user'}
            ])
            driver_data = list(driver_user)
            if driver_data:
                driver_info = driver_data[0]

        # Convert ObjectIds to strings
        ride['_id'] = str(ride['_id'])
        ride['rider_id'] = str(ride['rider_id'])
        if ride.get('driver_id'):
            ride['driver_id'] = str(ride['driver_id'])

        response_data = {
            'ride': ride,
            'rider_info': {
                'name': f"{rider_info['first_name']} {rider_info['last_name']}",
                'phone': rider_info.get('phone', ''),
                'rating': 5.0  # Default rating
            } if rider_info else None,
            'driver_info': {
                'name': f"{driver_info['user']['first_name']} {driver_info['user']['last_name']}",
                'phone': driver_info['user'].get('phone', ''),
                'rating': driver_info.get('rating', 5.0),
                'vehicle_type': driver_info.get('vehicle_type', 'standard')
            } if driver_info else None
        }

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Get ride details error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_ride():
    """Get user's current active ride"""
    try:
        user_id = get_jwt_identity()

        db = current_app.db.db
        if db is None:
            raise Exception("Database not initialized")

        # Check if user is rider or driver
        rider = db.riders.find_one({'user_id': ObjectId(user_id)})
        driver = db.drivers.find_one({'user_id': ObjectId(user_id)})

        active_ride = None

        if rider:
            # Find active ride as rider
            active_ride = db.rides.find_one({
                'rider_id': ObjectId(user_id),
                'status': {'$in': ['requested', 'accepted', 'in_progress']}
            })
        elif driver:
            # Find active ride as driver
            active_ride = db.rides.find_one({
                'driver_id': driver['_id'],
                'status': {'$in': ['accepted', 'in_progress']}
            })

        if not active_ride:
            return jsonify({'message': 'No active ride found'}), 404

        # Convert ObjectIds to strings
        active_ride['_id'] = str(active_ride['_id'])
        active_ride['rider_id'] = str(active_ride['rider_id'])
        if active_ride.get('driver_id'):
            active_ride['driver_id'] = str(active_ride['driver_id'])

        return jsonify({'ride': active_ride}), 200

    except Exception as e:
        logger.error(f"Get active ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500