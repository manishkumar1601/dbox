"""Typed model for ``phpbox.yml`` — the single source of truth for a project.

The ``.phpbox/`` Docker artifacts are always regenerated from this file, so
editing ``phpbox.yml`` and re-running ``phpbox start`` is the supported way to
change an environment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

CONFIG_FILENAME = "phpbox.yml"
PHPBOX_DIR = ".phpbox"

SUPPORTED_PHP = ["7.4", "8.0", "8.1", "8.2", "8.3", "8.4"]
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
class ServerConfig:
    type: str = "nginx"


@dataclass
class DatabaseConfig:
    engine: str = "mariadb"
    version: str = "11"
    name: str = "app"
    user: str = "app"
    password: str = "secret"
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
    http: int = 8080
    https: int = 8443
    database: int = 3306
    redis: int = 6379
    mailpit: int = 8025
    phpmyadmin: int = 8081
    meilisearch: int = 7700
    elasticsearch: int = 9200


@dataclass
class ProjectConfig:
    name: str = "app"
    framework: str = "corephp"
    document_root: str = "/public"
    php: PhpConfig = field(default_factory=PhpConfig)
    composer: ComposerConfig = field(default_factory=ComposerConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    services: ServicesConfig = field(default_factory=ServicesConfig)
    ssl: SslConfig = field(default_factory=SslConfig)
    ports: PortsConfig = field(default_factory=PortsConfig)

    # ---- serialization -------------------------------------------------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        data = dict(data or {})
        return cls(
            name=data.get("name", "app"),
            framework=data.get("framework", "corephp"),
            document_root=data.get("document_root", "/public"),
            php=_merge(PhpConfig, data.get("php")),
            composer=_merge(ComposerConfig, data.get("composer")),
            server=_merge(ServerConfig, data.get("server")),
            database=_merge(DatabaseConfig, data.get("database")),
            services=_merge(ServicesConfig, data.get("services")),
            ssl=_merge(SslConfig, data.get("ssl")),
            ports=_merge(PortsConfig, data.get("ports")),
        )


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
    """Walk upward from ``start`` looking for a directory containing phpbox.yml."""
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
            f"No {CONFIG_FILENAME} found in {project_dir}. Run `phpbox init` first."
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
