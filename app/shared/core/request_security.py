from __future__ import annotations

import ipaddress
import re

from fastapi import Request


HOST_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
HOST_HEADER_FORBIDDEN_CHARS = frozenset('/?#@\\,')


def request_scope_path(request: Request) -> str:
    """Return the ASGI path, which is not reconstructed from the Host header."""
    scope = getattr(request, "scope", None)
    if isinstance(scope, dict):
        path = scope.get("path")
        if isinstance(path, str) and path:
            return path
    return str(getattr(getattr(request, "url", None), "path", "") or "")


def is_valid_host_header(value: str | None) -> bool:
    if value is None:
        return True

    host = value.strip()
    if not host:
        return False
    if any(ord(char) <= 32 or ord(char) == 127 for char in host):
        return False
    if any(char in HOST_HEADER_FORBIDDEN_CHARS for char in host):
        return False

    if host.startswith("["):
        return _is_valid_ip_literal_host(host)
    return _is_valid_dns_or_ipv4_host(host)


def _is_valid_ip_literal_host(value: str) -> bool:
    end = value.find("]")
    if end <= 1:
        return False

    literal = value[1:end]
    tail = value[end + 1 :]
    if tail and not _is_valid_port_tail(tail):
        return False

    try:
        parsed = ipaddress.ip_address(literal)
    except ValueError:
        return False
    return parsed.version == 6


def _is_valid_dns_or_ipv4_host(value: str) -> bool:
    if value.count(":") > 1:
        return False

    host = value
    if ":" in value:
        host, port = value.rsplit(":", 1)
        if not _is_valid_port(port):
            return False

    if not host:
        return False

    try:
        ipaddress.ip_address(host)
    except ValueError:
        return _is_valid_dns_name(host)
    return True


def _is_valid_dns_name(value: str) -> bool:
    host = value.rstrip(".")
    if not host or len(host) > 253:
        return False
    return all(HOST_LABEL_PATTERN.fullmatch(label) for label in host.split("."))


def _is_valid_port_tail(value: str) -> bool:
    if not value.startswith(":"):
        return False
    return _is_valid_port(value[1:])


def _is_valid_port(value: str) -> bool:
    if not value or not value.isdecimal():
        return False
    port = int(value)
    return 0 <= port <= 65535


__all__ = ["is_valid_host_header", "request_scope_path"]
