# DBox

**Universal PHP Development Environment Manager** — create and run any PHP
framework or CMS with only Docker installed. No PHP, Composer, Apache, Nginx,
MySQL, XAMPP/WAMP/MAMP/Laragon on your host.

```bash
dbox create laravel blog      # scaffold a new project
cd blog && dbox start         # build + run it

# …or for an existing repo:
git clone <project> && cd project
dbox init
dbox start
```

---

## Requirements

* **Docker Desktop** (Windows / macOS) or **Docker Engine + Compose** (Linux)
* Python 3.12+ (only to run the CLI itself)

## Install

### One line — no clone needed

The installer pulls the **latest DBox straight from GitHub** and, if Python or
Docker are missing, installs them too (via `winget` on Windows, Homebrew/apt on
macOS/Linux). It installs DBox as a **global, isolated** tool (via `pipx`) so
`dbox` works in **any folder**.

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/manishkumar1601/dbox/master/scripts/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/manishkumar1601/dbox/master/scripts/install.sh | bash
```

Then open a **new terminal** and:

```bash
dbox --help
dbox doctor          # checks Docker is installed and running
```

> ⚠️ **Docker Desktop needs a reboot + manual first launch** before your first
> `dbox start` (no installer can start the Docker engine for you). The script
> installs it and reminds you.
>
> Update any time with **`dbox update`**, and remove it with
> **`dbox uninstall`**. DBox also tells you when a newer version is available.

> 📖 Full fresh-PC walkthrough and troubleshooting:
> **[docs/installation.md → First-time setup on a fresh PC](docs/installation.md#first-time-setup-on-a-fresh-pc)**.

### From source (for development)

Use an **editable** install so code changes apply immediately (keep the repo):

```bash
git clone https://github.com/manishkumar1601/dbox && cd dbox
pip install -e .
dbox --help
```

(or run without installing: `python -m dbox --help`)

### Then create or run a project

```bash
dbox create laravel blog && cd blog && dbox start   # new project
# — or —
cd existing-project && dbox init && dbox start       # existing project
```

## How it works

Everything DBox needs lives in two places inside your project:

```
dbox.yml      # the single source of truth — edit this
.dbox/        # generated Docker artifacts (disposable, regenerated on start)
```

`dbox.yml` is read by the **generator**, which renders a `docker-compose.yml`,
a PHP `Dockerfile` (with your extensions), `php.ini`, and the web-server config.
DBox then drives `docker compose` to build and run the stack. See
[docs/architecture.md](docs/architecture.md) for the full picture.

It aims to **just work** out of the box: free ports are picked automatically
(and re-checked on every start), the database connection is auto-wired for
Laravel/Symfony/CakePHP/CodeIgniter 4, the app waits for the database to be
ready, and a post-start summary prints every URL and credential in one place.

---

## Project structure

```
dbox/                     repo root
├── pyproject.toml          packaging + dependencies
├── README.md
├── LICENSE
├── src/
│   └── dbox/             the importable package (src-layout)
│       ├── cli.py          Typer CLI — wires every command
│       ├── config.py       dbox.yml model (load / save / find_root)
│       ├── detection.py    framework + PHP version + extension inference
│       ├── generator.py    renders .dbox/ from the config via Jinja2
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
| `dbox init` | Detect an existing project and generate its environment |
| `dbox create <framework> <name>` | Scaffold a new project |
| `dbox start` / `stop` / `restart` / `down` | Lifecycle control |
| `dbox logs [-f] [service]` · `dbox shell [service]` | Inspect / enter containers |
| `dbox php use 8.4` · `dbox composer use 2.8` | Switch runtime versions |
| `dbox server nginx\|apache\|litespeed\|caddy` | Switch web server |
| `dbox db mariadb\|mysql\|postgres\|sqlite` | Switch database engine |
| `dbox ext list\|install\|remove` | Manage PHP extensions |
| `dbox redis\|mail\|phpmyadmin\|search …` | Toggle companion services |
| `dbox ssl enable\|disable` | Local HTTPS with auto-generated certs |
| `dbox db:backup` · `dbox db:restore <file>` | Database backups |
| `dbox export` · `dbox import <zip>` | Portable project packages |
| `dbox detect` · `dbox doctor` | Inspect / diagnose |
| `dbox update` | Update DBox to the latest version from GitHub |
| `dbox uninstall` | Remove DBox from your system |
| `dbox artisan\|spark\|wp\|cake\|console\|yii\|drush\|magento\|joomla …` | Framework CLIs |

Full reference: [docs/commands.md](docs/commands.md).

## Supported frameworks

Laravel · Symfony · CodeIgniter 3 & 4 · CakePHP · Yii · Core PHP ·
WordPress · Drupal · Magento · Joomla

Details and detection rules: [docs/frameworks.md](docs/frameworks.md).

---

## Documentation

| Doc | Contents |
|---|---|
| [docs/installation.md](docs/installation.md) | Requirements, install, building a standalone binary |
| [docs/getting-started.md](docs/getting-started.md) | First project, both `create` and `init` flows |
| [docs/architecture.md](docs/architecture.md) | Components, data flow, the generation pipeline |
| [docs/configuration.md](docs/configuration.md) | Complete `dbox.yml` reference |
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
