"""
Payment API endpoints
"""
from flask import Blueprint

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/', methods=['GET'])
def get_payments():
    return {'message': 'Payments API - Coming Soon'}