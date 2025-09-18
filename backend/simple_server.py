#!/usr/bin/env python3
"""
Simple test server to verify fixes
"""
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Simple server running'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({'success': True, 'message': 'Login endpoint working'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    return jsonify({'success': True, 'message': 'Register endpoint working'})

if __name__ == '__main__':
    print("Starting Simple Test Server...")
    print("API: http://localhost:8080")
    print("Health Check: http://localhost:8080/health")

    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True,
        threaded=True
    )