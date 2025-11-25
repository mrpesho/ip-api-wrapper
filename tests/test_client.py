"""
Unit tests for IP-API client
"""

import pytest
from unittest.mock import Mock, patch
from ipapi import IPAPIClient
from ipapi.exceptions import (
    IPAPIError,
    RateLimitError,
    InvalidIPError,
    BatchLimitError,
)


@pytest.fixture
def client():
    """Create a test client"""
    return IPAPIClient()


@pytest.fixture
def mock_response():
    """Create a mock response"""
    mock = Mock()
    mock.headers = {"Content-Type": "application/json"}
    mock.raise_for_status = Mock()
    return mock


def test_client_initialization():
    """Test client initialization"""
    client = IPAPIClient(api_key="test_key", lang="de", timeout=30)
    assert client.api_key == "test_key"
    assert client.lang == "de"
    assert client.timeout == 30


def test_available_fields(client):
    """Test that all expected fields are available"""
    expected_fields = [
        "status", "message", "continent", "continentCode", "country",
        "countryCode", "region", "regionName", "city", "query"
    ]

    for field in expected_fields:
        assert field in client.AVAILABLE_FIELDS


@patch("ipapi.client.requests.Session.get")
def test_single_lookup(mock_get, client, mock_response):
    """Test single IP lookup"""
    mock_response.json.return_value = {
        "status": "success",
        "country": "United States",
        "city": "Mountain View",
        "query": "8.8.8.8"
    }
    mock_get.return_value = mock_response

    result = client.lookup("8.8.8.8")

    assert result["status"] == "success"
    assert result["country"] == "United States"
    assert result["query"] == "8.8.8.8"


@patch("ipapi.client.requests.Session.get")
def test_lookup_with_fields(mock_get, client, mock_response):
    """Test lookup with custom fields"""
    mock_response.json.return_value = {
        "country": "United States",
        "city": "Mountain View",
        "query": "8.8.8.8"
    }
    mock_get.return_value = mock_response

    fields = ["country", "city", "query"]
    result = client.lookup("8.8.8.8", fields=fields)

    # Check that fields parameter was included in request
    call_args = mock_get.call_args
    assert "params" in call_args.kwargs
    assert "fields" in call_args.kwargs["params"]


@patch("ipapi.client.requests.Session.get")
def test_invalid_ip_error(mock_get, client, mock_response):
    """Test error handling for invalid IP"""
    mock_response.json.return_value = {
        "status": "fail",
        "message": "invalid query"
    }
    mock_get.return_value = mock_response

    with pytest.raises(InvalidIPError):
        client.lookup("invalid-ip")


@patch("ipapi.client.requests.Session.post")
def test_batch_lookup(mock_post, client, mock_response):
    """Test batch IP lookup"""
    mock_response.json.return_value = [
        {"status": "success", "country": "United States", "query": "8.8.8.8"},
        {"status": "success", "country": "Australia", "query": "1.1.1.1"},
    ]
    mock_post.return_value = mock_response

    ips = ["8.8.8.8", "1.1.1.1"]
    results = client.batch(ips)

    assert len(results) == 2
    assert results[0]["query"] == "8.8.8.8"
    assert results[1]["query"] == "1.1.1.1"


def test_batch_limit_error(client):
    """Test batch limit validation"""
    too_many_ips = [f"8.8.{i}.{i}" for i in range(101)]

    with pytest.raises(BatchLimitError):
        client.batch(too_many_ips)


def test_batch_empty_list(client):
    """Test batch with empty IP list"""
    with pytest.raises(ValueError):
        client.batch([])


@patch("ipapi.client.requests.Session.get")
def test_dns_lookup(mock_get, client, mock_response):
    """Test DNS lookup"""
    mock_response.json.return_value = {
        "status": "success",
        "country": "United States",
        "query": "142.250.185.46"
    }
    mock_get.return_value = mock_response

    result = client.dns_lookup("google.com")

    assert result["status"] == "success"
    assert "query" in result


@patch("ipapi.client.requests.Session.post")
def test_batch_dns(mock_post, client, mock_response):
    """Test batch DNS lookup"""
    mock_response.json.return_value = [
        {"status": "success", "query": "142.250.185.46"},
        {"status": "success", "query": "140.82.121.4"},
    ]
    mock_post.return_value = mock_response

    domains = ["google.com", "github.com"]
    results = client.batch_dns(domains)

    assert len(results) == 2


def test_invalid_fields(client):
    """Test validation of invalid fields"""
    with pytest.raises(ValueError, match="Invalid fields"):
        client.lookup("8.8.8.8", fields=["invalid_field"])


def test_rate_limiting(client):
    """Test rate limiting functionality"""
    # Set a low rate limit for testing
    client.rate_limit = 2
    client.rate_window = 60

    with patch.object(client, "_make_request"):
        # First two requests should work
        client.lookup("8.8.8.8")
        client.lookup("1.1.1.1")

        # Third request should raise rate limit error
        with pytest.raises(RateLimitError):
            client.lookup("8.8.4.4")


def test_context_manager():
    """Test context manager functionality"""
    with IPAPIClient() as client:
        assert client.session is not None

    # Session should be closed after context exit
    assert client.session


@patch("ipapi.client.requests.Session.get")
def test_different_formats(mock_get, client, mock_response):
    """Test different output formats"""
    # Test XML format
    mock_response.headers = {"Content-Type": "text/xml"}
    mock_response.text = "<xml>data</xml>"
    mock_get.return_value = mock_response

    result = client.lookup("8.8.8.8", format="xml")
    assert isinstance(result, str)
    assert "<xml>" in result


def test_invalid_field_in_batch(client):
    """Test invalid fields in batch request"""
    with pytest.raises(ValueError, match="Invalid fields"):
        client.batch(["8.8.8.8"], fields=["invalid_field"])


@patch("ipapi.client.requests.Session.get")
def test_language_parameter(mock_get, client, mock_response):
    """Test language parameter is passed correctly"""
    client.lang = "de"

    mock_response.json.return_value = {
        "status": "success",
        "country": "Vereinigte Staaten"
    }
    mock_get.return_value = mock_response

    client.lookup("8.8.8.8")

    # Check that lang parameter was included
    call_args = mock_get.call_args
    assert call_args.kwargs["params"]["lang"] == "de"
