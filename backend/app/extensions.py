"""
Flask extensions initialization
"""
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from app.database import Database

# Initialize extensions
db = Database()
jwt = JWTManager()
socketio = SocketIO()