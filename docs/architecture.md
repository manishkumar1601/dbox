# Architecture

DBox is a thin, deterministic layer on top of `docker compose`. It never asks
you to install PHP, Composer, a web server, or a database — those all run in
containers described by files DBox generates from a single config.

## High-level flow

```
                    ┌──────────────┐
   dbox.yml ─────▶│  config.py   │  load() → ProjectConfig
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
                    .dbox/ artifacts                   templates/*.j2
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
| `dbox.yml` | **Commit it.** | The single source of truth describing the environment. |
| `.dbox/` | Mostly ignored. | Generated artifacts. Regenerated on every `start`; data dirs are git-ignored. |

Because the artifacts are always regenerated from `dbox.yml`, you can delete
`.dbox/` at any time and `dbox start` will rebuild it. The only stateful
parts are `.dbox/data/` (database files) and `.dbox/backups/`.

## Generated `.dbox/` layout

```
.dbox/
├── docker-compose.yml          # the whole stack
├── php/                        # PHP runtime only
│   ├── Dockerfile              # FROM php:<ver>-fpm (or -apache), extensions, composer
│   └── php.ini                 # rendered from php.ini in dbox.yml
├── app/                        # Go / Rust runtimes only
│   ├── Dockerfile              # FROM golang:<ver>-bookworm or rust:<ver>-bookworm
│   └── .air.toml               # live-reload config (Go only)
├── nginx/default.conf          # when server = nginx           (PHP)
├── caddy/Caddyfile             # when server = caddy           (PHP)
├── litespeed/                  # when server = litespeed       (PHP)
│   ├── httpd_config.conf
│   └── vhconf.conf
├── apache/ssl.conf             # when server = apache and ssl enabled (PHP)
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
| `config.py` | `ProjectConfig` dataclasses, YAML load/save, and `find_root()` (walks up to locate `dbox.yml`). |
| `detection.py` | Inspects a directory to infer framework, PHP version, extensions, services. |
| `plugins/` | One `FrameworkPlugin` per framework. The registry (`plugins/__init__.py`) selects the best match by `priority`. |
| `generator.py` | Builds the render context and writes `.dbox/` from the Jinja2 templates. |
| `extensions.py` | Metadata mapping each extension to its install method (`core` / `pecl` / `builtin`) and required apt packages. |
| `engine.py` | Wraps `docker compose` (`up`, `down`, `build`, `logs`, `exec`, `run --rm`). |
| `ports.py` | Finds free host ports, avoiding collisions between concurrent projects. |
| `certs.py` | Generates local TLS certs (mkcert if available, otherwise self-signed via the PHP container). |
| `doctor.py` | Read-only health checks. |
| `console.py` | Rich output helpers; forces UTF-8 so glyphs render on legacy Windows code pages. |
| `templates/` | Jinja2 sources for all generated artifacts. |

## Container topology

The topology depends on the project's `runtime`. See [runtimes.md](runtimes.md)
for a side-by-side comparison.

**PHP runtime** — DBox favours separate containers for web, PHP, and database:

* `php` — PHP-FPM, built from the generated Dockerfile (your extensions live here).
* `web` — nginx / Caddy / OpenLiteSpeed, talking to `php` over FastCGI on port 9000.
* `db` — MariaDB / MySQL / PostgreSQL (omitted for SQLite).
* optional: `redis`, `mailpit`, `phpmyadmin`, `meilisearch`, `elasticsearch`.

**Apache is the exception:** it runs as `php:<ver>-apache` (mod_php) in the
`php` container itself, so there is no separate `web` container.

**Go / Rust runtime** — single self-serving app container, no separate web:

* `app` — `golang:<ver>-bookworm` or `rust:<ver>-bookworm`, with `air` /
  `cargo-watch` baked in for live reload. Container port (8080) maps directly
  to `ports.app` on your host.
* `db` and other services attach the same way as PHP.

All services share a project-scoped bridge network named `dbox`. The
application source is bind-mounted at `/var/www/html` (PHP) or `/app`
(Go/Rust).

> **The PHP process runs as `root` inside the container.** This is deliberate:
> Windows/macOS Docker bind mounts expose host files with ownership that a
> non-root user often can't write to, which breaks frameworks that write to
> disk (Laravel's `storage/`, Symfony's `var/`, …). Running as root sidesteps
> all bind-mount permission issues. It's a local dev environment, so this is an
> acceptable trade-off.

## Things that "just work"

A few behaviours are built in so a fresh project runs without manual fixups:

* **Auto database connection** — for Laravel, Symfony, CakePHP, and
  CodeIgniter 4, the generator injects the DB connection as environment
  variables into the app container (`DB_*` / `DATABASE_URL` /
  `database.default.*`), with `clear_env = no` in PHP-FPM so they reach PHP. No
  manual `.env` editing.
* **Wait for the database** — the `db` service has a healthcheck and the app
  container `depends_on` it `condition: service_healthy`, so the app never
  starts before the database is ready (no first-boot "connection refused").
* **Automatic free ports** — `ports.py` queries Docker for ports already
  published by other containers (a host socket check alone misses Docker's
  proxied ports) and shifts any busy port to the next free one — at create time
  *and* on every `start`.
* **Writable project dirs** — PHP runs as root in-container (see above) so
  framework write paths work regardless of host bind-mount ownership.
* **Fast image builds** — extensions install via `install-php-extensions`
  (prebuilt binaries), and a shared Composer cache speeds repeat scaffolds.

## Why shell out to `docker compose`?

Rather than the Docker SDK, DBox invokes the `docker compose` CLI. This means:

* It behaves identically on Docker Desktop and a plain Docker Engine.
* The generated `docker-compose.yml` is a first-class, inspectable artifact you
  can run by hand or hand off to teammates who don't use DBox.
* There's nothing magic to learn — it's the same Compose you already know.
