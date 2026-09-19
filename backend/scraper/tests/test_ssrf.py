import socket
from unittest.mock import patch

import pytest

from scraper.ssrf import BlockedHostError, assert_host_is_safe


def _addrinfo(ip):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]


def test_public_ip_is_allowed():
    with patch("socket.getaddrinfo", return_value=_addrinfo("93.184.216.34")):
        assert_host_is_safe("https://example.com/page")


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",  # loopback
        "10.0.0.5",  # private (RFC 1918)
        "192.168.1.1",  # private (RFC 1918)
        "169.254.169.254",  # link-local, the classic cloud metadata endpoint
        "0.0.0.0",  # private/unspecified
    ],
)
def test_blocked_ips_are_rejected(ip):
    with patch("socket.getaddrinfo", return_value=_addrinfo(ip)):
        with pytest.raises(BlockedHostError):
            assert_host_is_safe("https://internal.example/page")


def test_unresolvable_host_is_rejected():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror("no such host")):
        with pytest.raises(BlockedHostError):
            assert_host_is_safe("https://does-not-exist.invalid/page")


def test_url_without_host_is_rejected():
    with pytest.raises(BlockedHostError):
        assert_host_is_safe("not-a-url")
