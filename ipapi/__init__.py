"""
IP-API Python Wrapper
A comprehensive Python wrapper for the ip-api.com geolocation API service.
"""

from .client import IPAPIClient, ResponseMetadata
from .exceptions import (
    IPAPIError,
    RateLimitError,
    InvalidResponseError,
    InvalidIPError,
    BatchLimitError,
    BatchValidationError,
    ServerRateLimitError,
)

__version__ = "0.1.0"
__all__ = [
    "IPAPIClient",
    "ResponseMetadata",
    "IPAPIError",
    "RateLimitError",
    "InvalidResponseError",
    "InvalidIPError",
    "BatchLimitError",
    "BatchValidationError",
    "ServerRateLimitError",
]
