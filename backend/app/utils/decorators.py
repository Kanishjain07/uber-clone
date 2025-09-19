"""
Utility decorators
"""
import functools
import logging
from flask import jsonify, current_app

logger = logging.getLogger(__name__)


def handle_errors(f):
    """Decorator to handle common exceptions"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({'error': 'Invalid input', 'message': str(e)}), 400
        except KeyError as e:
            logger.warning(f"Missing key in {f.__name__}: {e}")
            return jsonify({'error': 'Missing required field', 'field': str(e)}), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            if current_app.debug:
                return jsonify({'error': 'Internal server error', 'debug': str(e)}), 500
            return jsonify({'error': 'Internal server error'}), 500
    return wrapper


def require_json(f):
    """Decorator to ensure request contains JSON data"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        return f(*args, **kwargs)
    return wrapper


def validate_user_type(allowed_types):
    """Decorator to validate user type from JWT claims"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import get_jwt
            claims = get_jwt()
            user_type = claims.get('user_type')

            if user_type not in allowed_types:
                return jsonify({'error': 'Access denied for user type'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(requests_per_minute=60):
    """Simple rate limiting decorator (in production, use Redis)"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # In a real application, implement proper rate limiting
            # using Redis or similar storage
            return f(*args, **kwargs)
        return wrapper
    return decorator


def log_request(f):
    """Decorator to log API requests"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request
        logger.info(f"API call: {request.method} {request.path} from {request.remote_addr}")
        return f(*args, **kwargs)
    return wrapper