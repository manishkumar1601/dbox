"""Automatic free-port detection.

Tries the preferred port first, then walks upward until a free one is found,
so concurrent DBox projects never collide on the host.
"""

from __future__ import annotations

import re
import shutil
import socket
import subprocess


def _socket_free(port: int, host: str = "0.0.0.0") -> bool:
    """True if a plain TCP bind on the host succeeds (catches non-Docker procs).

    No SO_REUSEADDR: on Windows that flag acts like SO_REUSEPORT and lets the
    bind succeed even when the port is already in use, hiding real conflicts.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def docker_published_ports() -> set[int]:
    """Host ports already published by running Docker containers.

    Docker Desktop (especially on Windows/macOS) forwards published ports
    through a proxy, so a host socket bind does NOT conflict with them — the
    only reliable way to see them is to ask Docker.
    """
    if not shutil.which("docker"):
        return set()
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Ports}}"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    # Lines look like "0.0.0.0:7030->3306/tcp, :::7030->3306/tcp"
    return {int(m) for m in re.findall(r":(\d+)->", result.stdout)}


def project_published_ports(project_name: str) -> set[int]:
    """Host ports published by *this* project's own containers, so a restart
    doesn't treat the project's own ports as conflicts."""
    if not shutil.which("docker"):
        return set()
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name=dbox-{project_name}-", "--format", "{{.Ports}}"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    return {int(m) for m in re.findall(r":(\d+)->", result.stdout)}


def is_free(port: int) -> bool:
    """True if the port is free — not bound on the host and not published by
    any running Docker container."""
    return port not in docker_published_ports() and _socket_free(port)


def find_free(preferred: int, taken: set[int] | None = None, limit: int = 200) -> int:
    """Find a free port at or above ``preferred``.

    ``taken`` reserves ports already claimed (by this project or other running
    containers) so the same number is never handed out twice.
    """
    taken = taken or set()
    port = preferred
    for _ in range(limit):
        if port not in taken and _socket_free(port):
            return port
        port += 1
    raise RuntimeError(f"No free port found near {preferred}")


def allocate(preferred_ports: dict[str, int]) -> dict[str, int]:
    """Resolve a mapping of name -> preferred port into free, non-colliding ports."""
    resolved: dict[str, int] = {}
    # Seed with ports already published by other running containers (one Docker
    # query), then add each chosen port so services within this project differ.
    taken: set[int] = docker_published_ports()
    for name, preferred in preferred_ports.items():
        chosen = find_free(preferred, taken)
        resolved[name] = chosen
        taken.add(chosen)
    return resolved
