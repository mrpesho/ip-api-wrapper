"""
Main IP-API client implementation
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from urllib.parse import urljoin
import requests

from .exceptions import (
    IPAPIError,
    RateLimitError,
    InvalidResponseError,
    InvalidIPError,
    BatchLimitError,
    BatchValidationError,
    ServerRateLimitError,
)


@dataclass
class ResponseMetadata:
    """Metadata from API response headers"""
    requests_remaining: Optional[int] = None  # X-Rl header
    seconds_until_reset: Optional[int] = None  # X-Ttl header

    @classmethod
    def from_headers(cls, headers: dict) -> 'ResponseMetadata':
        """Extract metadata from response headers"""
        return cls(
            requests_remaining=int(headers.get('X-Rl', -1)) if 'X-Rl' in headers else None,
            seconds_until_reset=int(headers.get('X-Ttl', -1)) if 'X-Ttl' in headers else None
        )


class IPAPIClient:
    """
    Client for interacting with ip-api.com API

    Supports:
    - Single IP lookups
    - Batch IP lookups
    - DNS lookups
    - Custom field selection
    - Multiple output formats (JSON, XML, CSV)
    - Pro tier support with HTTPS
    """

    BATCH_LIMIT = 100

    # Available fields for queries
    AVAILABLE_FIELDS = [
        "status", "message", "continent", "continentCode", "country",
        "countryCode", "region", "regionName", "city", "district",
        "zip", "lat", "lon", "timezone", "offset", "currency",
        "isp", "org", "as", "asname", "reverse", "mobile",
        "proxy", "hosting", "query"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        lang: str = "en",
        timeout: int = 10,
    ):
        """
        Initialize IP-API client

        Args:
            api_key: Optional API key for pro features (paid plans)
            lang: Language for location names (en, de, es, pt-BR, fr, ja, zh-CN, ru)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.lang = lang
        self.timeout = timeout
        self.session = requests.Session()

        # Rate limiting for free tier
        self._single_rate_limit = 45  # requests per minute for single lookups
        self._batch_rate_limit = 15   # requests per minute for batch operations
        self._rate_window = 60
        self._single_request_times: List[float] = []
        self._batch_request_times: List[float] = []

        # Response metadata tracking
        self.last_response_metadata: Optional[ResponseMetadata] = None

    @property
    def base_url(self) -> str:
        """
        Get base URL based on tier

        Returns:
            HTTP URL for free tier, HTTPS URL for pro tier
        """
        if self.api_key:
            return "https://pro.ip-api.com"
        return "http://ip-api.com"

    @property
    def _is_pro_tier(self) -> bool:
        """Check if using pro tier (has API key)"""
        return self.api_key is not None

    def _check_single_rate_limit(self):
        """Check if we're within rate limits for single requests (45/min)"""
        # Pro tier has unlimited requests
        if self._is_pro_tier:
            return

        now = time.time()
        # Remove requests older than the rate window
        self._single_request_times = [
            t for t in self._single_request_times if now - t < self._rate_window
        ]

        if len(self._single_request_times) >= self._single_rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded: {self._single_rate_limit} requests per {self._rate_window} seconds"
            )

        self._single_request_times.append(now)

    def _check_batch_rate_limit(self):
        """Check if we're within rate limits for batch requests (15/min)"""
        # Pro tier has unlimited requests
        if self._is_pro_tier:
            return

        now = time.time()
        # Remove requests older than the rate window
        self._batch_request_times = [
            t for t in self._batch_request_times if now - t < self._rate_window
        ]

        if len(self._batch_request_times) >= self._batch_rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded: {self._batch_rate_limit} requests per {self._rate_window} seconds"
            )

        self._batch_request_times.append(now)

    def _convert_fields_to_param(self, fields: Union[List[str], int]) -> str:
        """
        Convert fields parameter to query string format

        Args:
            fields: Either a list of field names or an integer bit mask

        Returns:
            Comma-separated string of field names or string representation of bit mask

        Raises:
            ValueError: If fields list contains invalid field names
            TypeError: If fields is neither List[str] nor int
        """
        if isinstance(fields, int):
            # Numeric bit mask - return as string
            return str(fields)
        elif isinstance(fields, list):
            # Validate field names
            invalid_fields = set(fields) - set(self.AVAILABLE_FIELDS)
            if invalid_fields:
                raise ValueError(f"Invalid fields: {invalid_fields}")
            return ",".join(fields)
        else:
            raise TypeError("fields must be List[str] or int")

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Union[Dict, List, str]:
        """
        Make HTTP request to API

        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request body data
            params: Query parameters

        Returns:
            Response data
        """
        # Add API key to params if present (pro tier)
        if self.api_key:
            if params is None:
                params = {}
            params["key"] = self.api_key

        url = urljoin(self.base_url, endpoint)

        try:
            if method == "GET":
                response = self.session.get(
                    url, params=params, timeout=self.timeout
                )
            elif method == "POST":
                response = self.session.post(
                    url, json=data, params=params, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check for specific HTTP error codes before raise_for_status()
            if response.status_code == 422:
                raise BatchValidationError(
                    "Batch request validation failed (>100 items or invalid format)"
                )
            elif response.status_code == 429:
                ttl = response.headers.get('X-Ttl')
                raise ServerRateLimitError(
                    f"Rate limit exceeded. Reset in {ttl} seconds" if ttl else "Rate limit exceeded",
                    seconds_until_reset=int(ttl) if ttl else None
                )

            response.raise_for_status()

            # Parse response metadata from headers
            self.last_response_metadata = ResponseMetadata.from_headers(response.headers)

            # Handle different content types
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                return response.json()
            elif "text/xml" in content_type or "application/xml" in content_type:
                return response.text
            elif "text/csv" in content_type:
                return response.text
            elif "text/plain" in content_type:
                # Newline-separated format (line)
                return response.text
            elif "php" in content_type or "serialized" in content_type:
                # Serialized PHP format
                return response.text
            else:
                return response.text

        except requests.exceptions.Timeout:
            raise IPAPIError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise IPAPIError(f"Request failed: {str(e)}")

    def lookup(
        self,
        ip: Optional[str] = None,
        fields: Optional[Union[List[str], int]] = None,
        format: str = "json",
        callback: Optional[str] = None,
    ) -> Union[Dict, str]:
        """
        Lookup information for a single IP address

        Args:
            ip: IP address to lookup (None for current IP)
            fields: List of field names or numeric bit mask (None for all fields)
            format: Response format (json, xml, csv, line, php)
            callback: JSONP callback function name (only works with json format)

        Returns:
            IP information
        """
        # Check rate limit for single requests
        self._check_single_rate_limit()

        # Validate callback parameter
        if callback and format != "json":
            raise ValueError("callback parameter only works with JSON format")

        # Build endpoint
        if ip:
            endpoint = f"/{format}/{ip}"
        else:
            endpoint = f"/{format}"

        # Build query parameters
        params = {}
        if fields is not None:
            params["fields"] = self._convert_fields_to_param(fields)

        if callback:
            params["callback"] = callback

        if self.lang != "en":
            params["lang"] = self.lang

        response = self._make_request(endpoint, params=params)

        # Check for error in response
        if isinstance(response, dict) and response.get("status") == "fail":
            message = response.get("message", "Unknown error")
            if "invalid" in message.lower():
                raise InvalidIPError(message)
            raise IPAPIError(message)

        return response

    def batch(
        self,
        ips: List[str],
        fields: Optional[Union[List[str], int]] = None,
    ) -> List[Dict]:
        """
        Lookup information for multiple IP addresses in a single request

        Args:
            ips: List of IP addresses (max 100 for free tier)
            fields: List of field names or numeric bit mask (None for all fields)

        Returns:
            List of IP information dictionaries
        """
        # Check rate limit for batch requests
        self._check_batch_rate_limit()

        if len(ips) > self.BATCH_LIMIT:
            raise BatchLimitError(
                f"Batch limit exceeded: {len(ips)} IPs (max {self.BATCH_LIMIT})"
            )

        if not ips:
            raise ValueError("IP list cannot be empty")

        # Build request data
        batch_data = []
        for ip in ips:
            item = {"query": ip}
            if fields is not None:
                item["fields"] = self._convert_fields_to_param(fields)
            if self.lang != "en":
                item["lang"] = self.lang
            batch_data.append(item)

        response = self._make_request("/batch", method="POST", data=batch_data)

        if not isinstance(response, list):
            raise InvalidResponseError("Expected list response from batch endpoint")

        return response

    def dns_lookup(
        self,
        domain: str,
        fields: Optional[Union[List[str], int]] = None,
        callback: Optional[str] = None,
    ) -> Union[Dict, str]:
        """
        Perform DNS lookup and get IP geolocation information

        Args:
            domain: Domain name to lookup
            fields: List of field names or numeric bit mask (None for all fields)
            callback: JSONP callback function name

        Returns:
            IP information for the domain
        """
        # Check rate limit for single requests
        self._check_single_rate_limit()

        endpoint = f"/json/{domain}"

        params = {}
        if fields is not None:
            params["fields"] = self._convert_fields_to_param(fields)

        if callback:
            params["callback"] = callback

        if self.lang != "en":
            params["lang"] = self.lang

        response = self._make_request(endpoint, params=params)

        if isinstance(response, dict) and response.get("status") == "fail":
            message = response.get("message", "Unknown error")
            raise IPAPIError(message)

        return response

    def batch_dns(
        self,
        domains: List[str],
        fields: Optional[Union[List[str], int]] = None,
    ) -> List[Dict]:
        """
        Batch DNS lookup for multiple domains

        Args:
            domains: List of domain names (max 100)
            fields: List of field names or numeric bit mask (None for all fields)

        Returns:
            List of IP information dictionaries
        """
        # Check rate limit for batch requests
        self._check_batch_rate_limit()

        if len(domains) > self.BATCH_LIMIT:
            raise BatchLimitError(
                f"Batch limit exceeded: {len(domains)} domains (max {self.BATCH_LIMIT})"
            )

        if not domains:
            raise ValueError("Domain list cannot be empty")

        batch_data = []
        for domain in domains:
            item = {"query": domain}
            if fields is not None:
                item["fields"] = self._convert_fields_to_param(fields)
            if self.lang != "en":
                item["lang"] = self.lang
            batch_data.append(item)

        response = self._make_request("/batch", method="POST", data=batch_data)

        if not isinstance(response, list):
            raise InvalidResponseError("Expected list response from batch endpoint")

        return response

    def get_rate_limit_info(self) -> Optional[ResponseMetadata]:
        """
        Get rate limit information from last API response

        Returns:
            ResponseMetadata object with requests_remaining and seconds_until_reset,
            or None if no requests have been made yet
        """
        return self.last_response_metadata

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
