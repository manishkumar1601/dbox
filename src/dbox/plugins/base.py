"""Framework plugin interface.

Each plugin describes how to detect a framework, what extensions and companion
services it wants, how to scaffold a fresh project, and which framework-native
CLI it exposes through DBox (e.g. ``artisan`` for Laravel).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Credential:
    """A secret DBox must collect before scaffolding (e.g. Magento keys).

    The value is taken from the environment variable ``env`` if set, otherwise
    the CLI prompts for it interactively.
    """

    env: str
    prompt: str
    secret: bool = False


@dataclass
class DetectionRule:
    """Markers that identify a framework in a project directory.

    * ``files``        — paths that must all exist (relative to project root)
    * ``any_files``    — at least one must exist
    * ``composer``     — composer.json must require one of these packages
    * ``go_modules``   — go.mod must require one of these modules
    * ``cargo_crates`` — Cargo.toml [dependencies] must list one of these crates
    """

    files: tuple[str, ...] = ()
    any_files: tuple[str, ...] = ()
    composer: tuple[str, ...] = ()
    go_modules: tuple[str, ...] = ()
    cargo_crates: tuple[str, ...] = ()


class FrameworkPlugin:
    """Base class for every framework/CMS plugin."""

    #: machine name, e.g. "laravel" — matches `dbox create <name>`
    name: str = ""
    #: human label shown in output, e.g. "Laravel"
    label: str = ""
    #: language runtime — "php" | "go" | "rust"
    runtime: str = "php"
    #: web document root relative to the app root, e.g. "/public"
    document_root: str = "/public"
    #: detection markers
    detection: DetectionRule = DetectionRule()
    #: scoring weight — higher wins when several plugins match
    priority: int = 50
    #: preferred PHP version when the project doesn't pin one (e.g. legacy
    #: frameworks that aren't compatible with the latest PHP). None = default.
    php_version: str | None = None
    #: port the runtime binds inside the container (Go/Rust apps self-serve)
    default_app_port: int = 8080

    # ---- detection -----------------------------------------------------

    def detect(self, project_dir: Path) -> bool:
        """Return True if this plugin's framework lives in ``project_dir``.

        Detection signals are independent — any one is enough to match. When
        several plugins match, ``priority`` breaks the tie.
        """
        rule = self.detection

        if rule.composer:
            requires = _composer_requires(project_dir)
            if any(pkg in requires for pkg in rule.composer):
                return True

        if rule.go_modules:
            requires = _go_modules(project_dir)
            if any(mod in requires for mod in rule.go_modules):
                return True

        if rule.cargo_crates:
            requires = _cargo_crates(project_dir)
            if any(crate in requires for crate in rule.cargo_crates):
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
        """PHP extensions this framework commonly needs (PHP runtime only)."""
        return []

    def services(self) -> list[str]:
        """Companion services to recommend (redis, mailpit, ...)."""
        return []

    def commands(self) -> dict[str, list[str]]:
        """Map a DBox subcommand name to the in-container command prefix.

        Example: ``{"artisan": ["php", "artisan"]}`` means
        ``dbox artisan migrate`` runs ``php artisan migrate`` in the container.
        """
        return {}

    # ---- project creation ----------------------------------------------

    def create_steps(self, project_name: str) -> list[str] | None:
        """Shell commands (run in the app container) to scaffold a new project.

        Return ``None`` if automated scaffolding isn't supported; the CLI will
        print guidance instead.
        """
        return None

    def app_env(self, db) -> dict[str, str]:
        """Environment variables injected into the app container so the
        framework connects to the DBox database (host ``db``) with no manual
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


# ---- dependency scanners ---------------------------------------------


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


def _go_modules(project_dir: Path) -> set[str]:
    """Parse go.mod's ``require`` entries (both single and block form)."""
    gomod = project_dir / "go.mod"
    if not gomod.exists():
        return set()
    try:
        text = gomod.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    requires: set[str] = set()
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        if in_block:
            mod = stripped.split()[0] if stripped else ""
            if mod:
                requires.add(mod)
        elif stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                requires.add(parts[1])
    return requires


def _cargo_crates(project_dir: Path) -> set[str]:
    """Parse the [dependencies] section of Cargo.toml for crate names."""
    cargo = project_dir / "Cargo.toml"
    if not cargo.exists():
        return set()
    try:
        text = cargo.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    crates: set[str] = set()
    in_deps = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_deps = stripped in ("[dependencies]", "[dev-dependencies]")
            continue
        if in_deps and "=" in stripped and not stripped.startswith("#"):
            crate = stripped.split("=", 1)[0].strip()
            if crate:
                crates.add(crate)
    return crates
