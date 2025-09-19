"""
Rider API endpoints
"""
from flask import Blueprint

riders_bp = Blueprint('riders', __name__)

@riders_bp.route('/', methods=['GET'])
def get_riders():
    return {'message': 'Riders API - Coming Soon'}