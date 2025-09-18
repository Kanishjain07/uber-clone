from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routes and models
from api.auth import auth_bp
from api.riders import riders_bp
from api.drivers import drivers_bp
from api.rides import rides_bp
from models.db import init_db
from sockets import init_sockets

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # MongoDB configuration
    app.config['MONGO_URI'] = os.getenv("MONGO_URI")
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)

    # Initialize database
    init_db(app)

    # Initialize SocketIO with handlers
    socketio = init_sockets(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(riders_bp, url_prefix='/api/riders')
    app.register_blueprint(drivers_bp, url_prefix='/api/drivers')
    app.register_blueprint(rides_bp, url_prefix='/api/rides')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Uber Clone Backend is running'})
    
    return app, socketio

# Create app instance
app, socketio = create_app()

if __name__ == '__main__':
    port = 5000
    print("Starting Uber Clone Backend...")
    print(f"API: http://localhost:{port}")
    print(f"WebSocket: ws://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/health")

    socketio.run(
        app,
        host='127.0.0.1',
        port=port,
        debug=True,
        use_reloader=True
    )
