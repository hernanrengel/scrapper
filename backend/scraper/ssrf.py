import ipaddress
import socket
from urllib.parse import urlsplit


class BlockedHostError(Exception):
    pass


def assert_host_is_safe(url):
    hostname = urlsplit(url).hostname
    if not hostname:
        raise BlockedHostError(f"URL has no host: {url}")

    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise BlockedHostError(f"Could not resolve host: {hostname}") from exc

    for info in resolved:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise BlockedHostError(f"Host resolves to a blocked address: {ip}")
