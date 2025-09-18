from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# API endpoints
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Uber Clone Backend with WebSocket is running'})

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

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Successfully connected to WebSocket server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('authenticate')
def handle_authenticate(data):
    print(f'Client authenticated: {data}')
    emit('authenticated', {'success': True, 'message': 'Authentication successful'})

@socketio.on('ping')
def handle_ping(data):
    print(f'Ping received: {data}')
    emit('pong', {'timestamp': data.get('timestamp', 0)})

@socketio.on('ride_request')
def handle_ride_request(data):
    print(f'Ride request received: {data}')
    # Echo back the ride request
    emit('ride_update', {
        'rideId': '12345',
        'status': 'searching',
        'message': 'Searching for nearby drivers...'
    })

@socketio.on('driver_location')
def handle_driver_location(data):
    print(f'Driver location update: {data}')
    # Broadcast to other clients if needed
    emit('driver_location_update', data, broadcast=True)

if __name__ == '__main__':
    port = 9002
    print("Starting Uber Clone Backend with WebSocket...")
    print(f"API: http://localhost:{port}")
    print(f"WebSocket: ws://localhost:{port}")
    print(f"Health: http://localhost:{port}/health")

    socketio.run(
        app,
        host='127.0.0.1',
        port=port,
        debug=True,
        use_reloader=False
    )