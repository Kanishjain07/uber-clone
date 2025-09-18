from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId
import logging
from models.db import get_db
from utils.security import validate_ride_data, calculate_distance, estimate_ride_fare
from services.matching import find_nearest_driver
from services.pricing import calculate_fare
from services.notifications import send_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rides_bp = Blueprint('rides', __name__)

@rides_bp.route('/request', methods=['POST'])
@jwt_required()
def request_ride():
    """Request a new ride"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate ride data
        is_valid, message = validate_ride_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'rider':
            return jsonify({'error': 'Only riders can request rides'}), 403
        
        # Check if user has an active ride
        active_ride = db.rides.find_one({
            'rider_id': current_user_id,
            'status': {'$in': ['requested', 'accepted', 'enroute', 'started']}
        })
        
        if active_ride:
            return jsonify({'error': 'You already have an active ride'}), 400
        
        # Calculate distance and estimated fare
        pickup = data['pickup']
        destination = data['destination']
        
        distance_km = calculate_distance(
            pickup['lat'], pickup['lng'],
            destination['lat'], destination['lng']
        )
        
        estimated_fare = estimate_ride_fare(distance_km, data['ride_type'])
        
        # Create ride request
        ride_data = {
            'rider_id': current_user_id,
            'pickup_location': pickup,
            'destination_location': destination,
            'pickup_address': data.get('pickup_address', ''),
            'destination_address': data.get('destination_address', ''),
            'ride_type': data['ride_type'],
            'passengers': data.get('passengers', 1),
            'distance_km': round(distance_km, 2),
            'estimated_fare': estimated_fare,
            'status': 'requested',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert ride into database
        result = db.rides.insert_one(ride_data)
        ride_id = str(result.inserted_id)
        
        # Find nearest available driver
        driver = find_nearest_driver(pickup, data['ride_type'])
        
        if driver:
            # Update ride with driver info
            db.rides.update_one(
                {'_id': result.inserted_id},
                {
                    '$set': {
                        'driver_id': str(driver['_id']),
                        'status': 'accepted',
                        'accepted_at': datetime.utcnow()
                    }
                }
            )
            
            # Send notification to driver
            send_notification(
                driver['_id'],
                'new_ride_request',
                f'New ride request from {user["first_name"]}',
                {'ride_id': ride_id}
            )
            
            # Send notification to rider
            send_notification(
                current_user_id,
                'ride_accepted',
                f'Driver {driver["first_name"]} accepted your ride',
                {'ride_id': ride_id, 'driver_info': driver}
            )
            
            logger.info(f"🚗 Ride {ride_id} accepted by driver {driver['_id']}")
            
            return jsonify({
                'message': 'Ride request accepted',
                'ride_id': ride_id,
                'driver_info': driver,
                'estimated_fare': estimated_fare,
                'estimated_time': '3-5 minutes'
            }), 201
        
        else:
            # No driver available, keep ride in requested status
            logger.info(f"🚗 Ride {ride_id} requested, waiting for driver")
            
            return jsonify({
                'message': 'Ride request submitted, searching for driver',
                'ride_id': ride_id,
                'status': 'searching',
                'estimated_fare': estimated_fare
            }), 201
        
    except Exception as e:
        logger.error(f"❌ Ride request error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/accept', methods=['POST'])
@jwt_required()
def accept_ride(ride_id):
    """Driver accepts a ride request"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can accept rides'}), 403
        
        # Check if driver is available
        driver = db.drivers.find_one({'user_id': current_user_id})
        if not driver:
            return jsonify({'error': 'Driver profile not found'}), 404
        
        if driver.get('current_ride_id'):
            return jsonify({'error': 'Driver already has an active ride'}), 400
        
        # Get ride request
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
        
        if ride['status'] != 'requested':
            return jsonify({'error': 'Ride is not available for acceptance'}), 400
        
        # Update ride status
        result = db.rides.update_one(
            {'_id': ObjectId(ride_id)},
            {
                '$set': {
                    'driver_id': current_user_id,
                    'status': 'accepted',
                    'accepted_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            # Update driver status
            db.drivers.update_one(
                {'user_id': current_user_id},
                {
                    '$set': {
                        'current_ride_id': ride_id,
                        'is_online': False
                    }
                }
            )
            
            # Send notification to rider
            send_notification(
                ride['rider_id'],
                'ride_accepted',
                f'Driver {user["first_name"]} accepted your ride',
                {'ride_id': ride_id, 'driver_info': user}
            )
            
            logger.info(f"✅ Driver {current_user_id} accepted ride {ride_id}")
            
            return jsonify({
                'message': 'Ride accepted successfully',
                'ride_id': ride_id,
                'rider_info': {
                    'pickup': ride['pickup_location'],
                    'destination': ride['destination_location'],
                    'estimated_fare': ride['estimated_fare']
                }
            }), 200
        
        else:
            return jsonify({'error': 'Failed to accept ride'}), 500
        
    except Exception as e:
        logger.error(f"❌ Accept ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/start', methods=['POST'])
@jwt_required()
def start_ride(ride_id):
    """Start a ride (driver picks up rider)"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can start rides'}), 403
        
        # Get ride
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
        
        if ride['driver_id'] != current_user_id:
            return jsonify({'error': 'You are not assigned to this ride'}), 403
        
        if ride['status'] != 'accepted':
            return jsonify({'error': 'Ride cannot be started in current status'}), 400
        
        # Update ride status
        result = db.rides.update_one(
            {'_id': ObjectId(ride_id)},
            {
                '$set': {
                    'status': 'started',
                    'started_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            # Send notification to rider
            send_notification(
                ride['rider_id'],
                'ride_started',
                'Your ride has started!',
                {'ride_id': ride_id}
            )
            
            logger.info(f"🚗 Ride {ride_id} started by driver {current_user_id}")
            
            return jsonify({
                'message': 'Ride started successfully',
                'ride_id': ride_id
            }), 200
        
        else:
            return jsonify({'error': 'Failed to start ride'}), 500
        
    except Exception as e:
        logger.error(f"❌ Start ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/complete', methods=['POST'])
@jwt_required()
def complete_ride(ride_id):
    """Complete a ride"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user['user_type'] != 'driver':
            return jsonify({'error': 'Only drivers can complete rides'}), 403
        
        # Get ride
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
        
        if ride['driver_id'] != current_user_id:
            return jsonify({'error': 'You are not assigned to this ride'}), 403
        
        if ride['status'] != 'started':
            return jsonify({'error': 'Ride cannot be completed in current status'}), 400
        
        # Calculate final fare
        final_fare = calculate_fare(ride)
        
        # Update ride status
        result = db.rides.update_one(
            {'_id': ObjectId(ride_id)},
            {
                '$set': {
                    'status': 'completed',
                    'completed_at': datetime.utcnow(),
                    'final_fare': final_fare,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            # Update driver status
            db.drivers.update_one(
                {'user_id': current_user_id},
                {
                    '$set': {
                        'current_ride_id': None,
                        'is_online': True
                    },
                    '$inc': {
                        'earnings': final_fare,
                        'total_rides': 1
                    }
                }
            )
            
            # Update rider stats
            db.riders.update_one(
                {'user_id': ride['rider_id']},
                {'$inc': {'total_rides': 1}}
            )
            
            # Create payment record
            payment_data = {
                'ride_id': ride_id,
                'rider_id': ride['rider_id'],
                'driver_id': current_user_id,
                'amount': final_fare,
                'status': 'completed',
                'created_at': datetime.utcnow()
            }
            db.payments.insert_one(payment_data)
            
            # Send notification to rider
            send_notification(
                ride['rider_id'],
                'ride_completed',
                f'Your ride has been completed. Total fare: ${final_fare}',
                {'ride_id': ride_id, 'final_fare': final_fare}
            )
            
            logger.info(f"✅ Ride {ride_id} completed by driver {current_user_id}")
            
            return jsonify({
                'message': 'Ride completed successfully',
                'ride_id': ride_id,
                'final_fare': final_fare
            }), 200
        
        else:
            return jsonify({'error': 'Failed to complete ride'}), 500
        
    except Exception as e:
        logger.error(f"❌ Complete ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_ride(ride_id):
    """Cancel a ride"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get ride
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
        
        # Check if user is authorized to cancel
        if ride['rider_id'] != current_user_id and ride.get('driver_id') != current_user_id:
            return jsonify({'error': 'You are not authorized to cancel this ride'}), 403
        
        if ride['status'] in ['completed', 'cancelled']:
            return jsonify({'error': 'Ride cannot be cancelled in current status'}), 400
        
        # Update ride status
        result = db.rides.update_one(
            {'_id': ObjectId(ride_id)},
            {
                '$set': {
                    'status': 'cancelled',
                    'cancelled_at': datetime.utcnow(),
                    'cancelled_by': current_user_id,
                    'cancellation_reason': data.get('reason', 'No reason provided'),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            # If driver was assigned, free them up
            if ride.get('driver_id'):
                db.drivers.update_one(
                    {'user_id': ride['driver_id']},
                    {
                        '$set': {
                            'current_ride_id': None,
                            'is_online': True
                        }
                    }
                )
                
                # Send notification to driver
                send_notification(
                    ride['driver_id'],
                    'ride_cancelled',
                    'A ride has been cancelled',
                    {'ride_id': ride_id}
                )
            
            # Send notification to rider
            send_notification(
                ride['rider_id'],
                'ride_cancelled',
                'Your ride has been cancelled',
                {'ride_id': ride_id}
            )
            
            logger.info(f"❌ Ride {ride_id} cancelled by {current_user_id}")
            
            return jsonify({
                'message': 'Ride cancelled successfully',
                'ride_id': ride_id
            }), 200
        
        else:
            return jsonify({'error': 'Failed to cancel ride'}), 500
        
    except Exception as e:
        logger.error(f"❌ Cancel ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/<ride_id>', methods=['GET'])
@jwt_required()
def get_ride(ride_id):
    """Get ride details"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get ride
        db = get_db()
        ride = db.rides.find_one({'_id': ObjectId(ride_id)})
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
        
        # Check if user is authorized to view this ride
        if ride['rider_id'] != current_user_id and ride.get('driver_id') != current_user_id:
            return jsonify({'error': 'You are not authorized to view this ride'}), 403
        
        # Get user info for display
        rider = db.users.find_one({'_id': ObjectId(ride['rider_id'])})
        driver = None
        if ride.get('driver_id'):
            driver = db.users.find_one({'_id': ObjectId(ride['driver_id'])})
        
        # Prepare response
        ride_response = {
            'id': str(ride['_id']),
            'status': ride['status'],
            'pickup': ride['pickup_location'],
            'destination': ride['destination_location'],
            'pickup_address': ride.get('pickup_address', ''),
            'destination_address': ride.get('destination_address', ''),
            'ride_type': ride['ride_type'],
            'passengers': ride.get('passengers', 1),
            'distance_km': ride['distance_km'],
            'estimated_fare': ride['estimated_fare'],
            'final_fare': ride.get('final_fare'),
            'created_at': ride['created_at'].isoformat(),
            'rider_info': {
                'id': str(rider['_id']),
                'name': f"{rider['first_name']} {rider['last_name']}",
                'phone': rider['phone']
            } if rider else None
        }
        
        if driver:
            ride_response['driver_info'] = {
                'id': str(driver['_id']),
                'name': f"{driver['first_name']} {driver['last_name']}",
                'phone': driver['phone']
            }
        
        return jsonify(ride_response), 200
        
    except Exception as e:
        logger.error(f"❌ Get ride error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@rides_bp.route('/history', methods=['GET'])
@jwt_required()
def get_ride_history():
    """Get user's ride history"""
    try:
        current_user_id = get_jwt_identity()
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Get user info
        db = get_db()
        user = db.users.find_one({'_id': ObjectId(current_user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Build query based on user type
        if user['user_type'] == 'rider':
            query = {'rider_id': current_user_id}
        else:
            query = {'driver_id': current_user_id}
        
        # Get total count
        total_rides = db.rides.count_documents(query)
        
        # Get rides with pagination
        rides = list(db.rides.find(query)
                    .sort('created_at', -1)
                    .skip((page - 1) * limit)
                    .limit(limit))
        
        # Format rides for response
        rides_response = []
        for ride in rides:
            ride_response = {
                'id': str(ride['_id']),
                'status': ride['status'],
                'pickup_address': ride.get('pickup_address', ''),
                'destination_address': ride.get('destination_address', ''),
                'ride_type': ride['ride_type'],
                'distance_km': ride['distance_km'],
                'estimated_fare': ride['estimated_fare'],
                'final_fare': ride.get('final_fare'),
                'created_at': ride['created_at'].isoformat()
            }
            rides_response.append(ride_response)
        
        return jsonify({
            'rides': rides_response,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_rides,
                'pages': (total_rides + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get ride history error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
