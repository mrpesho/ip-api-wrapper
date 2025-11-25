"""
Basic usage examples for IP-API Python wrapper
"""

from ipapi import IPAPIClient


def example_single_lookup():
    """Example: Single IP lookup"""
    print("=== Single IP Lookup ===")

    with IPAPIClient() as client:
        # Lookup current IP
        result = client.lookup()
        print(f"Your IP: {result['query']}")
        print(f"Location: {result['city']}, {result['country']}")
        print(f"ISP: {result['isp']}")
        print()

        # Lookup specific IP
        result = client.lookup("8.8.8.8")
        print(f"IP: {result['query']}")
        print(f"Location: {result['city']}, {result['country']}")
        print(f"Org: {result['org']}")
        print()


def example_batch_lookup():
    """Example: Batch IP lookup"""
    print("=== Batch IP Lookup ===")

    with IPAPIClient() as client:
        ips = [
            "8.8.8.8",          # Google DNS
            "1.1.1.1",          # Cloudflare DNS
            "208.67.222.222",   # OpenDNS
        ]

        results = client.batch(ips)

        for result in results:
            print(f"{result['query']}: {result['city']}, {result['country']} ({result['org']})")
        print()


def example_custom_fields():
    """Example: Using custom fields"""
    print("=== Custom Fields ===")

    with IPAPIClient() as client:
        # Request only specific fields
        fields = ["query", "country", "city", "isp", "lat", "lon"]

        result = client.lookup("8.8.8.8", fields=fields)
        print("Custom fields result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print()


def example_dns_lookup():
    """Example: DNS lookup"""
    print("=== DNS Lookup ===")

    with IPAPIClient() as client:
        domains = ["google.com", "github.com", "cloudflare.com"]

        for domain in domains:
            result = client.dns_lookup(domain)
            print(f"{domain} -> {result['query']}")
            print(f"  Location: {result['city']}, {result['country']}")
            print(f"  ISP: {result['isp']}")
        print()


def example_batch_dns():
    """Example: Batch DNS lookup"""
    print("=== Batch DNS Lookup ===")

    with IPAPIClient() as client:
        domains = [
            "google.com",
            "github.com",
            "stackoverflow.com",
            "reddit.com",
        ]

        results = client.batch_dns(domains)

        for result in results:
            print(f"{result.get('reverse', 'N/A')}: {result['city']}, {result['countryCode']}")
        print()


def example_different_languages():
    """Example: Using different languages"""
    print("=== Different Languages ===")

    languages = ["en", "de", "es", "fr"]

    for lang in languages:
        with IPAPIClient(lang=lang) as client:
            result = client.lookup("8.8.8.8")
            print(f"{lang}: {result['country']}")
    print()


def example_error_handling():
    """Example: Error handling"""
    print("=== Error Handling ===")

    from ipapi import InvalidIPError, BatchLimitError

    with IPAPIClient() as client:
        # Invalid IP
        try:
            result = client.lookup("invalid-ip-address")
        except InvalidIPError as e:
            print(f"Invalid IP error: {e}")

        # Batch limit exceeded
        try:
            too_many_ips = [f"8.8.{i}.{i % 256}" for i in range(101)]
            results = client.batch(too_many_ips)
        except BatchLimitError as e:
            print(f"Batch limit error: {e}")
        print()


def example_security_check():
    """Example: Check for proxy/VPN/hosting"""
    print("=== Security Check ===")

    with IPAPIClient() as client:
        # Request security-related fields
        fields = ["query", "country", "proxy", "hosting", "mobile"]

        test_ips = ["8.8.8.8", "1.1.1.1"]

        for ip in test_ips:
            result = client.lookup(ip, fields=fields)
            print(f"IP: {result['query']}")
            print(f"  Country: {result['country']}")
            print(f"  Proxy/VPN: {result['proxy']}")
            print(f"  Hosting: {result['hosting']}")
            print(f"  Mobile: {result['mobile']}")
        print()


if __name__ == "__main__":
    print("IP-API Python Wrapper - Examples\n")

    example_single_lookup()
    example_batch_lookup()
    example_custom_fields()
    example_dns_lookup()
    example_batch_dns()
    example_different_languages()
    example_error_handling()
    example_security_check()

    print("All examples completed!")
