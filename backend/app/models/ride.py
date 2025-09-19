"""
Ride models
"""
from .base import BaseModel

class Ride(BaseModel):
    collection_name = 'rides'

class RideRequest(BaseModel):
    collection_name = 'ride_requests'