"""
Custom exceptions for IP-API wrapper
"""


class IPAPIError(Exception):
    """Base exception for IP-API errors"""
    pass


class RateLimitError(IPAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class InvalidResponseError(IPAPIError):
    """Raised when API returns invalid response"""
    pass


class InvalidIPError(IPAPIError):
    """Raised when an invalid IP address is provided"""
    pass


class BatchLimitError(IPAPIError):
    """Raised when batch request exceeds the allowed limit"""
    pass
