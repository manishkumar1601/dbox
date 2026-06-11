"""Render the ``.phpbox/`` Docker artifacts from a ``ProjectConfig``.

Everything under ``.phpbox/`` is disposable and regenerated on demand, so the
config file stays the only thing a user needs to edit or commit.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from phpbox import extensions
from phpbox.config import PHPBOX_DIR, ProjectConfig

TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(enabled_extensions=()),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def _normalize_docroot(document_root: str) -> str:
    """Turn '/public' into the absolute in-container path '/var/www/html/public'."""
    root = "/var/www/html" + ("/" + document_root.strip("/") if document_root.strip("/") else "")
    return root.rstrip("/") or "/var/www/html"


def _database_spec(cfg: ProjectConfig) -> dict | None:
    db = cfg.database
    if db.engine == "sqlite":
        return None
    if db.engine in ("mariadb", "mysql"):
        prefix = "MARIADB" if db.engine == "mariadb" else "MYSQL"
        env = {
            f"{prefix}_DATABASE": db.name,
            f"{prefix}_ROOT_PASSWORD": db.root_password,
        }
        # MySQL/MariaDB reject MYSQL_USER=root (root already exists), so only
        # create a separate app user when it isn't root. Logging in as root
        # uses the root password above.
        if db.user != "root":
            env[f"{prefix}_USER"] = db.user
            env[f"{prefix}_PASSWORD"] = db.password
        return {
            "image": f"{db.engine}:{db.version}",
            "env": env,
            "data_dir": "/var/lib/mysql",
            "container_port": 3306,
        }
    if db.engine == "postgres":
        return {
            "image": f"postgres:{db.version}",
            "env": {
                "POSTGRES_DB": db.name,
                "POSTGRES_USER": db.user,
                "POSTGRES_PASSWORD": db.password,
            },
            "data_dir": "/var/lib/postgresql/data",
            "container_port": 5432,
        }
    return None


def _context(cfg: ProjectConfig) -> dict:
    server = cfg.server.type
    separate_web = server in ("nginx", "caddy", "litespeed")
    web_image = {
        "nginx": "nginx:alpine",
        "caddy": "caddy:alpine",
        "litespeed": "litespeedtech/openlitespeed:latest",
    }.get(server, "nginx:alpine")
    db = _database_spec(cfg)
    return {
        "cfg": cfg,
        "name": cfg.name,
        "framework": cfg.framework,
        "php_version": cfg.php.version,
        "composer_version": cfg.composer.version,
        "document_root": cfg.document_root,
        "container_docroot": _normalize_docroot(cfg.document_root),
        "apache_docroot": _normalize_docroot(cfg.document_root),
        "server": server,
        "separate_web": separate_web,
        "web_image": web_image,
        "ext": extensions.resolve(cfg.php.extensions),
        # de-duped extension list for install-php-extensions
        "php_extensions": list(dict.fromkeys(cfg.php.extensions)),
        "install_wp_cli": cfg.framework == "wordpress",
        "ports": cfg.ports,
        "ssl": cfg.ssl,
        "services": cfg.services,
        "db_engine": cfg.database.engine,
        "needs_db": db is not None,
        "db": db,
    }


def _render(template: str, ctx: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_env.get_template(template).render(**ctx), encoding="utf-8")


def generate(project_dir: Path, cfg: ProjectConfig) -> Path:
    """Write the full ``.phpbox/`` tree and return its path."""
    ctx = _context(cfg)
    base = project_dir / PHPBOX_DIR

    # Persistent data / output directories (kept across regenerations).
    for sub in ("data/mariadb", "data/mysql", "data/postgres", "backups", "cache", "env"):
        (base / sub).mkdir(parents=True, exist_ok=True)

    _render("docker-compose.yml.j2", ctx, base / "docker-compose.yml")
    _render("php/Dockerfile.j2", ctx, base / "php" / "Dockerfile")
    _render("php/php.ini.j2", ctx, base / "php" / "php.ini")
    # Source template is named env.j2 (not .env.j2) so it survives the wheel
    # build — setuptools' package-data globs skip dotfiles.
    _render("env/env.j2", ctx, base / "env" / ".env")

    if cfg.server.type == "nginx":
        _render("nginx/default.conf.j2", ctx, base / "nginx" / "default.conf")
    elif cfg.server.type == "caddy":
        _render("caddy/Caddyfile.j2", ctx, base / "caddy" / "Caddyfile")
    elif cfg.server.type == "litespeed":
        _render("litespeed/httpd_config.conf.j2", ctx, base / "litespeed" / "httpd_config.conf")
        _render("litespeed/vhconf.conf.j2", ctx, base / "litespeed" / "vhconf.conf")
    # apache: served by the PHP image (mod_php), no separate web container.
    if cfg.server.type == "apache" and cfg.ssl.enabled:
        _render("apache/ssl.conf.j2", ctx, base / "apache" / "ssl.conf")

    if cfg.ssl.enabled:
        (base / "certs").mkdir(parents=True, exist_ok=True)

    return base
