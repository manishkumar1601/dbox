"""Unit tests for the PHPBox engine (no Docker required)."""

from __future__ import annotations

from pathlib import Path

import yaml

from phpbox import detection, extensions, generator, plugins
from phpbox.config import ProjectConfig, ServerConfig, DatabaseConfig, load, save
from phpbox.ports import allocate, find_free, is_free


# ---- detection ---------------------------------------------------------


def _mk(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp_path


def test_detect_laravel(tmp_path):
    _mk(tmp_path, {"artisan": "<?php", "bootstrap/app.php": "<?php", "routes/web.php": ""})
    det = detection.detect(tmp_path)
    assert det.framework == "laravel"
    assert det.document_root == "/public"


def test_detect_wordpress(tmp_path):
    _mk(tmp_path, {"wp-config.php": "<?php", "wp-content/index.php": ""})
    assert detection.detect(tmp_path).framework == "wordpress"


def test_detect_symfony(tmp_path):
    _mk(tmp_path, {"bin/console": "<?php", "src/Kernel.php": "<?php"})
    assert detection.detect(tmp_path).framework == "symfony"


def test_detect_codeigniter4_beats_ci3(tmp_path):
    _mk(
        tmp_path,
        {
            "spark": "<?php",
            "app/Config/App.php": "<?php",
            "system/core/CodeIgniter.php": "<?php",
            "application/config/config.php": "<?php",
        },
    )
    # CI4 has higher priority than CI3 even though both could match.
    assert detection.detect(tmp_path).framework == "codeigniter"


def test_detect_php_version_from_composer(tmp_path):
    _mk(tmp_path, {"composer.json": '{"require": {"php": "^8.1"}}'})
    assert detection.detect(tmp_path).php_version == "8.1"


def test_codeigniter3_prefers_php_81(tmp_path):
    # CI3 isn't PHP 8.2+ clean, so it should default to 8.1 when unspecified.
    _mk(
        tmp_path,
        {"application/config/config.php": "<?php", "system/core/CodeIgniter.php": "<?php"},
    )
    det = detection.detect(tmp_path)
    assert det.framework == "codeigniter3"
    assert det.php_version == "8.1"


def test_detect_falls_back_to_corephp(tmp_path):
    _mk(tmp_path, {"index.php": "<?php echo 'hi';"})
    assert detection.detect(tmp_path).framework == "corephp"


# ---- config round-trip -------------------------------------------------


def test_config_roundtrip(tmp_path):
    cfg = ProjectConfig(name="demo", framework="laravel")
    cfg.server = ServerConfig(type="caddy")
    cfg.database = DatabaseConfig(engine="postgres", version="16")
    save(tmp_path, cfg)
    loaded = load(tmp_path)
    assert loaded.name == "demo"
    assert loaded.server.type == "caddy"
    assert loaded.database.engine == "postgres"
    assert loaded.database.version == "16"


# ---- extensions --------------------------------------------------------


def test_extension_resolution_buckets():
    r = extensions.resolve(["gd", "redis", "pdo_pgsql", "unknown_ext"])
    assert "redis" in r["pecl"]
    assert "gd" in r["core"]
    assert "libpq-dev" in r["apt"]  # from pdo_pgsql
    assert "unknown_ext" in r["core"]  # unknown passes through as core


# ---- generator ---------------------------------------------------------


def test_generator_outputs_valid_yaml(tmp_path):
    cfg = ProjectConfig(name="g", framework="laravel")
    generator.generate(tmp_path, cfg)
    compose = tmp_path / ".phpbox" / "docker-compose.yml"
    data = yaml.safe_load(compose.read_text())
    assert "php" in data["services"]
    assert "web" in data["services"]  # nginx default


def test_generator_writes_env_file(tmp_path):
    cfg = ProjectConfig(name="e", framework="laravel")
    generator.generate(tmp_path, cfg)
    env = tmp_path / ".phpbox" / "env" / ".env"
    assert env.exists()
    assert "DB_HOST=db" in env.read_text()


def test_no_dotfile_templates():
    """Templates must not start with '.' — setuptools' package-data globs skip
    dotfiles, so a dotfile template silently vanishes from the wheel build."""
    from phpbox import generator as gen

    dotfiles = [p for p in gen.TEMPLATE_DIR.rglob("*") if p.is_file() and p.name.startswith(".")]
    assert not dotfiles, f"dotfile templates won't survive packaging: {dotfiles}"


def test_generator_apache_has_no_web_service(tmp_path):
    cfg = ProjectConfig(name="a", framework="laravel", server=ServerConfig(type="apache"))
    generator.generate(tmp_path, cfg)
    data = yaml.safe_load((tmp_path / ".phpbox" / "docker-compose.yml").read_text())
    assert "web" not in data["services"]
    dockerfile = (tmp_path / ".phpbox" / "php" / "Dockerfile").read_text()
    assert "-apache" in dockerfile


def test_root_db_user_not_recreated_for_mysql(tmp_path):
    # If someone sets the DB user to root, MySQL/MariaDB must not re-create it.
    cfg = ProjectConfig(
        name="x", framework="laravel", database=DatabaseConfig(engine="mariadb", user="root")
    )
    generator.generate(tmp_path, cfg)
    env = yaml.safe_load((tmp_path / ".phpbox" / "docker-compose.yml").read_text())["services"]["db"]["environment"]
    assert "MARIADB_USER" not in env
    assert env["MARIADB_ROOT_PASSWORD"] == "root"


def test_db_user_defaults_to_app_name(tmp_path):
    # Normal projects get a DB user/password matching the project name.
    cfg = ProjectConfig(
        name="blog", framework="laravel",
        database=DatabaseConfig(engine="mariadb", name="blog", user="blog", password="blog"),
    )
    generator.generate(tmp_path, cfg)
    env = yaml.safe_load((tmp_path / ".phpbox" / "docker-compose.yml").read_text())["services"]["db"]["environment"]
    assert env["MARIADB_USER"] == "blog"
    assert env["MARIADB_PASSWORD"] == "blog"


def test_generator_sqlite_has_no_db(tmp_path):
    cfg = ProjectConfig(name="s", framework="corephp", database=DatabaseConfig(engine="sqlite"))
    generator.generate(tmp_path, cfg)
    data = yaml.safe_load((tmp_path / ".phpbox" / "docker-compose.yml").read_text())
    assert "db" not in data["services"]


# ---- litespeed ---------------------------------------------------------


def test_litespeed_generates_ols_config(tmp_path):
    from phpbox.config import ServerConfig

    cfg = ProjectConfig(name="ls", framework="laravel", server=ServerConfig(type="litespeed"))
    generator.generate(tmp_path, cfg)
    data = yaml.safe_load((tmp_path / ".phpbox" / "docker-compose.yml").read_text())
    assert "openlitespeed" in data["services"]["web"]["image"]
    httpd = (tmp_path / ".phpbox" / "litespeed" / "httpd_config.conf").read_text()
    # External php-fpm must not be auto-started, and the handler must register.
    assert "autoStart               0" in httpd
    assert "address                 php:9000" in httpd
    assert "fcgi:phpfpm php" in httpd


# ---- ssl ---------------------------------------------------------------


def test_ssl_nginx_listens_443(tmp_path):
    from phpbox.config import ServerConfig, SslConfig

    cfg = ProjectConfig(name="x", framework="laravel", ssl=SslConfig(enabled=True))
    generator.generate(tmp_path, cfg)
    conf = (tmp_path / ".phpbox" / "nginx" / "default.conf").read_text()
    assert "listen 443 ssl;" in conf
    assert "/etc/phpbox/certs/cert.pem" in conf


def test_ssl_apache_writes_vhost(tmp_path):
    from phpbox.config import ServerConfig, SslConfig

    cfg = ProjectConfig(
        name="x", framework="laravel", server=ServerConfig(type="apache"), ssl=SslConfig(enabled=True)
    )
    generator.generate(tmp_path, cfg)
    assert (tmp_path / ".phpbox" / "apache" / "ssl.conf").exists()
    assert "a2enmod rewrite ssl" in (tmp_path / ".phpbox" / "php" / "Dockerfile").read_text()


# ---- magento -----------------------------------------------------------


def test_magento_builds_composer_auth():
    import json

    plugin = plugins.get("magento")
    creds = {"MAGENTO_PUBLIC_KEY": "pub123", "MAGENTO_PRIVATE_KEY": "priv456"}
    env = plugin.create_env(creds)
    auth = json.loads(env["COMPOSER_AUTH"])
    basic = auth["http-basic"]["repo.magento.com"]
    assert basic["username"] == "pub123"
    assert basic["password"] == "priv456"


def test_magento_requires_credentials():
    plugin = plugins.get("magento")
    envs = {c.env for c in plugin.create_credentials()}
    assert envs == {"MAGENTO_PUBLIC_KEY", "MAGENTO_PRIVATE_KEY"}
    assert plugin.create_steps("shop") is not None  # now scaffolds via Composer


# ---- uninstall detection -----------------------------------------------


def test_detect_install_returns_command():
    from phpbox.cli import _detect_install

    method, argv = _detect_install()
    assert method in ("pip", "pipx")
    assert argv and "phpbox" in argv


def test_detect_install_pipx(monkeypatch):
    import phpbox.cli as cli

    fake_prefix = str(Path.home() / "pipx" / "venvs" / "phpbox")
    monkeypatch.setattr(cli.sys, "prefix", fake_prefix)
    monkeypatch.setattr(cli.shutil, "which", lambda n: "/usr/bin/pipx" if n == "pipx" else None)
    method, argv = cli._detect_install()
    assert method == "pipx"
    assert argv == ["/usr/bin/pipx", "uninstall", "phpbox"]


# ---- plugins -----------------------------------------------------------


def test_wordpress_requires_mysqli():
    # WordPress core uses the mysqli extension; without it WP refuses to run.
    assert "mysqli" in plugins.get("wordpress").extensions()


def test_all_frameworks_registered():
    expected = {
        "laravel", "symfony", "codeigniter", "codeigniter3", "cakephp", "yii",
        "slim", "laminas", "wordpress", "drupal", "magento", "joomla", "corephp",
    }
    assert expected.issubset(set(plugins.names()))


# ---- ports -------------------------------------------------------------


def test_allocate_no_collisions():
    chosen = allocate({"a": 8080, "b": 8080, "c": 8080})
    assert len(set(chosen.values())) == 3
