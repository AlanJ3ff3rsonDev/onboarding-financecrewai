"""URL validation utilities for SSRF protection."""

import ipaddress
import socket
from urllib.parse import urlparse


def _is_private_ip(ip_str: str) -> bool:
    """Check if an IP address string is private, reserved, or loopback."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable → reject

    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped

    return any([
        addr.is_private,
        addr.is_loopback,
        addr.is_reserved,
        addr.is_link_local,
        addr.is_multicast,
        addr.is_unspecified,
    ])


_BLOCKED_SCHEMES = frozenset({"file", "ftp", "data", "gopher", "javascript", "dict"})
_BLOCKED_HOSTNAMES = frozenset({"localhost", "localhost."})


def validate_url_scheme(url: str) -> str:
    """Lightweight URL validation (no DNS). For use in Pydantic validators.

    - Strips whitespace
    - Prepends https:// if no scheme
    - Rejects non-http/https schemes
    - Rejects localhost hostname
    - Rejects literal private/reserved IPs

    Returns cleaned URL or raises ValueError.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(url)

    # No scheme → prepend https://
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)

    # Block non-http(s) schemes
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Scheme '{parsed.scheme}' is not allowed. Use http or https.")

    hostname = parsed.hostname or ""

    # Block localhost
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError("localhost URLs are not allowed")

    # Block literal private IPs (without DNS resolution)
    try:
        addr = ipaddress.ip_address(hostname)
        if _is_private_ip(str(addr)):
            raise ValueError(f"Private/reserved IP address '{hostname}' is not allowed")
    except ValueError as exc:
        # If it starts with "Private" or "Scheme" it's our own error — re-raise
        if str(exc).endswith("is not allowed"):
            raise
        # Otherwise it's not an IP literal (it's a hostname) — that's fine
        pass

    return url


def validate_url(url: str) -> str:
    """Full URL validation with DNS resolution. For use in scrape_website().

    Calls validate_url_scheme() first, then resolves hostname and checks
    all resolved IPs against private/reserved ranges.

    Returns cleaned URL or raises ValueError.
    """
    url = validate_url_scheme(url)
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Skip DNS check for literal IPs (already validated by validate_url_scheme)
    try:
        ipaddress.ip_address(hostname)
        return url  # already validated as non-private in validate_url_scheme
    except ValueError:
        pass  # hostname, not IP — resolve via DNS

    # DNS resolution
    try:
        addrinfo = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname '{hostname}'")

    if not addrinfo:
        raise ValueError(f"No DNS results for hostname '{hostname}'")

    for family, _type, _proto, _canonname, sockaddr in addrinfo:
        ip_str = sockaddr[0]
        if _is_private_ip(ip_str):
            raise ValueError(
                f"Hostname '{hostname}' resolves to private/reserved IP '{ip_str}'"
            )

    return url
