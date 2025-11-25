"""
IP-API Python Wrapper
A comprehensive Python wrapper for the ip-api.com geolocation API service.
"""

from .client import IPAPIClient
from .exceptions import IPAPIError, RateLimitError, InvalidResponseError

__version__ = "0.0.1"
__all__ = ["IPAPIClient", "IPAPIError", "RateLimitError", "InvalidResponseError"]
