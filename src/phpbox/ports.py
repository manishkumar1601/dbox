"""Automatic free-port detection.

Tries the preferred port first, then walks upward until a free one is found,
so concurrent PHPBox projects never collide on the host.
"""

from __future__ import annotations

import socket


def is_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if a TCP port can be bound on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_free(preferred: int, taken: set[int] | None = None, limit: int = 200) -> int:
    """Find a free port at or above ``preferred``.

    ``taken`` lets the caller reserve ports already assigned within the same
    project so two services don't claim the same number.
    """
    taken = taken or set()
    port = preferred
    for _ in range(limit):
        if port not in taken and is_free(port):
            return port
        port += 1
    raise RuntimeError(f"No free port found near {preferred}")


def allocate(preferred_ports: dict[str, int]) -> dict[str, int]:
    """Resolve a mapping of name -> preferred port into free, non-colliding ports."""
    resolved: dict[str, int] = {}
    taken: set[int] = set()
    for name, preferred in preferred_ports.items():
        chosen = find_free(preferred, taken)
        resolved[name] = chosen
        taken.add(chosen)
    return resolved
