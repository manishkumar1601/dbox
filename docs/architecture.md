# Architecture

PHPBox is a thin, deterministic layer on top of `docker compose`. It never asks
you to install PHP, Composer, a web server, or a database — those all run in
containers described by files PHPBox generates from a single config.

## High-level flow

```
                    ┌──────────────┐
   phpbox.yml ─────▶│  config.py   │  load() → ProjectConfig
                    └──────┬───────┘
                           │
              detection.py │ (init / detect only)
   project files ─────────▶│  infer framework, PHP, extensions, services
                           ▼
                    ┌──────────────┐   extensions.resolve()
                    │ generator.py │◀──────────────────────────┐
                    └──────┬───────┘                            │
                           │ renders Jinja2 templates           │
                           ▼                                    │
                    .phpbox/ artifacts                   templates/*.j2
              (docker-compose.yml, Dockerfile,
               php.ini, server config, .env)
                           │
                           ▼
                    ┌──────────────┐
                    │  engine.py   │  docker compose up/exec/logs/down
                    └──────┬───────┘
                           ▼
                  Docker containers (php, web, db, redis, …)
```

## The two project files

| Path | Tracked? | Purpose |
|---|---|---|
| `phpbox.yml` | **Commit it.** | The single source of truth describing the environment. |
| `.phpbox/` | Mostly ignored. | Generated artifacts. Regenerated on every `start`; data dirs are git-ignored. |

Because the artifacts are always regenerated from `phpbox.yml`, you can delete
`.phpbox/` at any time and `phpbox start` will rebuild it. The only stateful
parts are `.phpbox/data/` (database files) and `.phpbox/backups/`.

## Generated `.phpbox/` layout

```
.phpbox/
├── docker-compose.yml          # the whole stack
├── php/
│   ├── Dockerfile              # FROM php:<ver>-fpm (or -apache), extensions, composer
│   └── php.ini                 # rendered from php.ini in phpbox.yml
├── nginx/default.conf          # when server = nginx
├── caddy/Caddyfile             # when server = caddy
├── litespeed/                  # when server = litespeed
│   ├── httpd_config.conf
│   └── vhconf.conf
├── apache/ssl.conf             # when server = apache and ssl enabled
├── env/.env                    # connection details for your app's .env
├── certs/                      # cert.pem / key.pem when ssl enabled
├── data/{mariadb,mysql,postgres}/   # persistent DB storage (bind mounts)
├── backups/                    # db:backup output
└── cache/
```

## Modules

| Module | Responsibility |
|---|---|
| `cli.py` | Typer application. Defines every command and wires the modules together. |
| `config.py` | `ProjectConfig` dataclasses, YAML load/save, and `find_root()` (walks up to locate `phpbox.yml`). |
| `detection.py` | Inspects a directory to infer framework, PHP version, extensions, services. |
| `plugins/` | One `FrameworkPlugin` per framework. The registry (`plugins/__init__.py`) selects the best match by `priority`. |
| `generator.py` | Builds the render context and writes `.phpbox/` from the Jinja2 templates. |
| `extensions.py` | Metadata mapping each extension to its install method (`core` / `pecl` / `builtin`) and required apt packages. |
| `engine.py` | Wraps `docker compose` (`up`, `down`, `build`, `logs`, `exec`, `run --rm`). |
| `ports.py` | Finds free host ports, avoiding collisions between concurrent projects. |
| `certs.py` | Generates local TLS certs (mkcert if available, otherwise self-signed via the PHP container). |
| `doctor.py` | Read-only health checks. |
| `console.py` | Rich output helpers; forces UTF-8 so glyphs render on legacy Windows code pages. |
| `templates/` | Jinja2 sources for all generated artifacts. |

## Container topology

PHPBox favours **separate containers** for the web server, PHP runtime, and
database:

* `php` — PHP-FPM, built from the generated Dockerfile (your extensions live here).
* `web` — nginx / Caddy / OpenLiteSpeed, talking to `php` over FastCGI on port 9000.
* `db` — MariaDB / MySQL / PostgreSQL (omitted for SQLite).
* optional: `redis`, `mailpit`, `phpmyadmin`, `meilisearch`, `elasticsearch`.

**Apache is the exception:** it runs as `php:<ver>-apache` (mod_php) in the
`php` container itself, so there is no separate `web` container. See
[web-servers.md](web-servers.md) for the reasoning.

All services share a project-scoped bridge network named `phpbox`, and your
application source is bind-mounted into every container at `/var/www/html`.

## Why shell out to `docker compose`?

Rather than the Docker SDK, PHPBox invokes the `docker compose` CLI. This means:

* It behaves identically on Docker Desktop and a plain Docker Engine.
* The generated `docker-compose.yml` is a first-class, inspectable artifact you
  can run by hand or hand off to teammates who don't use PHPBox.
* There's nothing magic to learn — it's the same Compose you already know.
