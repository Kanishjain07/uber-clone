from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize SocketIO with handlers
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Mock API endpoints
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Uber Clone Backend is running'})

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json() or {}
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': '1',
                'name': 'Demo User',
                'email': data.get('email', 'demo@example.com') if isinstance(data, dict) else 'demo@example.com',
                'userType': 'rider'
            },
            'token': 'mock-jwt-token-12345'
        })

    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json() or {}
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': '2',
                'name': data.get('name', 'New User') if isinstance(data, dict) else 'New User',
                'email': data.get('email', 'newuser@example.com') if isinstance(data, dict) else 'newuser@example.com',
                'userType': 'rider'
            },
            'token': 'mock-jwt-token-67890'
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app, socketio

# Create app instance
app, socketio = create_app()

if __name__ == '__main__':
    port = 9000
    print("Starting Uber Clone Backend (No MongoDB)...")
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