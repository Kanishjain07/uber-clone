from flask_socketio import emit, join_room, leave_room
from flask import request
from flask_jwt_extended import decode_token
from datetime import datetime
import logging
from models.db import get_db
from services.notifications import create_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_rider_socket(socketio):
    """Initialize rider socket events"""
    
    @socketio.on('rider_connect')
    def handle_rider_connect(data):
        """Handle rider connection"""
        try:
            # Verify JWT token
            token = data.get('token')
            if not token:
                emit('error', {'message': 'Authentication required'})
                return
            
            try:
                decoded = decode_token(token)
                rider_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Join rider's personal room
            join_room(f'rider_{rider_id}')
            
            # Update rider's online status
            db = get_db()
            db.riders.update_one(
                {'user_id': rider_id},
                {
                    '$set': {
                        'is_online': True,
                        'socket_id': request.sid,
                        'last_seen': datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"🚶 Rider {rider_id} connected")
            emit('connected', {'message': 'Connected successfully', 'rider_id': rider_id})
            
        except Exception as e:
            logger.error(f"❌ Rider connect error: {e}")
            emit('error', {'message': 'Connection failed'})
    
    @socketio.on('rider_disconnect')
    def handle_rider_disconnect(data):
        """Handle rider disconnection"""
        try:
            token = data.get('token')
            if token:
                try:
                    decoded = decode_token(token)
                    rider_id = decoded['sub']
                    
                    # Update rider's offline status
                    db = get_db()
                    db.riders.update_one(
                        {'user_id': rider_id},
                        {
                            '$set': {
                                'is_online': False,
                                'last_seen': datetime.utcnow()
                            }
                        }
                    )
                    
                    # Leave room
                    leave_room(f'rider_{rider_id}')
                    
                    logger.info(f"🚶 Rider {rider_id} disconnected")
                    
                except Exception as e:
                    logger.error(f"❌ Token decode error: {e}")
            
        except Exception as e:
            logger.error(f"❌ Rider disconnect error: {e}")
    
    @socketio.on('request_ride')
    def handle_ride_request(data):
        """Handle ride request from rider"""
        try:
            token = data.get('token')
            if not token:
                emit('error', {'message': 'Authentication required'})
                return
            
            try:
                decoded = decode_token(token)
                rider_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Validate ride data
            pickup = data.get('pickup_location')
            destination = data.get('destination_location')
            ride_type = data.get('ride_type', 'standard')
            
            if not pickup or not destination:
                emit('error', {'message': 'Pickup and destination locations required'})
                return
            
            # Create ride request
            db = get_db()
            ride_data = {
                'rider_id': rider_id,
                'pickup_location': pickup,
                'destination_location': destination,
                'pickup_address': data.get('pickup_address', ''),
                'destination_address': data.get('destination_address', ''),
                'ride_type': ride_type,
                'passengers': data.get('passengers', 1),
                'status': 'requested',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Calculate distance and fare
            from services.pricing import estimate_fare
            fare_estimate = estimate_fare(pickup, destination, ride_type)
            ride_data['distance_km'] = fare_estimate['distance_km']
            ride_data['estimated_fare'] = fare_estimate['estimated_fare']
            
            # Insert ride request
            result = db.rides.insert_one(ride_data)
            ride_id = str(result.inserted_id)
            
            # Update rider's current ride
            db.riders.update_one(
                {'user_id': rider_id},
                {
                    '$set': {
                        'current_ride_id': ride_id,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Find nearby drivers
            from services.matching import find_nearest_drivers
            nearby_drivers = find_nearest_drivers(pickup, ride_type, limit=10)
            
            # Notify nearby drivers
            for driver in nearby_drivers:
                driver_room = f'driver_{driver["user_id"]}'
                emit('new_ride_request', {
                    'ride_id': ride_id,
                    'pickup': pickup,
                    'destination': destination,
                    'pickup_address': data.get('pickup_address', ''),
                    'destination_address': data.get('destination_address', ''),
                    'ride_type': ride_type,
                    'passengers': data.get('passengers', 1),
                    'distance_km': fare_estimate['distance_km'],
                    'estimated_fare': fare_estimate['estimated_fare'],
                    'rider_info': {
                        'id': rider_id,
                        'name': f"{data.get('rider_name', 'Rider')}"
                    }
                }, room=driver_room)
            
            # Confirm ride request to rider
            emit('ride_requested', {
                'ride_id': ride_id,
                'message': 'Ride request sent to nearby drivers',
                'estimated_fare': fare_estimate['estimated_fare'],
                'estimated_time': fare_estimate['estimated_time']
            })
            
            # Create notification
            create_notification(
                user_id=rider_id,
                title='Ride Requested',
                message=f'Your ride request has been sent to nearby drivers. Estimated fare: ${fare_estimate["estimated_fare"]:.2f}',
                notification_type='ride_request'
            )
            
            logger.info(f"🚗 Ride request created: {ride_id} by rider {rider_id}")
            
        except Exception as e:
            logger.error(f"❌ Ride request error: {e}")
            emit('error', {'message': 'Failed to request ride'})
    
    @socketio.on('cancel_ride')
    def handle_ride_cancellation(data):
        """Handle ride cancellation from rider"""
        try:
            token = data.get('token')
            ride_id = data.get('ride_id')
            
            if not token or not ride_id:
                emit('error', {'message': 'Token and ride ID required'})
                return
            
            try:
                decoded = decode_token(token)
                rider_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Cancel ride
            db = get_db()
            ride = db.rides.find_one({'_id': ride_id, 'rider_id': rider_id})
            
            if not ride:
                emit('error', {'message': 'Ride not found'})
                return
            
            if ride['status'] not in ['requested', 'accepted']:
                emit('error', {'message': 'Cannot cancel ride in current status'})
                return
            
            # Update ride status
            db.rides.update_one(
                {'_id': ride_id},
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled_at': datetime.utcnow(),
                        'cancelled_by': 'rider',
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Clear rider's current ride
            db.riders.update_one(
                {'user_id': rider_id},
                {
                    '$unset': {'current_ride_id': ''},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            
            # Notify driver if ride was accepted
            if ride['status'] == 'accepted' and ride.get('driver_id'):
                driver_room = f'driver_{ride["driver_id"]}'
                emit('ride_cancelled', {
                    'ride_id': ride_id,
                    'message': 'Ride cancelled by rider'
                }, room=driver_room)
                
                # Clear driver's current ride
                db.drivers.update_one(
                    {'user_id': ride['driver_id']},
                    {
                        '$unset': {'current_ride_id': ''},
                        '$set': {'updated_at': datetime.utcnow()}
                    }
                )
            
            # Confirm cancellation to rider
            emit('ride_cancelled', {
                'ride_id': ride_id,
                'message': 'Ride cancelled successfully'
            })
            
            # Create notification
            create_notification(
                user_id=rider_id,
                title='Ride Cancelled',
                message='Your ride has been cancelled successfully',
                notification_type='ride_cancellation'
            )
            
            logger.info(f"❌ Ride {ride_id} cancelled by rider {rider_id}")
            
        except Exception as e:
            logger.error(f"❌ Ride cancellation error: {e}")
            emit('error', {'message': 'Failed to cancel ride'})
    
    @socketio.on('update_location')
    def handle_location_update(data):
        """Handle rider location update"""
        try:
            token = data.get('token')
            location = data.get('location')
            
            if not token or not location:
                emit('error', {'message': 'Token and location required'})
                return
            
            try:
                decoded = decode_token(token)
                rider_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Update rider location
            db = get_db()
            db.riders.update_one(
                {'user_id': rider_id},
                {
                    '$set': {
                        'current_location': location,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # If rider has an active ride, notify driver
            rider = db.riders.find_one({'user_id': rider_id})
            if rider and rider.get('current_ride_id'):
                ride = db.rides.find_one({'_id': rider['current_ride_id']})
                if ride and ride.get('driver_id') and ride['status'] in ['accepted', 'enroute']:
                    driver_room = f'driver_{ride["driver_id"]}'
                    emit('rider_location_update', {
                        'ride_id': str(ride['_id']),
                        'location': location
                    }, room=driver_room)
            
            emit('location_updated', {'message': 'Location updated successfully'})
            
        except Exception as e:
            logger.error(f"❌ Location update error: {e}")
            emit('error', {'message': 'Failed to update location'})
    
    @socketio.on('rate_driver')
    def handle_driver_rating(data):
        """Handle driver rating from rider"""
        try:
            token = data.get('token')
            ride_id = data.get('ride_id')
            rating = data.get('rating')
            comment = data.get('comment', '')
            
            if not token or not ride_id or not rating:
                emit('error', {'message': 'Token, ride ID, and rating required'})
                return
            
            if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
                emit('error', {'message': 'Rating must be between 1 and 5'})
                return
            
            try:
                decoded = decode_token(token)
                rider_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Update ride with rating
            db = get_db()
            ride = db.rides.find_one({'_id': ride_id, 'rider_id': rider_id})
            
            if not ride:
                emit('error', {'message': 'Ride not found'})
                return
            
            if ride['status'] != 'completed':
                emit('error', {'message': 'Can only rate completed rides'})
                return
            
            if ride.get('rider_rating'):
                emit('error', {'message': 'Ride already rated'})
                return
            
            # Update ride
            db.rides.update_one(
                {'_id': ride_id},
                {
                    '$set': {
                        'rider_rating': rating,
                        'rider_comment': comment,
                        'rated_at': datetime.utcnow()
                    }
                }
            )
            
            # Update driver's average rating
            if ride.get('driver_id'):
                driver = db.drivers.find_one({'user_id': ride['driver_id']})
                if driver:
                    current_rating = driver.get('rating', 5.0)
                    total_rides = driver.get('total_rides', 0)
                    
                    # Calculate new average rating
                    new_rating = ((current_rating * total_rides) + rating) / (total_rides + 1)
                    
                    db.drivers.update_one(
                        {'user_id': ride['driver_id']},
                        {
                            '$set': {'rating': round(new_rating, 2)},
                            '$inc': {'total_rides': 1}
                        }
                    )
            
            emit('driver_rated', {
                'ride_id': ride_id,
                'message': 'Driver rated successfully'
            })
            
            logger.info(f"⭐ Driver rated {rating}/5 for ride {ride_id}")
            
        except Exception as e:
            logger.error(f"❌ Driver rating error: {e}")
            emit('error', {'message': 'Failed to rate driver'})
    
    @socketio.on('join_ride_room')
    def handle_join_ride_room(data):
        """Handle rider joining ride-specific room"""
        try:
            token = data.get('token')
            ride_id = data.get('ride_id')
            
            if not token or not ride_id:
                emit('error', {'message': 'Token and ride ID required'})
                return
            
            try:
                decoded = decode_token(token)
                rider_id = decoded['sub']
            except Exception as e:
                emit('error', {'message': 'Invalid token'})
                return
            
            # Verify rider is part of this ride
            db = get_db()
            ride = db.rides.find_one({'_id': ride_id, 'rider_id': rider_id})
            
            if not ride:
                emit('error', {'message': 'Access denied'})
                return
            
            # Join ride room
            join_room(f'ride_{ride_id}')
            emit('joined_ride_room', {
                'ride_id': ride_id,
                'message': 'Joined ride room successfully'
            })
            
        except Exception as e:
            logger.error(f"❌ Join ride room error: {e}")
            emit('error', {'message': 'Failed to join ride room'})
    
    @socketio.on('leave_ride_room')
    def handle_leave_ride_room(data):
        """Handle rider leaving ride-specific room"""
        try:
            ride_id = data.get('ride_id')
            if ride_id:
                leave_room(f'ride_{ride_id}')
                emit('left_ride_room', {
                    'ride_id': ride_id,
                    'message': 'Left ride room successfully'
                })
        except Exception as e:
            logger.error(f"❌ Leave ride room error: {e}")
    
    return socketio
