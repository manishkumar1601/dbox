# PHPBox

**Universal PHP Development Environment Manager** — create and run any PHP
framework or CMS with only Docker installed. No PHP, Composer, Apache, Nginx,
MySQL, XAMPP/WAMP/MAMP/Laragon on your host.

```bash
phpbox create laravel blog      # scaffold a new project
cd blog && phpbox start         # build + run it

# …or for an existing repo:
git clone <project> && cd project
phpbox init
phpbox start
```

---

## Requirements

* **Docker Desktop** (Windows / macOS) or **Docker Engine + Compose** (Linux)
* Python 3.12+ (only to run the CLI itself)

## Install

### Recommended: clone, run the install script, done

The install script **installs everything you need**: if Python or Docker are
missing, it installs them (via `winget` on Windows, Homebrew/apt on macOS/Linux),
then installs PHPBox itself as a **global, isolated** tool (via `pipx`) so the
`phpbox` command works in **any folder**. Because nothing is installed
"editable", **you can delete the cloned repo afterwards.**

```bash
git clone https://github.com/manishkumar1601/phpbox
cd phpbox

# Linux / macOS
./scripts/install.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

Then open a **new terminal** and:

```bash
phpbox --help
phpbox doctor          # checks Docker is installed and running

cd ..
rm -rf phpbox          # ✅ safe — the clone is no longer needed
```

> ⚠️ **Docker Desktop needs a reboot + manual first launch** before your first
> `phpbox start` (no installer can start the Docker engine for you). The script
> installs it and reminds you.
>
> Flags: `-SkipDeps` / `--skip-deps` to skip installing Python/Docker;
> `-Pip` / `--pip` to use `pip` instead of `pipx`.
> Uninstall any time by running **`phpbox uninstall`** (or the
> `scripts/uninstall.*` scripts).

> 📖 Full fresh-PC walkthrough and troubleshooting:
> **[docs/installation.md → First-time setup on a fresh PC](docs/installation.md#first-time-setup-on-a-fresh-pc)**.

### From source (for development)

Use an **editable** install so code changes apply immediately (keep the repo):

```bash
git clone https://github.com/manishkumar1601/phpbox && cd phpbox
pip install -e .
phpbox --help
```

(or run without installing: `python -m phpbox --help`)

### Then create or run a project

```bash
phpbox create laravel blog && cd blog && phpbox start   # new project
# — or —
cd existing-project && phpbox init && phpbox start       # existing project
```

## How it works

Everything PHPBox needs lives in two places inside your project:

```
phpbox.yml      # the single source of truth — edit this
.phpbox/        # generated Docker artifacts (disposable, regenerated on start)
```

`phpbox.yml` is read by the **generator**, which renders a `docker-compose.yml`,
a PHP `Dockerfile` (with your extensions), `php.ini`, and the web-server config.
PHPBox then drives `docker compose` to build and run the stack. See
[docs/architecture.md](docs/architecture.md) for the full picture.

---

## Project structure

```
phpbox/                     repo root
├── pyproject.toml          packaging + dependencies
├── README.md
├── LICENSE
├── src/
│   └── phpbox/             the importable package (src-layout)
│       ├── cli.py          Typer CLI — wires every command
│       ├── config.py       phpbox.yml model (load / save / find_root)
│       ├── detection.py    framework + PHP version + extension inference
│       ├── generator.py    renders .phpbox/ from the config via Jinja2
│       ├── engine.py       docker compose wrapper (up/down/exec/logs…)
│       ├── extensions.py   PHP extension install metadata
│       ├── certs.py        local TLS certificate generation
│       ├── ports.py        automatic free-port detection
│       ├── doctor.py       environment health checks
│       ├── console.py      Rich output helpers
│       ├── plugins/        one module per framework (detect + scaffold + CLI)
│       └── templates/      Jinja2 templates for the generated artifacts
├── scripts/                install.sh / install.ps1 / uninstall.sh / uninstall.ps1
├── tests/                  pytest suite
└── docs/                   full documentation (see below)
```

---

## Commands at a glance

| Command | Description |
|---|---|
| `phpbox init` | Detect an existing project and generate its environment |
| `phpbox create <framework> <name>` | Scaffold a new project |
| `phpbox start` / `stop` / `restart` / `down` | Lifecycle control |
| `phpbox logs [-f] [service]` · `phpbox shell [service]` | Inspect / enter containers |
| `phpbox php use 8.4` · `phpbox composer use 2.8` | Switch runtime versions |
| `phpbox server nginx\|apache\|litespeed\|caddy` | Switch web server |
| `phpbox db mariadb\|mysql\|postgres\|sqlite` | Switch database engine |
| `phpbox ext list\|install\|remove` | Manage PHP extensions |
| `phpbox redis\|mail\|phpmyadmin\|search …` | Toggle companion services |
| `phpbox ssl enable\|disable` | Local HTTPS with auto-generated certs |
| `phpbox db:backup` · `phpbox db:restore <file>` | Database backups |
| `phpbox export` · `phpbox import <zip>` | Portable project packages |
| `phpbox detect` · `phpbox doctor` | Inspect / diagnose |
| `phpbox uninstall` | Remove PHPBox from your system |
| `phpbox artisan\|spark\|wp\|cake\|console\|yii\|drush\|magento\|joomla …` | Framework CLIs |

Full reference: [docs/commands.md](docs/commands.md).

## Supported frameworks

Laravel · Symfony · CodeIgniter 3 & 4 · CakePHP · Yii · Slim · Laminas ·
Core PHP · WordPress · Drupal · Magento · Joomla

Details and detection rules: [docs/frameworks.md](docs/frameworks.md).

---

## Documentation

| Doc | Contents |
|---|---|
| [docs/installation.md](docs/installation.md) | Requirements, install, building a standalone binary |
| [docs/getting-started.md](docs/getting-started.md) | First project, both `create` and `init` flows |
| [docs/architecture.md](docs/architecture.md) | Components, data flow, the generation pipeline |
| [docs/configuration.md](docs/configuration.md) | Complete `phpbox.yml` reference |
| [docs/commands.md](docs/commands.md) | Every CLI command and option |
| [docs/frameworks.md](docs/frameworks.md) | Supported frameworks, detection, scaffolding |
| [docs/web-servers.md](docs/web-servers.md) | nginx, Apache, Caddy, OpenLiteSpeed |
| [docs/databases.md](docs/databases.md) | Engines, backups, restore |
| [docs/extensions.md](docs/extensions.md) | Extension manager and supported extensions |
| [docs/services.md](docs/services.md) | Redis, Mailpit, phpMyAdmin, Meilisearch, Elasticsearch |
| [docs/ssl.md](docs/ssl.md) | Local HTTPS, mkcert vs self-signed |
| [docs/plugins.md](docs/plugins.md) | Writing a framework plugin |
| [docs/contributing.md](docs/contributing.md) | Dev setup, tests, conventions |

## Development

```bash
pip install -e ".[dev]"   # editable install + pytest/pyinstaller
pytest                    # run the test suite
```

## License

[MIT](LICENSE)
