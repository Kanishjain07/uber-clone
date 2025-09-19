"""
Notification API endpoints
"""
from flask import Blueprint

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    return {'message': 'Notifications API - Coming Soon'}