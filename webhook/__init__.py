"""
Cheqroom Webhook Service
Real-time updates for check-in/check-out events with signature verification and row locking.
"""

__version__ = "1.0.0"
__author__ = "Property-Office-DSS Team"

from .app import app
from .config import settings

__all__ = ["app", "settings"]
