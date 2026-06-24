"""`dbox doctor` — environment health checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dbox import detection, engine, plugins
from dbox.config import SUPPORTED_PHP, ProjectConfig


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def run_checks(project_dir: Path, cfg: ProjectConfig | None) -> list[Check]:
    checks: list[Check] = []

    # Docker
    docker_ok = engine.docker_available()
    checks.append(Check("Docker installed", docker_ok, "" if docker_ok else "docker not on PATH"))
    daemon_ok = docker_ok and engine.docker_running()
    checks.append(
        Check("Docker daemon running", daemon_ok, "" if daemon_ok else "start Docker Desktop/Engine")
    )

    if cfg is None:
        checks.append(Check("dbox.yml present", False, "run `dbox init`"))
        return checks
    checks.append(Check("dbox.yml present", True))

    # Framework detection
    plugin = plugins.detect(project_dir)
    checks.append(
        Check(
            "Framework detected",
            plugin is not None,
            f"{plugin.label}" if plugin else "no framework markers found",
        )
    )

    # Runtime
    checks.append(Check("Runtime", True, cfg.runtime))

    # PHP version (PHP runtime only)
    if cfg.runtime == "php" and cfg.php is not None:
        php_ok = cfg.php.version in SUPPORTED_PHP
        checks.append(
            Check(
                "PHP version supported",
                php_ok,
                cfg.php.version if php_ok else f"{cfg.php.version} not in {SUPPORTED_PHP}",
            )
        )

    # Containers (only meaningful if the daemon is up)
    if daemon_ok and engine.compose_file(project_dir).exists():
        running = engine.ps_running(project_dir)
        checks.append(
            Check(
                "Containers running",
                bool(running),
                ", ".join(running) if running else "run `dbox start`",
            )
        )
        if cfg.database.engine != "sqlite":
            checks.append(Check("Database service", "db" in running, "db container down" if "db" not in running else ""))
        if cfg.services.redis:
            checks.append(Check("Redis service", "redis" in running))

    # Extensions vs. what the framework wants (PHP runtime only)
    if plugin and cfg.runtime == "php" and cfg.php is not None:
        recommended = set(plugin.extensions())
        missing = recommended - set(cfg.php.extensions)
        checks.append(
            Check(
                "Recommended extensions present",
                not missing,
                "missing: " + ", ".join(sorted(missing)) if missing else "",
            )
        )

    # SSL
    checks.append(Check("SSL configured", cfg.ssl.enabled, "" if cfg.ssl.enabled else "ssl disabled"))

    return checks
