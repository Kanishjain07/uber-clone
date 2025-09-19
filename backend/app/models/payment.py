"""
Payment model
"""
from .base import BaseModel

class Payment(BaseModel):
    collection_name = 'payments'