# Getting Started

> **First time / fresh machine?** Install Docker, Python, and DBox first —
> see [installation.md → First-time setup on a fresh PC](installation.md#first-time-setup-on-a-fresh-pc).
> Then come back here.

There are two entry points: **create** a brand-new project, or **init** an
existing one. Both end with `dbox start`.

## Create a new project

```bash
dbox create laravel blog
```

This will:

1. Create a `blog/` directory.
2. Write `blog/dbox.yml` with sensible defaults for Laravel (PHP 8.3, the
   extensions Laravel wants, Mailpit + phpMyAdmin enabled, MariaDB with
   `blog` / `blog` credentials).
3. Generate `blog/.dbox/` (Docker artifacts).
4. Build the PHP image.
5. Scaffold the framework (`composer create-project laravel/laravel`).
6. Start the stack and print a summary (URLs **and** database credentials).

```bash
cd blog
dbox start          # if it isn't already running
```

`start` / `create` print everything you need in one place — service URLs plus
the database host, name, username, password, and a ready-to-paste connection
string (also written to `.dbox/env/.env`):

```text
blog — environment ready ───────────────────────────────
URLs
    App              http://localhost:8080
    Mailpit          http://localhost:8025
    phpMyAdmin       http://localhost:8081
Database
    Engine           mariadb
    Host (in app)    db
    Host (your PC)   localhost:3306
    Database         blog
    Username         blog
    Password         blog
    Root login       root / root
    Connection       mysql://blog:blog@db:3306/blog
```

The generic form is:

```bash
dbox create <framework> <name>
```

See [frameworks.md](frameworks.md) for every supported `<framework>` value.

> **Magento** additionally prompts for your Marketplace access keys (or reads
> `MAGENTO_PUBLIC_KEY` / `MAGENTO_PRIVATE_KEY` from the environment). See
> [frameworks.md](frameworks.md#magento).

### Create a Go or Rust project

DBox isn't PHP-only. The same `create` command works across runtimes:

```bash
dbox create gin myapi          # Go + Gin   (auto-installs gin into go.mod)
dbox create echo myapi         # Go + Echo
dbox create go myapi           # plain Go (net/http)

dbox create actix myapi        # Rust + Actix-web
dbox create axum myapi         # Rust + Axum
dbox create rust myapi         # plain Rust
```

Go and Rust projects come with **live reload** baked in (`air` and
`cargo-watch`) and auto-wire to the DBox database — Gin/Echo via `DB_*` env
vars, Actix/Axum via `DATABASE_URL`. The app container exposes its port
directly (default `7090`). See [runtimes.md](runtimes.md) for the full
picture. Use `dbox go …` / `dbox cargo …` to run the toolchain inside the
container.

## Adopt an existing project

```bash
git clone https://github.com/acme/shop
cd shop
dbox init
dbox start
```

`dbox init` inspects the directory and infers:

* **Framework** — from marker files and `composer.json`
* **PHP version** — from the `php` constraint in `composer.json`
* **Extensions** — framework defaults plus any `ext-*` in `composer.json`
* **Services** — framework defaults (e.g. Mailpit + phpMyAdmin for Laravel)

It then writes `dbox.yml` and `.dbox/`. Re-run with `--force` to overwrite
an existing `dbox.yml`.

Preview what it would do without writing anything:

```bash
dbox detect
```

## Everyday workflow

```bash
dbox start                 # build (if needed) + run
dbox logs -f               # tail logs
dbox shell                 # bash inside the PHP container
dbox artisan migrate       # run framework CLIs in the container
dbox composer require x/y  # Composer in the container
dbox stop                  # stop containers (data preserved)
dbox down                  # remove containers + network
dbox down -v               # …and delete the database volume
```

## Changing the environment

Edit `dbox.yml` and run `dbox start`, or use the convenience commands:

```bash
dbox php use 8.4           # switch PHP, rebuild image
dbox db postgres           # switch database engine
dbox server caddy          # switch web server
dbox ext install redis     # add an extension, rebuild image
dbox redis enable          # toggle a service
dbox ssl enable            # local HTTPS
```

All of these update `dbox.yml`, regenerate `.dbox/`, and tell you when a
`dbox start` is needed to apply the change.

## Verifying

```bash
dbox doctor
```

Checks Docker, the config, framework detection, the running containers, the
database/Redis services, recommended extensions, and SSL.
