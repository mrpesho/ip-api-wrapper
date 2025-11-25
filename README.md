# IP-API Python Wrapper

A comprehensive Python wrapper for the [ip-api.com](https://ip-api.com) geolocation API service.

## Features

- Single IP address lookups
- Batch IP lookups (up to 100 IPs per request)
- DNS lookups with geolocation
- Batch DNS lookups
- Custom field selection
- Multiple output formats (JSON, XML, CSV)
- Built-in rate limiting
- Comprehensive error handling
- Type hints for better IDE support

## Installation

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

## Quick Start

### Single IP Lookup

```python
from ipapi import IPAPIClient

# Create client
client = IPAPIClient()

# Lookup current IP
result = client.lookup()
print(f"Country: {result['country']}")
print(f"City: {result['city']}")

# Lookup specific IP
result = client.lookup("8.8.8.8")
print(f"ISP: {result['isp']}")
```

### Batch IP Lookup

```python
from ipapi import IPAPIClient

client = IPAPIClient()

# Lookup multiple IPs at once
ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
results = client.batch(ips)

for result in results:
    print(f"{result['query']}: {result['city']}, {result['country']}")
```

### DNS Lookup

```python
from ipapi import IPAPIClient

client = IPAPIClient()

# Resolve domain and get geolocation
result = client.dns_lookup("google.com")
print(f"IP: {result['query']}")
print(f"Location: {result['city']}, {result['country']}")
```

### Custom Fields

```python
from ipapi import IPAPIClient

client = IPAPIClient()

# Request only specific fields
fields = ["country", "city", "isp", "query"]
result = client.lookup("8.8.8.8", fields=fields)
print(result)
```

### Context Manager

```python
from ipapi import IPAPIClient

# Automatically close session when done
with IPAPIClient() as client:
    result = client.lookup("8.8.8.8")
    print(result)
```

## Available Fields

You can customize which fields are returned by specifying them in the `fields` parameter:

- `status` - Success or fail
- `message` - Error message (if status is fail)
- `continent` - Continent name
- `continentCode` - Two-letter continent code
- `country` - Country name
- `countryCode` - Two-letter country code (ISO 3166-1 alpha-2)
- `region` - Region/state short code
- `regionName` - Region/state full name
- `city` - City name
- `district` - District (subdivision of city)
- `zip` - Zip code
- `lat` - Latitude
- `lon` - Longitude
- `timezone` - Timezone (tz database)
- `offset` - Timezone UTC DST offset in seconds
- `currency` - National currency
- `isp` - ISP name
- `org` - Organization name
- `as` - AS number and organization, separated by space
- `asname` - AS name (RIR)
- `reverse` - Reverse DNS of the IP
- `mobile` - Mobile (cellular) connection
- `proxy` - Proxy, VPN or Tor exit address
- `hosting` - Hosting, colocated or data center
- `query` - IP used for the query

## Error Handling

```python
from ipapi import IPAPIClient, IPAPIError, RateLimitError, InvalidIPError

client = IPAPIClient()

try:
    result = client.lookup("invalid-ip")
except InvalidIPError as e:
    print(f"Invalid IP: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except IPAPIError as e:
    print(f"API error: {e}")
```

## Rate Limiting

The free tier allows 45 requests per minute. The client automatically tracks and enforces this limit:

```python
from ipapi import IPAPIClient, RateLimitError

client = IPAPIClient()

try:
    for i in range(50):
        result = client.lookup(f"8.8.{i}.{i}")
except RateLimitError:
    print("Rate limit reached, please wait...")
```

## Advanced Usage

### Different Languages

```python
client = IPAPIClient(lang="de")  # German
result = client.lookup("8.8.8.8")
print(result['country'])  # Returns "Vereinigte Staaten"
```

Supported languages: en, de, es, pt-BR, fr, ja, zh-CN, ru

### Different Output Formats

```python
client = IPAPIClient()

# JSON (default)
json_result = client.lookup("8.8.8.8", format="json")

# XML
xml_result = client.lookup("8.8.8.8", format="xml")

# CSV
csv_result = client.lookup("8.8.8.8", format="csv")
```

### Custom Timeout

```python
client = IPAPIClient(timeout=30)  # 30 second timeout
```

## API Reference

### IPAPIClient

#### `__init__(api_key=None, lang="en", timeout=10)`

Initialize the client.

**Parameters:**
- `api_key` (str, optional): API key for pro features
- `lang` (str): Language for location names (default: "en")
- `timeout` (int): Request timeout in seconds (default: 10)

#### `lookup(ip=None, fields=None, format="json")`

Lookup information for a single IP address.

**Parameters:**
- `ip` (str, optional): IP address to lookup (None for current IP)
- `fields` (list, optional): List of fields to return
- `format` (str): Response format (json, xml, csv, line)

**Returns:** Dict or str depending on format

#### `batch(ips, fields=None)`

Lookup information for multiple IP addresses.

**Parameters:**
- `ips` (list): List of IP addresses (max 100)
- `fields` (list, optional): List of fields to return

**Returns:** List of dicts

#### `dns_lookup(domain, fields=None)`

Perform DNS lookup and get geolocation.

**Parameters:**
- `domain` (str): Domain name to lookup
- `fields` (list, optional): List of fields to return

**Returns:** Dict with IP information

#### `batch_dns(domains, fields=None)`

Batch DNS lookup for multiple domains.

**Parameters:**
- `domains` (list): List of domain names (max 100)
- `fields` (list, optional): List of fields to return

**Returns:** List of dicts

## Testing

```bash
pytest tests/
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [IP-API Website](https://ip-api.com)
- [IP-API Documentation](https://ip-api.com/docs)
- [GitHub Repository](https://github.com/yourusername/ip-api)
