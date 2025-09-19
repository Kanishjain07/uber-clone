"""
API Blueprint registration
"""
from flask import Blueprint

from .auth import auth_bp
from .riders import riders_bp
from .drivers import drivers_bp
from .rides import rides_bp
from .payments import payments_bp
from .notifications import notifications_bp


def register_blueprints(app):
    """Register all API blueprints"""

    # Create main API blueprint
    api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

    # API documentation endpoint
    @api_v1.route('/docs')
    def api_docs():
        return {
            'title': 'Uber Clone API Documentation',
            'version': 'v1',
            'endpoints': {
                'auth': '/api/v1/auth',
                'riders': '/api/v1/riders',
                'drivers': '/api/v1/drivers',
                'rides': '/api/v1/rides',
                'payments': '/api/v1/payments',
                'notifications': '/api/v1/notifications'
            },
            'websocket': 'ws://localhost:5000',
            'health_check': '/health'
        }

    # Register sub-blueprints
    api_v1.register_blueprint(auth_bp, url_prefix='/auth')
    api_v1.register_blueprint(riders_bp, url_prefix='/riders')
    api_v1.register_blueprint(drivers_bp, url_prefix='/drivers')
    api_v1.register_blueprint(rides_bp, url_prefix='/rides')
    api_v1.register_blueprint(payments_bp, url_prefix='/payments')
    api_v1.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Register main API blueprint with app
    app.register_blueprint(api_v1)