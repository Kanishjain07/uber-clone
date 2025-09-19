"""
Flask application factory
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from config.settings import get_config
from app.extensions import db, socketio, jwt
from app.api import register_blueprints
from app.websockets import register_socketio_handlers


def create_app(config_name=None):
    """Create Flask application using factory pattern"""

    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register socket handlers
    register_socketio_handlers(socketio)

    # Error handlers
    register_error_handlers(app)

    return app, socketio


def init_extensions(app):
    """Initialize Flask extensions"""

    # Database
    db.init_app(app)

    # JWT
    jwt.init_app(app)

    # SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=True
    )

    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'message': str(error)}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'Insufficient permissions'}, 403

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': 'Resource not found'}, 404

    @app.errorhandler(409)
    def conflict(error):
        return {'error': 'Conflict', 'message': str(error)}, 409

    @app.errorhandler(422)
    def validation_error(error):
        return {'error': 'Validation error', 'message': str(error)}, 422

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error', 'message': 'Something went wrong'}, 500

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'service': 'uber-clone-api',
            'version': app.config.get('API_VERSION', 'v1')
        }

    @app.route('/')
    def root():
        return {
            'message': 'Uber Clone API',
            'version': app.config.get('API_VERSION', 'v1'),
            'documentation': '/api/v1/docs'
        }