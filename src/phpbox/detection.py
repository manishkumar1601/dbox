"""Environment detection.

Inspects a project directory to infer the framework, required PHP version,
extensions, and recommended services. Powers both ``phpbox init`` (which writes
a config) and ``phpbox detect`` (which just reports).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from phpbox import plugins
from phpbox.config import SUPPORTED_PHP
from phpbox.plugins.base import FrameworkPlugin


@dataclass
class Detection:
    plugin: FrameworkPlugin | None
    php_version: str
    extensions: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    needs_database: bool = True

    @property
    def framework(self) -> str:
        return self.plugin.name if self.plugin else "corephp"

    @property
    def label(self) -> str:
        return self.plugin.label if self.plugin else "Core PHP"

    @property
    def document_root(self) -> str:
        return self.plugin.document_root if self.plugin else "/"


def _read_composer(project_dir: Path) -> dict:
    path = project_dir / "composer.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def _php_from_composer(composer: dict) -> str | None:
    """Pick the lowest supported PHP version that satisfies the constraint."""
    constraint = (composer.get("require") or {}).get("php")
    if not constraint:
        return None
    # Find the first supported version that appears >= any "^X.Y"/">=X.Y" floor.
    floors = re.findall(r"(\d+\.\d+)", constraint)
    if not floors:
        return None
    floor = max(floors)  # be conservative: respect the highest stated minimum
    for version in SUPPORTED_PHP:
        if _ge(version, floor):
            return version
    return SUPPORTED_PHP[-1]


def _ge(a: str, b: str) -> bool:
    return tuple(int(x) for x in a.split(".")) >= tuple(int(x) for x in b.split("."))


def _ext_from_composer(composer: dict) -> list[str]:
    """Read `ext-*` requirements from composer.json."""
    found: list[str] = []
    for section in ("require", "require-dev"):
        for pkg in (composer.get(section) or {}):
            if pkg.startswith("ext-"):
                found.append(pkg[4:])
    return found


def detect(project_dir: Path) -> Detection:
    plugin = plugins.detect(project_dir)
    composer = _read_composer(project_dir)

    php_version = (
        _php_from_composer(composer)
        or (plugin.php_version if plugin else None)
        or "8.3"
    )

    extensions: list[str] = []
    if plugin:
        extensions.extend(plugin.extensions())
    extensions.extend(_ext_from_composer(composer))
    # de-dupe, keep order
    seen: set[str] = set()
    extensions = [e for e in extensions if not (e in seen or seen.add(e))]

    services = list(plugin.services()) if plugin else []

    return Detection(
        plugin=plugin,
        php_version=php_version,
        extensions=extensions,
        services=services,
    )
