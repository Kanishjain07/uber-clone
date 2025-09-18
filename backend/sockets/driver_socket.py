from flask_socketio import emit, join_room, leave_room
from flask import request
import logging
from models.db import get_db
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_driver_socket(socketio):
    """Initialize driver socket event handlers"""
    
    @socketio.on('driver_connect')
    def handle_driver_connect(data):
        """Handle driver connection"""
        try:
            driver_id = data.get('driver_id')
            if driver_id:
                # Join driver's personal room
                join_room(f'driver_{driver_id}')
                
                # Update driver's online status
                db = get_db()
                db.drivers.update_one(
                    {'user_id': driver_id},
                    {
                        '$set': {
                            'socket_id': request.sid,
                            'last_seen': datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"🚗 Driver {driver_id} connected with socket {request.sid}")
                emit('driver_connected', {'status': 'connected', 'driver_id': driver_id})
            else:
                emit('error', {'message': 'Driver ID required'})
                
        except Exception as e:
            logger.error(f"❌ Driver connect error: {e}")
            emit('error', {'message': 'Connection failed'})
    
    @socketio.on('driver_disconnect')
    def handle_driver_disconnect(data):
        """Handle driver disconnection"""
        try:
            driver_id = data.get('driver_id')
            if driver_id:
                # Leave driver's room
                leave_room(f'driver_{driver_id}')
                
                # Update driver's offline status
                db = get_db()
                db.drivers.update_one(
                    {'user_id': driver_id},
                    {
                        '$set': {
                            'is_online': False,
                            'socket_id': None,
                            'last_seen': datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"🚗 Driver {driver_id} disconnected")
                emit('driver_disconnected', {'status': 'disconnected'})
                
        except Exception as e:
            logger.error(f"❌ Driver disconnect error: {e}")
    
    @socketio.on('update_location')
    def handle_location_update(data):
        """Handle driver location updates"""
        try:
            driver_id = data.get('driver_id')
            location = data.get('location')
            
            if not driver_id or not location:
                emit('error', {'message': 'Driver ID and location required'})
                return
            
            # Validate location data
            if not isinstance(location, dict) or 'lat' not in location or 'lng' not in location:
                emit('error', {'message': 'Invalid location format'})
                return
            
            # Update driver location in database
            db = get_db()
            db.drivers.update_one(
                {'user_id': driver_id},
                {
                    '$set': {
                        'current_location': location,
                        'last_location_update': datetime.utcnow()
                    }
                }
            )
            
            # Also update driver_locations collection for real-time tracking
            db.driver_locations.update_one(
                {'driver_id': driver_id},
                {
                    '$set': {
                        'location': location,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Broadcast location update to relevant riders (if any)
            # This would typically be filtered based on proximity
            emit('location_updated', {
                'driver_id': driver_id,
                'location': location,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
            
            logger.info(f"📍 Driver {driver_id} location updated: {location}")
            
        except Exception as e:
            logger.error(f"❌ Location update error: {e}")
            emit('error', {'message': 'Location update failed'})
    
    @socketio.on('ride_request')
    def handle_ride_request(data):
        """Handle incoming ride requests for drivers"""
        try:
            driver_id = data.get('driver_id')
            ride_id = data.get('ride_id')
            
            if not driver_id or not ride_id:
                emit('error', {'message': 'Driver ID and ride ID required'})
                return
            
            # Get ride details
            db = get_db()
            ride = db.rides.find_one({'_id': ride_id})
            if not ride:
                emit('error', {'message': 'Ride not found'})
                return
            
            # Check if driver is available
            driver = db.drivers.find_one({'user_id': driver_id})
            if not driver or not driver.get('is_online'):
                emit('error', {'message': 'Driver not available'})
                return
            
            # Send ride request to driver
            emit('new_ride_request', {
                'ride_id': ride_id,
                'pickup': ride['pickup_location'],
                'destination': ride['destination_location'],
                'estimated_fare': ride['estimated_fare'],
                'ride_type': ride['ride_type']
            }, room=f'driver_{driver_id}')
            
            logger.info(f"🚗 Ride request {ride_id} sent to driver {driver_id}")
            
        except Exception as e:
            logger.error(f"❌ Ride request error: {e}")
            emit('error', {'message': 'Ride request failed'})
    
    @socketio.on('accept_ride')
    def handle_ride_acceptance(data):
        """Handle driver accepting a ride"""
        try:
            driver_id = data.get('driver_id')
            ride_id = data.get('ride_id')
            
            if not driver_id or not ride_id:
                emit('error', {'message': 'Driver ID and ride ID required'})
                return
            
            # Update ride status in database
            db = get_db()
            result = db.rides.update_one(
                {'_id': ride_id},
                {
                    '$set': {
                        'driver_id': driver_id,
                        'status': 'accepted',
                        'accepted_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update driver status
                db.drivers.update_one(
                    {'user_id': driver_id},
                    {
                        '$set': {
                            'current_ride_id': ride_id,
                            'is_online': False
                        }
                    }
                )
                
                # Get ride details for notification
                ride = db.rides.find_one({'_id': ride_id})
                if ride:
                    # Notify rider that ride was accepted
                    emit('ride_accepted', {
                        'ride_id': ride_id,
                        'driver_id': driver_id,
                        'message': 'Your ride has been accepted!'
                    }, room=f'rider_{ride["rider_id"]}')
                
                logger.info(f"✅ Driver {driver_id} accepted ride {ride_id}")
                emit('ride_accepted_success', {'message': 'Ride accepted successfully'})
            else:
                emit('error', {'message': 'Failed to accept ride'})
                
        except Exception as e:
            logger.error(f"❌ Ride acceptance error: {e}")
            emit('error', {'message': 'Ride acceptance failed'})
    
    @socketio.on('start_ride')
    def handle_ride_start(data):
        """Handle driver starting a ride"""
        try:
            driver_id = data.get('driver_id')
            ride_id = data.get('ride_id')
            
            if not driver_id or not ride_id:
                emit('error', {'message': 'Driver ID and ride ID required'})
                return
            
            # Update ride status
            db = get_db()
            result = db.rides.update_one(
                {'_id': ride_id},
                {
                    '$set': {
                        'status': 'started',
                        'started_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Get ride details for notification
                ride = db.rides.find_one({'_id': ride_id})
                if ride:
                    # Notify rider that ride has started
                    emit('ride_started', {
                        'ride_id': ride_id,
                        'message': 'Your ride has started!'
                    }, room=f'rider_{ride["rider_id"]}')
                
                logger.info(f"🚗 Driver {driver_id} started ride {ride_id}")
                emit('ride_started_success', {'message': 'Ride started successfully'})
            else:
                emit('error', {'message': 'Failed to start ride'})
                
        except Exception as e:
            logger.error(f"❌ Ride start error: {e}")
            emit('error', {'message': 'Ride start failed'})
    
    @socketio.on('complete_ride')
    def handle_ride_completion(data):
        """Handle driver completing a ride"""
        try:
            driver_id = data.get('driver_id')
            ride_id = data.get('ride_id')
            
            if not driver_id or not ride_id:
                emit('error', {'message': 'Driver ID and ride ID required'})
                return
            
            # Update ride status
            db = get_db()
            result = db.rides.update_one(
                {'_id': ride_id},
                {
                    '$set': {
                        'status': 'completed',
                        'completed_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update driver status
                db.drivers.update_one(
                    {'user_id': driver_id},
                    {
                        '$set': {
                            'current_ride_id': None,
                            'is_online': True
                        }
                    }
                )
                
                # Get ride details for notification
                ride = db.rides.find_one({'_id': ride_id})
                if ride:
                    # Notify rider that ride is completed
                    emit('ride_completed', {
                        'ride_id': ride_id,
                        'message': 'Your ride has been completed!'
                    }, room=f'rider_{ride["rider_id"]}')
                
                logger.info(f"✅ Driver {driver_id} completed ride {ride_id}")
                emit('ride_completed_success', {'message': 'Ride completed successfully'})
            else:
                emit('error', {'message': 'Failed to complete ride'})
                
        except Exception as e:
            logger.error(f"❌ Ride completion error: {e}")
            emit('error', {'message': 'Ride completion failed'})
    
    @socketio.on('driver_status_update')
    def handle_status_update(data):
        """Handle driver status updates (online/offline)"""
        try:
            driver_id = data.get('driver_id')
            status = data.get('status')  # 'online' or 'offline'
            
            if not driver_id or status not in ['online', 'offline']:
                emit('error', {'message': 'Invalid driver ID or status'})
                return
            
            # Update driver status in database
            db = get_db()
            is_online = status == 'online'
            
            result = db.drivers.update_one(
                {'user_id': driver_id},
                {
                    '$set': {
                        'is_online': is_online,
                        'status_updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🚗 Driver {driver_id} status updated to {status}")
                emit('status_updated', {
                    'driver_id': driver_id,
                    'status': status,
                    'message': f'Driver status updated to {status}'
                })
            else:
                emit('error', {'message': 'Failed to update status'})
                
        except Exception as e:
            logger.error(f"❌ Status update error: {e}")
            emit('error', {'message': 'Status update failed'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            # Find driver by socket ID and mark as offline
            db = get_db()
            driver = db.drivers.find_one({'socket_id': request.sid})
            
            if driver:
                db.drivers.update_one(
                    {'user_id': driver['user_id']},
                    {
                        '$set': {
                            'is_online': False,
                            'socket_id': None,
                            'last_seen': datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"🚗 Driver {driver['user_id']} disconnected unexpectedly")
                
        except Exception as e:
            logger.error(f"❌ Disconnect handling error: {e}")
    
    logger.info("✅ Driver socket handlers initialized")
