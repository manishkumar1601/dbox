"""Thin wrapper around the ``docker compose`` CLI.

PHPBox shells out to ``docker compose`` rather than the Docker SDK so it works
identically against Docker Desktop and a plain Docker Engine, and so users can
inspect/reuse the generated compose file directly.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from phpbox.config import PHPBOX_DIR

PHP_SERVICE = "php"


def compose_file(project_dir: Path) -> Path:
    return project_dir / PHPBOX_DIR / "docker-compose.yml"


def docker_available() -> bool:
    return shutil.which("docker") is not None


def docker_running() -> bool:
    """True if the Docker daemon responds."""
    if not docker_available():
        return False
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _base(project_dir: Path) -> list[str]:
    return ["docker", "compose", "-f", str(compose_file(project_dir))]


def command(project_dir: Path, args: list[str]) -> list[str]:
    """Build a raw ``docker compose`` argv — for callers that need custom I/O
    redirection (e.g. piping a SQL dump to/from a file)."""
    return _base(project_dir) + args


def run_once(
    project_dir: Path,
    shell_command: str,
    service: str = "php",
    env: dict[str, str] | None = None,
) -> int:
    """Run a throwaway shell command in a fresh service container (`run --rm`).

    Used for project scaffolding before the stack is brought up. ``env`` is
    injected into the container with ``-e`` (e.g. Composer auth tokens).
    """
    args = ["run", "--rm"]
    for key, value in (env or {}).items():
        args += ["-e", f"{key}={value}"]
    args += [service, "sh", "-lc", shell_command]
    return run(project_dir, args).returncode


def run(project_dir: Path, args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    """Run a compose subcommand, streaming output unless ``capture`` is set."""
    cmd = _base(project_dir) + args
    if capture:
        return subprocess.run(cmd, text=True, capture_output=True)
    return subprocess.run(cmd)


def up(project_dir: Path, build: bool = False, detach: bool = True) -> int:
    args = ["up"]
    if detach:
        args.append("-d")
    if build:
        args.append("--build")
    return run(project_dir, args).returncode


def down(project_dir: Path, volumes: bool = False) -> int:
    args = ["down"]
    if volumes:
        args.append("-v")
    return run(project_dir, args).returncode


def stop(project_dir: Path) -> int:
    return run(project_dir, ["stop"]).returncode


def restart(project_dir: Path) -> int:
    return run(project_dir, ["restart"]).returncode


def build(project_dir: Path, service: str | None = None) -> int:
    args = ["build"]
    if service:
        args.append(service)
    return run(project_dir, args).returncode


def logs(project_dir: Path, follow: bool = False, service: str | None = None) -> int:
    args = ["logs"]
    if follow:
        args.append("-f")
    if service:
        args.append(service)
    return run(project_dir, args).returncode


def ps_running(project_dir: Path) -> list[str]:
    """Return the names of running services."""
    result = run(project_dir, ["ps", "--services", "--status", "running"], capture=True)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def exec_service(
    project_dir: Path,
    command: list[str],
    service: str = PHP_SERVICE,
    interactive: bool = False,
    workdir: str | None = None,
) -> int:
    """Run a command inside a service container.

    ``interactive=True`` allocates a TTY (for shells); otherwise output is
    streamed without a TTY so it behaves consistently on every platform.
    """
    args = ["exec"]
    if not interactive:
        args.append("-T")
    if workdir:
        args += ["-w", workdir]
    args.append(service)
    args += command
    return run(project_dir, args).returncode


def exec_php(project_dir: Path, command: list[str], interactive: bool = False) -> int:
    return exec_service(project_dir, command, service=PHP_SERVICE, interactive=interactive)
