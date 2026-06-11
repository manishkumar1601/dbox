"""PHPBox command-line interface.

Wires every feature from the product spec onto ``docker compose`` via the
config model, generator, and framework plugins.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import typer

from phpbox import __version__, certs, config, detection, engine, extensions, generator, plugins
from phpbox.config import (
    SUPPORTED_DB,
    SUPPORTED_PHP,
    SUPPORTED_SERVERS,
    ComposerConfig,
    DatabaseConfig,
    PhpConfig,
    PortsConfig,
    ProjectConfig,
    ServerConfig,
    ServicesConfig,
)
from phpbox.console import console, error, info, step, success, warn
from phpbox.doctor import run_checks
from phpbox.ports import allocate

app = typer.Typer(
    name="phpbox",
    help="Universal PHP Development Environment Manager — run any PHP framework with only Docker.",
    add_completion=False,
    no_args_is_help=True,
)

PASSTHROUGH_CTX = {"allow_extra_args": True, "ignore_unknown_options": True}

# Framework-native CLIs exposed through PHPBox (command -> in-container prefix).
PASSTHROUGH = {
    "artisan": ["php", "artisan"],
    "spark": ["php", "spark"],
    "wp": ["wp", "--allow-root"],
    "cake": ["bin/cake"],
    "console": ["php", "bin/console"],
    "yii": ["php", "yii"],
    "drush": ["vendor/bin/drush"],
    "magento": ["php", "bin/magento"],
    "joomla": ["php", "cli/joomla.php"],
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _resolve() -> tuple[Path, ProjectConfig]:
    """Locate the project root and load its config, or abort."""
    root = config.find_root()
    if root is None:
        error("No phpbox.yml found in this directory or any parent. Run `phpbox init`.")
        raise typer.Exit(1)
    return root, config.load(root)


def _save_and_regen(project_dir: Path, cfg: ProjectConfig) -> None:
    config.save(project_dir, cfg)
    generator.generate(project_dir, cfg)


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", value).strip("_") or "app"


def _allocated_ports() -> PortsConfig:
    defaults = PortsConfig()
    chosen = allocate(
        {
            "http": defaults.http,
            "https": defaults.https,
            "database": defaults.database,
            "redis": defaults.redis,
            "mailpit": defaults.mailpit,
            "phpmyadmin": defaults.phpmyadmin,
            "meilisearch": defaults.meilisearch,
            "elasticsearch": defaults.elasticsearch,
        }
    )
    return PortsConfig(**chosen)


def _merge_extensions(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for ext in group:
            if ext not in seen:
                seen.add(ext)
                out.append(ext)
    return out


def _services_from(names: list[str]) -> ServicesConfig:
    s = ServicesConfig()
    for name in names:
        if hasattr(s, name):
            setattr(s, name, True)
    return s


def _kv(label: str, value: str) -> None:
    """Print an aligned key/value line for the summary."""
    console.print(f"    [muted]{label:<16}[/muted] {value}")


def _print_urls(cfg: ProjectConfig) -> None:
    scheme = "https" if cfg.ssl.enabled else "http"
    port = cfg.ports.https if cfg.ssl.enabled else cfg.ports.http
    db = cfg.database

    console.print()
    console.rule(f"[title]{cfg.name}[/title] — environment ready", align="left")

    # --- URLs ----------------------------------------------------------
    console.print("[title]URLs[/title]")
    _kv("App", f"{scheme}://localhost:{port}")
    if cfg.services.mailpit:
        _kv("Mailpit", f"http://localhost:{cfg.ports.mailpit}")
    if cfg.services.phpmyadmin and db.engine != "sqlite":
        _kv("phpMyAdmin", f"http://localhost:{cfg.ports.phpmyadmin}")
    if cfg.services.meilisearch:
        _kv("Meilisearch", f"http://localhost:{cfg.ports.meilisearch}")
    if cfg.services.elasticsearch:
        _kv("Elasticsearch", f"http://localhost:{cfg.ports.elasticsearch}")

    # --- Database ------------------------------------------------------
    console.print("[title]Database[/title]")
    if db.engine == "sqlite":
        _kv("Engine", "SQLite (file-based — no server)")
    else:
        driver = "pgsql" if db.engine == "postgres" else "mysql"
        cport = 5432 if db.engine == "postgres" else 3306
        _kv("Engine", db.engine)
        _kv("Host (in app)", "db")
        _kv("Host (your PC)", f"localhost:{cfg.ports.database}")
        _kv("Database", db.name)
        _kv("Username", db.user)
        _kv("Password", db.password)
        _kv("Root login", f"root / {db.root_password}")
        _kv("Connection", f"{driver}://{db.user}:{db.password}@db:{cport}/{db.name}")

    # --- Other services ------------------------------------------------
    if cfg.services.redis or cfg.services.mailpit:
        console.print("[title]Services[/title]")
        if cfg.services.redis:
            _kv("Redis", f"redis:6379  (localhost:{cfg.ports.redis} from your PC)")
        if cfg.services.mailpit:
            _kv("Mailpit SMTP", "mailpit:1025")

    console.print(
        "[muted]    Connection details are also written to "
        ".phpbox/env/.env[/muted]"
    )


def _ensure_docker() -> None:
    if not engine.docker_available():
        error("Docker is not installed or not on PATH. Install Docker Desktop / Engine.")
        raise typer.Exit(1)


def _run_framework(ctx: typer.Context, prefix: list[str]) -> None:
    project_dir, _ = _resolve()
    _ensure_docker()
    code = engine.exec_php(project_dir, prefix + list(ctx.args), interactive=sys.stdin.isatty())
    raise typer.Exit(code)


# ---------------------------------------------------------------------------
# top-level commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show the PHPBox version."""
    console.print(f"PHPBox {__version__}")


def _detect_install() -> tuple[str, list[str] | None]:
    """Figure out how PHPBox was installed and the command to remove it.

    Returns (method, argv). ``argv`` is None if we couldn't build a command.
    """
    prefix = Path(sys.prefix)
    parts = [p.lower() for p in prefix.parts]
    is_pipx = prefix.name.lower() == "phpbox" and ("pipx" in parts or "venvs" in parts)

    if is_pipx:
        pipx = shutil.which("pipx")
        if pipx:
            return "pipx", [pipx, "uninstall", "phpbox"]
        base = shutil.which("python") or shutil.which("python3")
        if base:
            return "pipx", [base, "-m", "pipx", "uninstall", "phpbox"]
        return "pipx", None

    # pip (user / system / editable dev install)
    return "pip", [sys.executable, "-m", "pip", "uninstall", "-y", "phpbox"]


def _spawn_delayed_windows(argv: list[str]) -> None:
    """Run the uninstall in a detached process after a short delay, so PHPBox's
    own (now-exiting) process releases its file locks first."""
    quoted = subprocess.list2cmdline(argv)
    full = f"ping 127.0.0.1 -n 3 >nul & {quoted}"
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    subprocess.Popen(
        ["cmd", "/c", full],
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )


@app.command()
def uninstall(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Uninstall PHPBox from your system."""
    method, argv = _detect_install()
    if argv is None:
        error("Couldn't locate the PHPBox installation automatically.")
        info("Remove it manually with:  pipx uninstall phpbox   (or:  pip uninstall phpbox)")
        raise typer.Exit(1)

    console.print(f"This will remove PHPBox (installed via [title]{method}[/title]).")
    info("Your projects and their .phpbox/ folders are NOT affected.")
    if not yes and not typer.confirm("Uninstall PHPBox now?"):
        info("Cancelled.")
        raise typer.Exit(0)

    if os.name == "nt":
        # Windows locks the running executable — defer the removal to a detached
        # helper that runs once this process exits.
        _spawn_delayed_windows(argv)
        success("PHPBox is being removed.")
        info("This terminal's `phpbox` stops working now; open a new terminal to confirm.")
        raise typer.Exit(0)

    # POSIX: deleting in-use files is fine, so run it directly and show output.
    code = subprocess.run(argv).returncode
    if code == 0:
        success("PHPBox uninstalled.")
    else:
        error("Uninstall failed. Try manually:  pipx uninstall phpbox  /  pip uninstall phpbox")
    raise typer.Exit(code)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite an existing phpbox.yml."),
) -> None:
    """Detect an existing project and generate its environment."""
    project_dir = Path.cwd()
    if config.exists(project_dir) and not force:
        error("phpbox.yml already exists. Use --force to regenerate.")
        raise typer.Exit(1)

    step(f"Inspecting {project_dir.name}/")
    det = detection.detect(project_dir)
    info(f"Framework:  {det.label}")
    info(f"PHP:        {det.php_version}")
    if det.extensions:
        info(f"Extensions: {', '.join(det.extensions)}")
    if det.services:
        info(f"Services:   {', '.join(det.services)}")

    cfg = ProjectConfig(
        name=_slug(project_dir.name),
        framework=det.framework,
        document_root=det.document_root,
        php=PhpConfig(
            version=det.php_version,
            extensions=_merge_extensions(PhpConfig().extensions, det.extensions),
        ),
        composer=ComposerConfig(),
        server=ServerConfig(),
        database=DatabaseConfig(
            name=_slug(project_dir.name),
            user=_slug(project_dir.name),
            password=_slug(project_dir.name),
        ),
        services=_services_from(det.services),
        ports=_allocated_ports(),
    )
    # Plain PHP / sqlite-less projects keep the DB; users can switch with `phpbox db`.
    _save_and_regen(project_dir, cfg)
    success("Wrote phpbox.yml and .phpbox/ environment.")
    info("Next: `phpbox start`")


@app.command()
def create(
    framework: str = typer.Argument(..., help="laravel, symfony, codeigniter, cakephp, yii, wordpress, ..."),
    name: str = typer.Argument(..., help="Project directory name."),
) -> None:
    """Scaffold a brand-new project for a framework."""
    plugin = plugins.get(framework)
    if plugin is None:
        error(f"Unknown framework '{framework}'. Known: {', '.join(plugins.names())}")
        raise typer.Exit(1)
    _ensure_docker()

    target = Path.cwd() / name
    if target.exists() and any(target.iterdir()):
        error(f"Directory '{name}' already exists and is not empty.")
        raise typer.Exit(1)
    target.mkdir(parents=True, exist_ok=True)

    db_name = _slug(name)
    cfg = ProjectConfig(
        name=_slug(name),
        framework=plugin.name,
        document_root=plugin.document_root,
        php=PhpConfig(
            version=plugin.php_version or PhpConfig().version,
            extensions=_merge_extensions(PhpConfig().extensions, plugin.extensions()),
        ),
        database=DatabaseConfig(name=db_name, user=db_name, password=db_name),
        services=_services_from(plugin.services()),
        ports=_allocated_ports(),
    )
    _save_and_regen(target, cfg)
    success(f"Created {name}/phpbox.yml ({plugin.label})")

    step("Building PHP image (first run can take a few minutes)…")
    if engine.build(target, "php") != 0:
        error("Image build failed.")
        raise typer.Exit(1)

    steps = plugin.create_steps(name)
    if steps is None:
        warn(f"{plugin.label} can't be scaffolded automatically (needs auth/manual download).")
        info("Add your source to the directory, then run `phpbox start`.")
        return

    # Collect any credentials the framework needs (e.g. Magento access keys).
    creds: dict[str, str] = {}
    for cred in plugin.create_credentials():
        value = os.environ.get(cred.env)
        if not value:
            value = typer.prompt(cred.prompt, hide_input=cred.secret)
        creds[cred.env] = value
    create_env = plugin.create_env(creds) if creds else {}

    step(f"Scaffolding {plugin.label}…")
    if engine.run_once(target, " && ".join(steps), env=create_env) != 0:
        error("Scaffolding failed. The image is built — add sources manually and run `phpbox start`.")
        raise typer.Exit(1)

    step("Starting environment…")
    generator.generate(target, cfg)
    engine.up(target, build=False)
    _print_urls(cfg)
    note = plugin.post_create_note()
    if note:
        console.print()
        info(note)
    info(f"cd {name}")


@app.command()
def start(
    build: bool = typer.Option(True, "--build/--no-build", help="Rebuild images before starting."),
) -> None:
    """Generate config and start the environment."""
    project_dir, cfg = _resolve()
    _ensure_docker()
    generator.generate(project_dir, cfg)

    if cfg.ssl.enabled and not certs.have_certs(project_dir):
        step("Generating local TLS certificate…")
        ok, method = certs.ensure(project_dir, cfg)
        if ok:
            success(f"Certificate ready ({method}).")
        else:
            warn("Could not generate a certificate; starting without HTTPS may fail.")

    step("Starting containers…")
    code = engine.up(project_dir, build=build)
    if code != 0:
        raise typer.Exit(code)
    _print_urls(cfg)


@app.command()
def stop() -> None:
    """Stop the environment (containers preserved)."""
    project_dir, _ = _resolve()
    raise typer.Exit(engine.stop(project_dir))


@app.command()
def restart() -> None:
    """Restart the environment."""
    project_dir, _ = _resolve()
    raise typer.Exit(engine.restart(project_dir))


@app.command()
def down(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Also remove named volumes."),
) -> None:
    """Tear down containers and networks."""
    project_dir, _ = _resolve()
    raise typer.Exit(engine.down(project_dir, volumes=volumes))


@app.command()
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Stream logs."),
    service: str = typer.Argument(None, help="Limit to a single service (php, web, db, …)."),
) -> None:
    """Show container logs."""
    project_dir, _ = _resolve()
    raise typer.Exit(engine.logs(project_dir, follow=follow, service=service))


@app.command()
def shell(
    service: str = typer.Argument("php", help="Service to open a shell in."),
) -> None:
    """Open an interactive shell inside a container."""
    project_dir, _ = _resolve()
    _ensure_docker()
    # Prefer bash, fall back to sh.
    code = engine.exec_service(project_dir, ["bash"], service=service, interactive=True)
    if code != 0:
        code = engine.exec_service(project_dir, ["sh"], service=service, interactive=True)
    raise typer.Exit(code)


@app.command()
def detect() -> None:
    """Analyze the current project and report what PHPBox would configure."""
    project_dir = config.find_root() or Path.cwd()
    det = detection.detect(project_dir)
    console.print(f"[title]Framework:[/title] {det.label}")
    console.print(f"[title]PHP:[/title] {det.php_version}")
    if det.extensions:
        console.print("[title]Required Extensions:[/title]")
        for ext in det.extensions:
            console.print(f"  - {ext}")
    if det.services:
        console.print("[title]Recommended Services:[/title]")
        for svc in det.services:
            console.print(f"  - {svc}")


@app.command()
def doctor() -> None:
    """Run environment health checks."""
    root = config.find_root()
    cfg = config.load(root) if root else None
    project_dir = root or Path.cwd()
    console.print("[title]PHPBox Doctor[/title]")
    failed = 0
    for check in run_checks(project_dir, cfg):
        mark = "[ok]✓[/ok]" if check.ok else "[err]✗[/err]"
        detail = f" [muted]({check.detail})[/muted]" if check.detail else ""
        console.print(f"  {mark} {check.name}{detail}")
        if not check.ok:
            failed += 1
    console.print()
    if failed:
        warn(f"{failed} check(s) need attention.")
    else:
        success("All checks passed.")


@app.command()
def export() -> None:
    """Package the project into phpbox-package.zip."""
    project_dir, cfg = _resolve()
    out = project_dir / "phpbox-package.zip"
    skip_dirs = {".git", "node_modules", "vendor"}
    skip_phpbox = {"data", "backups", "cache"}

    step(f"Exporting {cfg.name}…")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in project_dir.rglob("*"):
            if path == out:
                continue
            rel = path.relative_to(project_dir)
            parts = rel.parts
            if parts[0] in skip_dirs:
                continue
            if parts[0] == ".phpbox" and len(parts) > 1 and parts[1] in skip_phpbox:
                continue
            if path.is_file():
                zf.write(path, rel.as_posix())
    success(f"Created {out.name}")


@app.command(name="import")
def import_package(
    archive: str = typer.Argument(..., help="Path to a phpbox-package.zip."),
) -> None:
    """Unpack a phpbox-package.zip into the current directory."""
    src = Path(archive)
    if not src.exists():
        error(f"Archive not found: {archive}")
        raise typer.Exit(1)
    dest = Path.cwd()
    step(f"Importing {src.name}…")
    with zipfile.ZipFile(src) as zf:
        zf.extractall(dest)
    success("Imported. Run `phpbox start` to launch.")


# ---- backup / restore (colon-style commands from the spec) ----------------


@app.command(name="db:backup")
def db_backup() -> None:
    """Dump the database into .phpbox/backups/."""
    project_dir, cfg = _resolve()
    _ensure_docker()
    if cfg.database.engine == "sqlite":
        error("SQLite databases live in your project files — back them up directly.")
        raise typer.Exit(1)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = project_dir / config.PHPBOX_DIR / "backups" / f"{cfg.database.name}-{stamp}.sql"
    out.parent.mkdir(parents=True, exist_ok=True)

    if cfg.database.engine == "postgres":
        dump = f"PGPASSWORD='{cfg.database.password}' pg_dump -U {cfg.database.user} {cfg.database.name}"
    else:
        dump = f"mysqldump -u root -p'{cfg.database.root_password}' {cfg.database.name}"

    cmd = engine.command(project_dir, ["exec", "-T", "db", "sh", "-c", dump])
    import subprocess

    with out.open("wb") as fh:
        code = subprocess.run(cmd, stdout=fh).returncode
    if code != 0:
        error("Backup failed (is the db container running?).")
        out.unlink(missing_ok=True)
        raise typer.Exit(code)
    success(f"Saved {out.relative_to(project_dir)}")


@app.command(name="db:restore")
def db_restore(
    backup: str = typer.Argument(..., help="Path to a .sql dump (relative paths resolve to backups/)."),
) -> None:
    """Restore the database from a SQL dump."""
    project_dir, cfg = _resolve()
    _ensure_docker()
    path = Path(backup)
    if not path.exists():
        path = project_dir / config.PHPBOX_DIR / "backups" / backup
    if not path.exists():
        error(f"Backup not found: {backup}")
        raise typer.Exit(1)

    if cfg.database.engine == "postgres":
        restore = f"PGPASSWORD='{cfg.database.password}' psql -U {cfg.database.user} {cfg.database.name}"
    else:
        restore = f"mysql -u root -p'{cfg.database.root_password}' {cfg.database.name}"

    cmd = engine.command(project_dir, ["exec", "-T", "db", "sh", "-c", restore])
    import subprocess

    with path.open("rb") as fh:
        code = subprocess.run(cmd, stdin=fh).returncode
    if code != 0:
        error("Restore failed.")
        raise typer.Exit(code)
    success("Database restored.")


@app.command(name="ssl")
def ssl(action: str = typer.Argument("enable", help="enable | disable")) -> None:
    """Toggle local SSL (https) for the project."""
    project_dir, cfg = _resolve()
    cfg.ssl.enabled = action != "disable"
    _save_and_regen(project_dir, cfg)
    if cfg.ssl.enabled:
        success(f"SSL enabled — https://localhost:{cfg.ports.https}")
        info("A certificate is generated automatically on `phpbox start`")
        info("(mkcert is used if installed for a browser-trusted cert; otherwise self-signed).")
    else:
        success("SSL disabled.")
    info("Run `phpbox start` to apply.")


# ---------------------------------------------------------------------------
# framework passthrough commands
# ---------------------------------------------------------------------------


@app.command(context_settings=PASSTHROUGH_CTX)
def artisan(ctx: typer.Context) -> None:
    """Laravel: run `php artisan` in the container."""
    _run_framework(ctx, PASSTHROUGH["artisan"])


@app.command(context_settings=PASSTHROUGH_CTX)
def spark(ctx: typer.Context) -> None:
    """CodeIgniter 4: run `php spark`."""
    _run_framework(ctx, PASSTHROUGH["spark"])


@app.command(context_settings=PASSTHROUGH_CTX)
def wp(ctx: typer.Context) -> None:
    """WordPress: run WP-CLI."""
    _run_framework(ctx, PASSTHROUGH["wp"])


@app.command(context_settings=PASSTHROUGH_CTX)
def cake(ctx: typer.Context) -> None:
    """CakePHP: run `bin/cake`."""
    _run_framework(ctx, PASSTHROUGH["cake"])


@app.command(name="console", context_settings=PASSTHROUGH_CTX)
def console_cmd(ctx: typer.Context) -> None:
    """Symfony: run `php bin/console`."""
    _run_framework(ctx, PASSTHROUGH["console"])


@app.command(context_settings=PASSTHROUGH_CTX)
def yii(ctx: typer.Context) -> None:
    """Yii: run `php yii`."""
    _run_framework(ctx, PASSTHROUGH["yii"])


@app.command(context_settings=PASSTHROUGH_CTX)
def drush(ctx: typer.Context) -> None:
    """Drupal: run `drush`."""
    _run_framework(ctx, PASSTHROUGH["drush"])


@app.command(context_settings=PASSTHROUGH_CTX)
def magento(ctx: typer.Context) -> None:
    """Magento: run `php bin/magento`."""
    _run_framework(ctx, PASSTHROUGH["magento"])


@app.command(context_settings=PASSTHROUGH_CTX)
def joomla(ctx: typer.Context) -> None:
    """Joomla: run the Joomla console."""
    _run_framework(ctx, PASSTHROUGH["joomla"])


@app.command(context_settings=PASSTHROUGH_CTX)
def composer(ctx: typer.Context) -> None:
    """Run Composer in the container, or `composer use <version>` to switch it."""
    project_dir, cfg = _resolve()
    _ensure_docker()
    args = list(ctx.args)
    if len(args) >= 2 and args[0] == "use":
        cfg.composer = ComposerConfig(version=args[1])
        _save_and_regen(project_dir, cfg)
        success(f"Composer pinned to {args[1]}. Rebuilding image…")
        raise typer.Exit(engine.build(project_dir, "php"))
    code = engine.exec_php(project_dir, ["composer", *args], interactive=sys.stdin.isatty())
    raise typer.Exit(code)


# ---------------------------------------------------------------------------
# php / server / db / extension / service sub-apps
# ---------------------------------------------------------------------------

php_app = typer.Typer(help="Manage the PHP runtime version.", no_args_is_help=True)
app.add_typer(php_app, name="php")


@php_app.command("use")
def php_use(version: str = typer.Argument(..., help=f"One of: {', '.join(SUPPORTED_PHP)}")) -> None:
    """Switch the PHP version."""
    if version not in SUPPORTED_PHP:
        error(f"Unsupported PHP version. Choose from: {', '.join(SUPPORTED_PHP)}")
        raise typer.Exit(1)
    project_dir, cfg = _resolve()
    cfg.php.version = version
    _save_and_regen(project_dir, cfg)
    success(f"PHP set to {version}. Rebuilding image…")
    _ensure_docker()
    raise typer.Exit(engine.build(project_dir, "php"))


server_app = typer.Typer(help="Switch the web server.", no_args_is_help=True)
app.add_typer(server_app, name="server")


def _make_server_cmd(server_type: str):
    def _cmd() -> None:
        project_dir, cfg = _resolve()
        cfg.server = ServerConfig(type=server_type)
        _save_and_regen(project_dir, cfg)
        success(f"Web server set to {server_type}. Run `phpbox start` to apply.")

    return _cmd


for _srv in SUPPORTED_SERVERS:
    server_app.command(_srv, help=f"Use {_srv}.")(_make_server_cmd(_srv))


db_app = typer.Typer(help="Switch the database engine.", no_args_is_help=True)
app.add_typer(db_app, name="db")


def _make_db_cmd(engine_name: str):
    def _cmd() -> None:
        project_dir, cfg = _resolve()
        cfg.database.engine = engine_name
        if engine_name == "postgres":
            cfg.database.version = "16"
        elif engine_name == "mysql":
            cfg.database.version = "8.4"
        elif engine_name == "mariadb":
            cfg.database.version = "11"
        if engine_name == "sqlite":
            cfg.services.phpmyadmin = False
        _save_and_regen(project_dir, cfg)
        success(f"Database engine set to {engine_name}. Run `phpbox start` to apply.")

    return _cmd


for _db in SUPPORTED_DB:
    db_app.command(_db, help=f"Use {_db}.")(_make_db_cmd(_db))


ext_app = typer.Typer(help="Manage PHP extensions.", no_args_is_help=True)
app.add_typer(ext_app, name="ext")


@ext_app.command("list")
def ext_list() -> None:
    """List supported and currently enabled extensions."""
    root = config.find_root()
    enabled = set(config.load(root).php.extensions) if root else set()
    console.print("[title]Extensions[/title] [muted](● enabled)[/muted]")
    for name in extensions.supported():
        mark = "[ok]●[/ok]" if name in enabled else "[muted]○[/muted]"
        console.print(f"  {mark} {name}")


@ext_app.command("install")
def ext_install(name: str = typer.Argument(..., help="Extension name, e.g. redis")) -> None:
    """Add an extension and rebuild the PHP image."""
    project_dir, cfg = _resolve()
    if name not in cfg.php.extensions:
        cfg.php.extensions.append(name)
    _save_and_regen(project_dir, cfg)
    success(f"Added {name}. Rebuilding image…")
    _ensure_docker()
    raise typer.Exit(engine.build(project_dir, "php"))


@ext_app.command("remove")
def ext_remove(name: str = typer.Argument(..., help="Extension name to remove")) -> None:
    """Remove an extension and rebuild the PHP image."""
    project_dir, cfg = _resolve()
    if name in cfg.php.extensions:
        cfg.php.extensions.remove(name)
    _save_and_regen(project_dir, cfg)
    success(f"Removed {name}. Rebuilding image…")
    _ensure_docker()
    raise typer.Exit(engine.build(project_dir, "php"))


def _toggle_service(attr: str, enabled: bool, label: str) -> None:
    project_dir, cfg = _resolve()
    setattr(cfg.services, attr, enabled)
    _save_and_regen(project_dir, cfg)
    state = "enabled" if enabled else "disabled"
    success(f"{label} {state}. Run `phpbox start` to apply.")


redis_app = typer.Typer(help="Manage the Redis service.", no_args_is_help=True)
app.add_typer(redis_app, name="redis")
redis_app.command("enable")(lambda: _toggle_service("redis", True, "Redis"))
redis_app.command("disable")(lambda: _toggle_service("redis", False, "Redis"))


mail_app = typer.Typer(help="Manage the Mailpit service.", no_args_is_help=True)
app.add_typer(mail_app, name="mail")
mail_app.command("enable")(lambda: _toggle_service("mailpit", True, "Mailpit"))
mail_app.command("disable")(lambda: _toggle_service("mailpit", False, "Mailpit"))


pma_app = typer.Typer(help="Manage phpMyAdmin.", no_args_is_help=True)
app.add_typer(pma_app, name="phpmyadmin")
pma_app.command("enable")(lambda: _toggle_service("phpmyadmin", True, "phpMyAdmin"))
pma_app.command("disable")(lambda: _toggle_service("phpmyadmin", False, "phpMyAdmin"))


search_app = typer.Typer(help="Enable a search engine service.", no_args_is_help=True)
app.add_typer(search_app, name="search")
search_app.command("meilisearch")(lambda: _toggle_service("meilisearch", True, "Meilisearch"))
search_app.command("elasticsearch")(lambda: _toggle_service("elasticsearch", True, "Elasticsearch"))


if __name__ == "__main__":
    app()
