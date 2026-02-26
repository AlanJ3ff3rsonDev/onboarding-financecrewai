"""Tests for URL validation / SSRF protection (T36.2)."""

import socket
from unittest.mock import patch

import pytest

from app.utils.url_validation import _is_private_ip, validate_url, validate_url_scheme


# ─── TestIsPrivateIp ─────────────────────────────────────────────────────────


class TestIsPrivateIp:
    """Direct tests on the IP range helper."""

    @pytest.mark.parametrize("ip", [
        "127.0.0.1",
        "127.255.255.255",
        "10.0.0.1",
        "10.255.255.255",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.1",
        "192.168.255.255",
        "169.254.169.254",
        "0.0.0.0",
        "::1",
        "fe80::1",
        "fc00::1",
        "::ffff:127.0.0.1",
        "::ffff:10.0.0.1",
    ])
    def test_private_ips_detected(self, ip: str) -> None:
        assert _is_private_ip(ip) is True

    @pytest.mark.parametrize("ip", [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",
        "2606:4700::6810:85e5",
    ])
    def test_public_ips_allowed(self, ip: str) -> None:
        assert _is_private_ip(ip) is False

    def test_unparseable_ip_rejected(self) -> None:
        assert _is_private_ip("not-an-ip") is True


# ─── TestValidateUrlScheme ────────────────────────────────────────────────────


class TestValidateUrlScheme:
    """Tests for the lightweight (no DNS) URL validator."""

    # --- valid URLs pass through ---

    def test_https_url_passes(self) -> None:
        assert validate_url_scheme("https://example.com") == "https://example.com"

    def test_http_url_passes(self) -> None:
        assert validate_url_scheme("http://example.com") == "http://example.com"

    def test_no_scheme_prepends_https(self) -> None:
        assert validate_url_scheme("example.com") == "https://example.com"

    def test_strips_whitespace(self) -> None:
        assert validate_url_scheme("  https://example.com  ") == "https://example.com"

    def test_url_with_path(self) -> None:
        result = validate_url_scheme("https://example.com/page?q=1")
        assert result == "https://example.com/page?q=1"

    # --- blocked schemes ---

    def test_rejects_file_scheme(self) -> None:
        with pytest.raises(ValueError, match="Scheme.*not allowed"):
            validate_url_scheme("file:///etc/passwd")

    def test_rejects_ftp_scheme(self) -> None:
        with pytest.raises(ValueError, match="Scheme.*not allowed"):
            validate_url_scheme("ftp://example.com")

    def test_rejects_data_scheme(self) -> None:
        with pytest.raises(ValueError, match="Scheme.*not allowed"):
            validate_url_scheme("data:text/html,<h1>hi</h1>")

    def test_rejects_gopher_scheme(self) -> None:
        with pytest.raises(ValueError, match="Scheme.*not allowed"):
            validate_url_scheme("gopher://example.com")

    def test_rejects_javascript_scheme(self) -> None:
        with pytest.raises(ValueError, match="Scheme.*not allowed"):
            validate_url_scheme("javascript:alert(1)")

    # --- blocked hostnames ---

    def test_rejects_localhost(self) -> None:
        with pytest.raises(ValueError, match="localhost.*not allowed"):
            validate_url_scheme("https://localhost")

    def test_rejects_localhost_with_port(self) -> None:
        with pytest.raises(ValueError, match="localhost.*not allowed"):
            validate_url_scheme("https://localhost:8000")

    # --- blocked literal private IPs ---

    @pytest.mark.parametrize("ip", [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "0.0.0.0",
    ])
    def test_rejects_literal_private_ips(self, ip: str) -> None:
        with pytest.raises(ValueError, match="Private.*not allowed"):
            validate_url_scheme(f"https://{ip}")

    def test_rejects_literal_ipv6_loopback(self) -> None:
        with pytest.raises(ValueError, match="Private.*not allowed"):
            validate_url_scheme("https://[::1]")

    # --- empty URL ---

    def test_rejects_empty_url(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_url_scheme("")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_url_scheme("   ")


# ─── TestValidateUrl ──────────────────────────────────────────────────────────


def _mock_addrinfo(ip: str, family: int = socket.AF_INET):
    """Build a fake getaddrinfo result for a single IP."""
    if family == socket.AF_INET:
        return [(family, socket.SOCK_STREAM, 6, "", (ip, 0))]
    return [(family, socket.SOCK_STREAM, 6, "", (ip, 0, 0, 0))]


class TestValidateUrl:
    """Tests for the full validator (with DNS resolution)."""

    # --- public IPs pass ---

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_public_ip_passes(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("93.184.216.34")
        result = validate_url("https://example.com")
        assert result == "https://example.com"

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_public_ipv6_passes(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("2606:4700::6810:85e5", socket.AF_INET6)
        result = validate_url("https://example.com")
        assert result == "https://example.com"

    # --- private IPs rejected via DNS ---

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_loopback(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("127.0.0.1")
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_10_x(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("10.0.0.1")
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_172_16(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("172.16.0.1")
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_192_168(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("192.168.1.1")
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_metadata(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("169.254.169.254")
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_ipv6_loopback(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("::1", socket.AF_INET6)
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_dns_to_ipv4_mapped_ipv6(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("::ffff:127.0.0.1", socket.AF_INET6)
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://evil.com")

    # --- DNS rebinding: multiple IPs, one private ---

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_if_any_ip_is_private(self, mock_dns) -> None:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0)),
        ]
        with pytest.raises(ValueError, match="private/reserved"):
            validate_url("https://rebind.example.com")

    # --- unresolvable hostname ---

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_rejects_unresolvable_hostname(self, mock_dns) -> None:
        mock_dns.side_effect = socket.gaierror("Name resolution failed")
        with pytest.raises(ValueError, match="Could not resolve"):
            validate_url("https://nonexistent.invalid")

    # --- scheme-level blocks also apply ---

    def test_file_scheme_blocked(self) -> None:
        with pytest.raises(ValueError, match="Scheme.*not allowed"):
            validate_url("file:///etc/passwd")

    def test_localhost_blocked(self) -> None:
        with pytest.raises(ValueError, match="localhost.*not allowed"):
            validate_url("https://localhost:8000/admin")

    # --- literal public IP passes without DNS ---

    def test_literal_public_ip_passes(self) -> None:
        result = validate_url("https://93.184.216.34")
        assert result == "https://93.184.216.34"

    # --- no scheme → prepends https then resolves ---

    @patch("app.utils.url_validation.socket.getaddrinfo")
    def test_no_scheme_resolves(self, mock_dns) -> None:
        mock_dns.return_value = _mock_addrinfo("93.184.216.34")
        result = validate_url("example.com")
        assert result == "https://example.com"
