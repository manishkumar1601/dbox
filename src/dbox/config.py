"""Typed model for ``dbox.yml`` — the single source of truth for a project.

The ``.dbox/`` Docker artifacts are always regenerated from this file, so
editing ``dbox.yml`` and re-running ``dbox start`` is the supported way to
change an environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_FILENAME = "dbox.yml"
DBOX_DIR = ".dbox"

SUPPORTED_RUNTIMES = ["php", "go", "rust"]
SUPPORTED_PHP = ["7.4", "8.0", "8.1", "8.2", "8.3", "8.4"]
SUPPORTED_GO = ["1.23", "1.24", "1.25"]
SUPPORTED_RUST = ["1.75", "1.80", "stable"]
SUPPORTED_SERVERS = ["nginx", "apache", "litespeed", "caddy"]
SUPPORTED_DB = ["mariadb", "mysql", "postgres", "sqlite"]


@dataclass
class PhpConfig:
    version: str = "8.3"
    extensions: list[str] = field(
        default_factory=lambda: ["gd", "zip", "intl", "pdo_mysql", "opcache"]
    )
    ini: dict[str, str] = field(
        default_factory=lambda: {
            "memory_limit": "256M",
            "upload_max_filesize": "64M",
            "post_max_size": "64M",
            "max_execution_time": "120",
        }
    )


@dataclass
class ComposerConfig:
    version: str = "latest"


@dataclass
class GoConfig:
    version: str = "1.25"


@dataclass
class RustConfig:
    version: str = "stable"


@dataclass
class ServerConfig:
    type: str = "nginx"


@dataclass
class DatabaseConfig:
    engine: str = "mariadb"
    version: str = "11"
    name: str = "app"
    user: str = "app"
    password: str = "app"
    root_password: str = "root"


@dataclass
class ServicesConfig:
    redis: bool = False
    mailpit: bool = False
    meilisearch: bool = False
    elasticsearch: bool = False
    phpmyadmin: bool = False


@dataclass
class SslConfig:
    enabled: bool = False
    host: str = "app.localhost"


@dataclass
class PortsConfig:
    http: int = 7010
    https: int = 7020
    database: int = 7030
    redis: int = 7040
    mailpit: int = 7050
    phpmyadmin: int = 7060
    meilisearch: int = 7070
    elasticsearch: int = 7080
    # Go / Rust app container host port (unused for PHP runtime).
    app: int = 7090


@dataclass
class ProjectConfig:
    name: str = "app"
    framework: str = "corephp"
    runtime: str = "php"  # "php" | "go" | "rust"
    document_root: str = "/public"
    php: PhpConfig | None = None
    composer: ComposerConfig | None = None
    go: GoConfig | None = None
    rust: RustConfig | None = None
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    services: ServicesConfig = field(default_factory=ServicesConfig)
    ssl: SslConfig = field(default_factory=SslConfig)
    ports: PortsConfig = field(default_factory=PortsConfig)

    def __post_init__(self) -> None:
        """Auto-populate the runtime-specific config block when missing.

        Keeps callers that do ``ProjectConfig(framework="laravel")`` working
        — they get a PhpConfig/ComposerConfig for free. Same for Go/Rust.
        """
        if self.runtime == "php":
            if self.php is None:
                self.php = PhpConfig()
            if self.composer is None:
                self.composer = ComposerConfig()
        elif self.runtime == "go" and self.go is None:
            self.go = GoConfig()
        elif self.runtime == "rust" and self.rust is None:
            self.rust = RustConfig()

    # ---- serialization -------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for round-tripping through YAML.

        Runtime-specific blocks that are unused are stripped so a PHP yml
        doesn't carry empty ``go:``/``rust:`` keys (and vice versa). The
        ``runtime`` key is also omitted when it equals ``php`` so existing
        PHP project files stay byte-identical to pre-multi-runtime DBox.
        """
        result: dict = {
            "name": self.name,
            "framework": self.framework,
        }
        if self.runtime != "php":
            result["runtime"] = self.runtime
        result["document_root"] = self.document_root
        if self.php is not None:
            result["php"] = _to_plain(self.php)
        if self.composer is not None:
            result["composer"] = _to_plain(self.composer)
        if self.go is not None:
            result["go"] = _to_plain(self.go)
        if self.rust is not None:
            result["rust"] = _to_plain(self.rust)
        result["server"] = _to_plain(self.server)
        result["database"] = _to_plain(self.database)
        result["services"] = _to_plain(self.services)
        result["ssl"] = _to_plain(self.ssl)
        result["ports"] = _to_plain(self.ports)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """Load from a dict, defaulting unknown runtimes to ``php`` so legacy
        ``dbox.yml`` files (with no ``runtime`` key) keep working unchanged."""
        data = dict(data or {})
        runtime = data.get("runtime", "php")
        php = _merge(PhpConfig, data.get("php")) if runtime == "php" else None
        composer = _merge(ComposerConfig, data.get("composer")) if runtime == "php" else None
        go = _merge(GoConfig, data.get("go")) if runtime == "go" else None
        rust = _merge(RustConfig, data.get("rust")) if runtime == "rust" else None
        # When loading a PHP project, populate php/composer even if absent
        # from the file (legacy yml may have just framework/server/db sections).
        if runtime == "php" and php is None:
            php = PhpConfig()
        if runtime == "php" and composer is None:
            composer = ComposerConfig()
        return cls(
            name=data.get("name", "app"),
            framework=data.get("framework", "corephp"),
            runtime=runtime,
            document_root=data.get("document_root", "/public"),
            php=php,
            composer=composer,
            go=go,
            rust=rust,
            server=_merge(ServerConfig, data.get("server")),
            database=_merge(DatabaseConfig, data.get("database")),
            services=_merge(ServicesConfig, data.get("services")),
            ssl=_merge(SslConfig, data.get("ssl")),
            ports=_merge(PortsConfig, data.get("ports")),
        )


def _to_plain(obj) -> dict:
    """Serialize a dataclass to a plain dict (no asdict so we keep ordering)."""
    return {k: getattr(obj, k) for k in obj.__dataclass_fields__}


def _merge(cls, data):
    """Build a dataclass from a dict, falling back to field defaults."""
    if not data:
        return cls()
    base = cls()
    for key, value in data.items():
        if hasattr(base, key):
            setattr(base, key, value)
    return base


# ---- file helpers ------------------------------------------------------


def config_path(project_dir: Path) -> Path:
    return project_dir / CONFIG_FILENAME


def find_root(start: Path | None = None) -> Path | None:
    """Walk upward from ``start`` looking for a directory containing dbox.yml."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        if (directory / CONFIG_FILENAME).exists():
            return directory
    return None


def exists(project_dir: Path) -> bool:
    return config_path(project_dir).exists()


def load(project_dir: Path) -> ProjectConfig:
    path = config_path(project_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"No {CONFIG_FILENAME} found in {project_dir}. Run `dbox init` first."
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return ProjectConfig.from_dict(data)


def save(project_dir: Path, config: ProjectConfig) -> Path:
    path = config_path(project_dir)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            config.to_dict(),
            fh,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    return path
