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


class BatchValidationError(IPAPIError):
    """Raised when batch request validation fails (HTTP 422)"""
    pass


class ServerRateLimitError(RateLimitError):
    """Raised when server returns HTTP 429 (rate limit exceeded)"""

    def __init__(self, message: str, seconds_until_reset: int = None):
        """
        Initialize ServerRateLimitError

        Args:
            message: Error message
            seconds_until_reset: Seconds until rate limit resets (from X-Ttl header)
        """
        super().__init__(message)
        self.seconds_until_reset = seconds_until_reset
