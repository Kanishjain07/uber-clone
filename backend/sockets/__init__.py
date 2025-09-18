from flask_socketio import SocketIO
from .driver_socket import init_driver_socket
from .rider_socket import init_rider_socket

def init_sockets(app):
    """Initialize all socket handlers"""
    
    # Create SocketIO instance
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=True
    )
    
    # Initialize driver and rider socket handlers
    init_driver_socket(socketio)
    init_rider_socket(socketio)
    
    return socketio
