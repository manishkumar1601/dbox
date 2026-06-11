"""Framework plugin interface.

Each plugin describes how to detect a framework, what extensions and companion
services it wants, how to scaffold a fresh project, and which framework-native
CLI it exposes through PHPBox (e.g. ``artisan`` for Laravel).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Credential:
    """A secret PHPBox must collect before scaffolding (e.g. Magento keys).

    The value is taken from the environment variable ``env`` if set, otherwise
    the CLI prompts for it interactively.
    """

    env: str
    prompt: str
    secret: bool = False


@dataclass
class DetectionRule:
    """Markers that identify a framework in a project directory.

    * ``files``    — paths that must all exist (relative to project root)
    * ``any_files`` — at least one must exist
    * ``composer`` — composer.json must require one of these packages
    """

    files: tuple[str, ...] = ()
    any_files: tuple[str, ...] = ()
    composer: tuple[str, ...] = ()


class FrameworkPlugin:
    """Base class for every framework/CMS plugin."""

    #: machine name, e.g. "laravel" — matches `phpbox create <name>`
    name: str = ""
    #: human label shown in output, e.g. "Laravel"
    label: str = ""
    #: web document root relative to the app root, e.g. "/public"
    document_root: str = "/public"
    #: detection markers
    detection: DetectionRule = DetectionRule()
    #: scoring weight — higher wins when several plugins match
    priority: int = 50
    #: preferred PHP version when the project doesn't pin one (e.g. legacy
    #: frameworks that aren't compatible with the latest PHP). None = default.
    php_version: str | None = None

    # ---- detection -----------------------------------------------------

    def detect(self, project_dir: Path) -> bool:
        """Return True if this plugin's framework lives in ``project_dir``.

        The three signals are independent — any one is enough to match (a
        project may have framework files without a composer.json, or vice
        versa). When several plugins match, ``priority`` breaks the tie.
        """
        rule = self.detection

        if rule.composer:
            requires = _composer_requires(project_dir)
            if any(pkg in requires for pkg in rule.composer):
                return True

        # All required `files` must be present together (a strong marker set).
        if rule.files and all((project_dir / f).exists() for f in rule.files):
            return True

        # Any single `any_files` marker is enough.
        if rule.any_files and any((project_dir / f).exists() for f in rule.any_files):
            return True

        return False

    # ---- environment hints --------------------------------------------

    def extensions(self) -> list[str]:
        """PHP extensions this framework commonly needs."""
        return []

    def services(self) -> list[str]:
        """Companion services to recommend (redis, mailpit, ...)."""
        return []

    def commands(self) -> dict[str, list[str]]:
        """Map a PHPBox subcommand name to the in-container command prefix.

        Example: ``{"artisan": ["php", "artisan"]}`` means
        ``phpbox artisan migrate`` runs ``php artisan migrate`` in the PHP
        container.
        """
        return {}

    # ---- project creation ----------------------------------------------

    def create_steps(self, project_name: str) -> list[str] | None:
        """Shell commands (run in the PHP container) to scaffold a new project.

        Return ``None`` if automated scaffolding isn't supported; the CLI will
        print guidance instead.
        """
        return None

    def app_env(self, db) -> dict[str, str]:
        """Environment variables injected into the app container so the
        framework connects to the PHPBox database (host ``db``) with no manual
        config. ``db`` is the project's DatabaseConfig. Default: none.
        """
        return {}

    def create_credentials(self) -> list[Credential]:
        """Secrets to collect before scaffolding (empty for most frameworks)."""
        return []

    def create_env(self, credentials: dict[str, str]) -> dict[str, str]:
        """Turn collected credentials into environment variables for the
        scaffolding container. Default: pass them straight through."""
        return dict(credentials)

    def post_create_note(self) -> str | None:
        """Optional guidance printed after a project is created."""
        return None


def _composer_requires(project_dir: Path) -> set[str]:
    import json

    composer = project_dir / "composer.json"
    if not composer.exists():
        return set()
    try:
        data = json.loads(composer.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return set()
    requires: set[str] = set()
    requires.update((data.get("require") or {}).keys())
    requires.update((data.get("require-dev") or {}).keys())
    return requires
