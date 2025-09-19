"""
WebSocket handlers for real-time ride updates
"""
from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room, rooms
from bson import ObjectId
from flask import current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Store connected clients
connected_clients = {}

def register_socketio_handlers(socketio):
    """Register all socket handlers"""

    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection with authentication"""
        try:
            # Get token from auth or query parameters
            token = None
            if auth and 'token' in auth:
                token = auth['token']
            elif request.args.get('token'):
                token = request.args.get('token')

            if not token:
                logger.warning("Client connected without token")
                return False  # Reject connection

            # Decode JWT token
            try:
                decoded_token = decode_token(token)
                user_id = decoded_token['sub']
                user_type = decoded_token.get('user_type', 'unknown')
            except Exception as e:
                logger.warning(f"Invalid token in socket connection: {e}")
                return False

            # Store client info
            connected_clients[request.sid] = {
                'user_id': user_id,
                'user_type': user_type,
                'connected_at': None
            }

            # Join user to their personal room
            join_room(f"user_{user_id}")

            logger.info(f"User {user_id} ({user_type}) connected via WebSocket")
            emit('connected', {'status': 'success', 'user_id': user_id})

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if request.sid in connected_clients:
            client_info = connected_clients[request.sid]
            user_id = client_info['user_id']

            # Leave all rooms
            for room in rooms(request.sid):
                leave_room(room)

            # Remove from connected clients
            del connected_clients[request.sid]

            logger.info(f"User {user_id} disconnected from WebSocket")

    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection testing"""
        emit('pong', {'timestamp': str(datetime.utcnow())})

    @socketio.on('driver_location_update')
    def handle_driver_location_update(data):
        """Handle real-time driver location updates"""
        try:
            if request.sid not in connected_clients:
                return

            client_info = connected_clients[request.sid]
            user_id = client_info['user_id']

            if client_info['user_type'] != 'driver':
                emit('error', {'message': 'Only drivers can update location'})
                return

            if 'latitude' not in data or 'longitude' not in data:
                emit('error', {'message': 'Missing location coordinates'})
                return

            # Update driver location in database
            db = current_app.db.db
            if db is None:
                emit('error', {'message': 'Database error'})
                return

            driver = db.drivers.find_one({'user_id': ObjectId(user_id)})
            if not driver:
                emit('error', {'message': 'Driver profile not found'})
                return

            # Update location
            db.drivers.update_one(
                {'_id': driver['_id']},
                {
                    '$set': {
                        'current_location': {
                            'latitude': float(data['latitude']),
                            'longitude': float(data['longitude']),
                            'updated_at': datetime.utcnow()
                        },
                        'last_seen': datetime.utcnow()
                    }
                }
            )

            # If driver has an active ride, update the rider
            if driver.get('current_ride_id'):
                ride = db.rides.find_one({'_id': driver['current_ride_id']})
                if ride and ride['status'] in ['accepted', 'in_progress']:
                    rider_id = str(ride['rider_id'])
                    socketio.emit('driver_location_update', {
                        'latitude': float(data['latitude']),
                        'longitude': float(data['longitude']),
                        'ride_id': str(ride['_id']),
                        'timestamp': str(datetime.utcnow())
                    }, room=f"user_{rider_id}")

            emit('location_updated', {'status': 'success'})

        except Exception as e:
            logger.error(f"Driver location update error: {e}")
            emit('error', {'message': 'Failed to update location'})

    @socketio.on('join_ride_room')
    def handle_join_ride_room(data):
        """Join a specific ride room for real-time updates"""
        try:
            if request.sid not in connected_clients:
                return

            client_info = connected_clients[request.sid]
            user_id = client_info['user_id']

            if 'ride_id' not in data:
                emit('error', {'message': 'Missing ride_id'})
                return

            ride_id = data['ride_id']

            # Verify user is part of this ride
            db = current_app.db.db
            if db is None:
                emit('error', {'message': 'Database error'})
                return

            ride = db.rides.find_one({'_id': ObjectId(ride_id)})
            if not ride:
                emit('error', {'message': 'Ride not found'})
                return

            # Check if user is rider or driver for this ride
            is_rider = str(ride['rider_id']) == user_id
            is_driver = (ride.get('driver_id') and
                        db.drivers.find_one({'_id': ride['driver_id'], 'user_id': ObjectId(user_id)}))

            if not (is_rider or is_driver):
                emit('error', {'message': 'Not authorized for this ride'})
                return

            # Join ride room
            room_name = f"ride_{ride_id}"
            join_room(room_name)

            emit('joined_ride_room', {'ride_id': ride_id, 'room': room_name})
            logger.info(f"User {user_id} joined ride room {room_name}")

        except Exception as e:
            logger.error(f"Join ride room error: {e}")
            emit('error', {'message': 'Failed to join ride room'})

    @socketio.on('ride_status_update')
    def handle_ride_status_update(data):
        """Handle ride status changes and broadcast to relevant users"""
        try:
            if request.sid not in connected_clients:
                return

            client_info = connected_clients[request.sid]
            user_id = client_info['user_id']

            if 'ride_id' not in data or 'status' not in data:
                emit('error', {'message': 'Missing ride_id or status'})
                return

            ride_id = data['ride_id']
            new_status = data['status']

            # Broadcast to ride room
            room_name = f"ride_{ride_id}"
            socketio.emit('ride_status_changed', {
                'ride_id': ride_id,
                'status': new_status,
                'timestamp': str(datetime.utcnow()),
                'updated_by': user_id
            }, room=room_name)

            logger.info(f"Ride {ride_id} status updated to {new_status} by user {user_id}")

        except Exception as e:
            logger.error(f"Ride status update error: {e}")
            emit('error', {'message': 'Failed to update ride status'})

    @socketio.on('send_message')
    def handle_ride_message(data):
        """Handle messages between rider and driver"""
        try:
            if request.sid not in connected_clients:
                return

            client_info = connected_clients[request.sid]
            user_id = client_info['user_id']
            user_type = client_info['user_type']

            if 'ride_id' not in data or 'message' not in data:
                emit('error', {'message': 'Missing ride_id or message'})
                return

            ride_id = data['ride_id']
            message = data['message']

            # Verify user is part of this ride
            db = current_app.db.db
            if db is None:
                emit('error', {'message': 'Database error'})
                return

            ride = db.rides.find_one({'_id': ObjectId(ride_id)})
            if not ride:
                emit('error', {'message': 'Ride not found'})
                return

            # Get sender info
            user_info = db.users.find_one({'_id': ObjectId(user_id)})
            sender_name = f"{user_info['first_name']} {user_info['last_name']}" if user_info else "User"

            # Broadcast message to ride room
            room_name = f"ride_{ride_id}"
            socketio.emit('new_message', {
                'ride_id': ride_id,
                'message': message,
                'sender_id': user_id,
                'sender_name': sender_name,
                'sender_type': user_type,
                'timestamp': str(datetime.utcnow())
            }, room=room_name)

            logger.info(f"Message sent in ride {ride_id} by {user_id}")

        except Exception as e:
            logger.error(f"Send message error: {e}")
            emit('error', {'message': 'Failed to send message'})

    def notify_ride_accepted(ride_id, driver_info):
        """Notify rider that their ride has been accepted"""
        try:
            db = current_app.db.db
            if db is None:
                return

            ride = db.rides.find_one({'_id': ObjectId(ride_id)})
            if not ride:
                return

            rider_id = str(ride['rider_id'])

            socketio.emit('ride_accepted', {
                'ride_id': ride_id,
                'driver': driver_info,
                'message': 'Your ride has been accepted!',
                'timestamp': str(datetime.utcnow())
            }, room=f"user_{rider_id}")

            logger.info(f"Ride accepted notification sent to rider {rider_id}")

        except Exception as e:
            logger.error(f"Notify ride accepted error: {e}")

    def notify_ride_started(ride_id):
        """Notify rider that their ride has started"""
        try:
            db = current_app.db.db
            if db is None:
                return

            ride = db.rides.find_one({'_id': ObjectId(ride_id)})
            if not ride:
                return

            rider_id = str(ride['rider_id'])

            socketio.emit('ride_started', {
                'ride_id': ride_id,
                'message': 'Your ride has started!',
                'timestamp': str(datetime.utcnow())
            }, room=f"user_{rider_id}")

            logger.info(f"Ride started notification sent to rider {rider_id}")

        except Exception as e:
            logger.error(f"Notify ride started error: {e}")

    def notify_ride_completed(ride_id, fare_info):
        """Notify both rider and driver that ride is completed"""
        try:
            db = current_app.db.db
            if db is None:
                return

            ride = db.rides.find_one({'_id': ObjectId(ride_id)})
            if not ride:
                return

            rider_id = str(ride['rider_id'])

            # Get driver info
            if ride.get('driver_id'):
                driver = db.drivers.find_one({'_id': ride['driver_id']})
                if driver:
                    driver_user_id = str(driver['user_id'])

                    # Notify both rider and driver
                    completion_data = {
                        'ride_id': ride_id,
                        'fare_info': fare_info,
                        'message': 'Ride completed successfully!',
                        'timestamp': str(datetime.utcnow())
                    }

                    socketio.emit('ride_completed', completion_data, room=f"user_{rider_id}")
                    socketio.emit('ride_completed', completion_data, room=f"user_{driver_user_id}")

            logger.info(f"Ride completed notifications sent for ride {ride_id}")

        except Exception as e:
            logger.error(f"Notify ride completed error: {e}")

    # Make notification functions available to other modules
    socketio.notify_ride_accepted = notify_ride_accepted
    socketio.notify_ride_started = notify_ride_started
    socketio.notify_ride_completed = notify_ride_completed