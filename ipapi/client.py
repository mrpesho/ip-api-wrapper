"""
Main IP-API client implementation
"""

import time
from typing import List, Dict, Optional, Union
from urllib.parse import urljoin
import requests

from .exceptions import (
    IPAPIError,
    RateLimitError,
    InvalidResponseError,
    InvalidIPError,
    BatchLimitError,
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
    """

    BASE_URL = "http://ip-api.com"
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

        # Rate limiting (free tier: 45 requests per minute)
        self.rate_limit = 45
        self.rate_window = 60
        self.request_times: List[float] = []

    def _check_rate_limit(self):
        """Check if we're within rate limits"""
        now = time.time()
        # Remove requests older than the rate window
        self.request_times = [t for t in self.request_times if now - t < self.rate_window]

        if len(self.request_times) >= self.rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded: {self.rate_limit} requests per {self.rate_window} seconds"
            )

        self.request_times.append(now)

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
        self._check_rate_limit()

        url = urljoin(self.BASE_URL, endpoint)

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

            response.raise_for_status()

            # Handle different content types
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                return response.json()
            elif "text/xml" in content_type or "application/xml" in content_type:
                return response.text
            elif "text/csv" in content_type:
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
        fields: Optional[List[str]] = None,
        format: str = "json",
    ) -> Union[Dict, str]:
        """
        Lookup information for a single IP address

        Args:
            ip: IP address to lookup (None for current IP)
            fields: List of fields to return (None for all fields)
            format: Response format (json, xml, csv, line)

        Returns:
            IP information
        """
        # Build endpoint
        if ip:
            endpoint = f"/{format}/{ip}"
        else:
            endpoint = f"/{format}"

        # Build query parameters
        params = {}
        if fields:
            # Validate fields
            invalid_fields = set(fields) - set(self.AVAILABLE_FIELDS)
            if invalid_fields:
                raise ValueError(f"Invalid fields: {invalid_fields}")
            params["fields"] = ",".join(fields)

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
        fields: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Lookup information for multiple IP addresses in a single request

        Args:
            ips: List of IP addresses (max 100 for free tier)
            fields: List of fields to return (None for all fields)

        Returns:
            List of IP information dictionaries
        """
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
            if fields:
                invalid_fields = set(fields) - set(self.AVAILABLE_FIELDS)
                if invalid_fields:
                    raise ValueError(f"Invalid fields: {invalid_fields}")
                item["fields"] = ",".join(fields)
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
        fields: Optional[List[str]] = None,
    ) -> Union[Dict, str]:
        """
        Perform DNS lookup and get IP geolocation information

        Args:
            domain: Domain name to lookup
            fields: List of fields to return (None for all fields)

        Returns:
            IP information for the domain
        """
        endpoint = f"/json/{domain}"

        params = {}
        if fields:
            invalid_fields = set(fields) - set(self.AVAILABLE_FIELDS)
            if invalid_fields:
                raise ValueError(f"Invalid fields: {invalid_fields}")
            params["fields"] = ",".join(fields)

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
        fields: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Batch DNS lookup for multiple domains

        Args:
            domains: List of domain names (max 100)
            fields: List of fields to return (None for all fields)

        Returns:
            List of IP information dictionaries
        """
        if len(domains) > self.BATCH_LIMIT:
            raise BatchLimitError(
                f"Batch limit exceeded: {len(domains)} domains (max {self.BATCH_LIMIT})"
            )

        if not domains:
            raise ValueError("Domain list cannot be empty")

        batch_data = []
        for domain in domains:
            item = {"query": domain}
            if fields:
                invalid_fields = set(fields) - set(self.AVAILABLE_FIELDS)
                if invalid_fields:
                    raise ValueError(f"Invalid fields: {invalid_fields}")
                item["fields"] = ",".join(fields)
            if self.lang != "en":
                item["lang"] = self.lang
            batch_data.append(item)

        response = self._make_request("/batch", method="POST", data=batch_data)

        if not isinstance(response, list):
            raise InvalidResponseError("Expected list response from batch endpoint")

        return response

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
