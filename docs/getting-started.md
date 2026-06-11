# Getting Started

> **First time / fresh machine?** Install Docker, Python, and PHPBox first —
> see [installation.md → First-time setup on a fresh PC](installation.md#first-time-setup-on-a-fresh-pc).
> Then come back here.

There are two entry points: **create** a brand-new project, or **init** an
existing one. Both end with `phpbox start`.

## Create a new project

```bash
phpbox create laravel blog
```

This will:

1. Create a `blog/` directory.
2. Write `blog/phpbox.yml` with sensible defaults for Laravel (PHP 8.3, the
   extensions Laravel wants, Mailpit + phpMyAdmin enabled, MariaDB with
   `blog` / `blog` credentials).
3. Generate `blog/.phpbox/` (Docker artifacts).
4. Build the PHP image.
5. Scaffold the framework (`composer create-project laravel/laravel`).
6. Start the stack and print a summary (URLs **and** database credentials).

```bash
cd blog
phpbox start          # if it isn't already running
```

`start` / `create` print everything you need in one place — service URLs plus
the database host, name, username, password, and a ready-to-paste connection
string (also written to `.phpbox/env/.env`):

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
phpbox create <framework> <name>
```

See [frameworks.md](frameworks.md) for every supported `<framework>` value.

> **Magento** additionally prompts for your Marketplace access keys (or reads
> `MAGENTO_PUBLIC_KEY` / `MAGENTO_PRIVATE_KEY` from the environment). See
> [frameworks.md](frameworks.md#magento).

## Adopt an existing project

```bash
git clone https://github.com/acme/shop
cd shop
phpbox init
phpbox start
```

`phpbox init` inspects the directory and infers:

* **Framework** — from marker files and `composer.json`
* **PHP version** — from the `php` constraint in `composer.json`
* **Extensions** — framework defaults plus any `ext-*` in `composer.json`
* **Services** — framework defaults (e.g. Mailpit + phpMyAdmin for Laravel)

It then writes `phpbox.yml` and `.phpbox/`. Re-run with `--force` to overwrite
an existing `phpbox.yml`.

Preview what it would do without writing anything:

```bash
phpbox detect
```

## Everyday workflow

```bash
phpbox start                 # build (if needed) + run
phpbox logs -f               # tail logs
phpbox shell                 # bash inside the PHP container
phpbox artisan migrate       # run framework CLIs in the container
phpbox composer require x/y  # Composer in the container
phpbox stop                  # stop containers (data preserved)
phpbox down                  # remove containers + network
phpbox down -v               # …and delete the database volume
```

## Changing the environment

Edit `phpbox.yml` and run `phpbox start`, or use the convenience commands:

```bash
phpbox php use 8.4           # switch PHP, rebuild image
phpbox db postgres           # switch database engine
phpbox server caddy          # switch web server
phpbox ext install redis     # add an extension, rebuild image
phpbox redis enable          # toggle a service
phpbox ssl enable            # local HTTPS
```

All of these update `phpbox.yml`, regenerate `.phpbox/`, and tell you when a
`phpbox start` is needed to apply the change.

## Verifying

```bash
phpbox doctor
```

Checks Docker, the config, framework detection, the running containers, the
database/Redis services, recommended extensions, and SSL.
