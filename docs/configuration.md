# Configuration — `dbox.yml`

`dbox.yml` is the single source of truth for a project's environment. It is
created by `dbox init` / `dbox create`, can be edited by hand, and is read
on every `dbox start` to regenerate the `.dbox/` artifacts.

## Full example

```yaml
name: blog
framework: laravel
document_root: /public

php:
  version: "8.4"
  extensions:
    - gd
    - zip
    - intl
    - pdo_mysql
    - opcache
    - redis
  ini:
    memory_limit: 256M
    upload_max_filesize: 64M
    post_max_size: 64M
    max_execution_time: "120"

composer:
  version: latest

server:
  type: nginx            # nginx | apache | litespeed | caddy

database:
  engine: mariadb        # mariadb | mysql | postgres | sqlite
  version: "11"
  name: blog
  user: blog             # defaults to the project name
  password: blog         # defaults to the project name
  root_password: root    # admin login is always root / root

services:
  redis: false
  mailpit: true
  meilisearch: false
  elasticsearch: false
  phpmyadmin: true

ssl:
  enabled: false
  host: app.localhost

ports:
  http: 8080
  https: 8443
  database: 3306
  redis: 6379
  mailpit: 8025
  phpmyadmin: 8081
  meilisearch: 7700
  elasticsearch: 9200
```

## Field reference

### Top level

| Key | Type | Default | Description |
|---|---|---|---|
| `name` | string | dir name | Project name; used for container names. |
| `framework` | string | `corephp` | One of the [supported frameworks](frameworks.md). |
| `runtime` | string | `php` | Language runtime: `php` \| `go` \| `rust`. Omitted in the YAML when `php` for backward compat. |
| `document_root` | string | `/public` | Web root relative to the app root (PHP only). |

### `php` (PHP runtime only)

| Key | Type | Default | Description |
|---|---|---|---|
| `version` | string | `8.3` | One of `7.4`, `8.0`, `8.1`, `8.2`, `8.3`, `8.4`. |
| `extensions` | list | `[gd, zip, intl, pdo_mysql, opcache]` | Extensions baked into the PHP image. See [extensions.md](extensions.md). |
| `ini` | map | see example | Key/value pairs written to a `php.ini` overlay. Any php.ini directive is allowed. |

### `composer` (PHP runtime only)

| Key | Type | Default | Description |
|---|---|---|---|
| `version` | string | `latest` | Maps to a `composer:<version>` image tag (e.g. `2.8`). |

### `go` (Go runtime only)

| Key | Type | Default | Description |
|---|---|---|---|
| `version` | string | `1.25` | One of `1.23`, `1.24`, `1.25`. Maps to `golang:<version>-bookworm`. |

### `rust` (Rust runtime only)

| Key | Type | Default | Description |
|---|---|---|---|
| `version` | string | `stable` | One of `1.75`, `1.80`, `stable`. Maps to `rust:<version>-bookworm`. |

### `server`

| Key | Type | Default | Description |
|---|---|---|---|
| `type` | string | `nginx` | `nginx`, `apache`, `litespeed`, or `caddy`. See [web-servers.md](web-servers.md). |

### `database`

| Key | Type | Default | Description |
|---|---|---|---|
| `engine` | string | `mariadb` | `mariadb`, `mysql`, `postgres`, or `sqlite`. |
| `version` | string | `11` | Image tag for the engine. |
| `name` | string | project name | Database name. |
| `user` | string | project name | Application database user. |
| `password` | string | project name | Password for `user`. |
| `root_password` | string | `root` | Root/superuser password (admin login is `root` / `root`). |

> `dbox create <fw> <name>` / `dbox init` set `name`, `user`, and
> `password` all to the project name. So a project called `blog` gets database
> `blog`, user `blog`, password `blog` — plus the `root` / `root` admin login.
>
> SQLite uses no container — store the database file in your project.

### `services`

Booleans that add or remove companion containers. The "Default" column is the
raw field default; on `create`/`init` each **framework enables a sensible set**
on top of this (e.g. Laravel turns on Mailpit + phpMyAdmin) — see
[frameworks.md](frameworks.md#default-services-per-framework) and
[services.md](services.md).

| Key | Default | Service |
|---|---|---|
| `redis` | `false` | Redis cache/queue |
| `mailpit` | `false` | Mailpit SMTP catcher (`http://localhost:8025`) |
| `meilisearch` | `false` | Meilisearch |
| `elasticsearch` | `false` | Elasticsearch |
| `phpmyadmin` | `false` | phpMyAdmin (ignored for SQLite) |

### `ssl`

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `false` | Enable HTTPS. A cert is generated automatically on `start`. |
| `host` | string | `app.localhost` | Common name used for the generated certificate. |

See [ssl.md](ssl.md).

### `ports`

Preferred **host** ports. On `init`/`create` these are auto-adjusted upward to
avoid collisions with other running projects, so two DBox apps never fight
over `8080`.

| Key | Default | Maps to | Runtime |
|---|---|---|---|
| `http` | `7010` | web :80 | PHP |
| `https` | `7020` | web :443 (when SSL enabled) | PHP |
| `app` | `7090` | app container :8080 | Go / Rust |
| `database` | `7030` | db engine port | all |
| `redis` | `7040` | redis :6379 | all |
| `mailpit` | `7050` | mailpit web UI | all |
| `phpmyadmin` | `7060` | phpMyAdmin :80 | all |
| `meilisearch` | `7070` | meilisearch :7700 | all |
| `elasticsearch` | `7080` | elasticsearch :9200 | all |

## Editing by hand vs. commands

Both are equivalent. These commands just edit `dbox.yml` and regenerate:

| Command | Field changed |
|---|---|
| `dbox php use 8.4` | `php.version` |
| `dbox composer use 2.8` | `composer.version` |
| `dbox server caddy` | `server.type` |
| `dbox db postgres` | `database.engine` (+ a sensible `version`) |
| `dbox ext install redis` | appends to `php.extensions` |
| `dbox redis enable` | `services.redis` |
| `dbox ssl enable` | `ssl.enabled` |

The `.env` DBox writes to `.dbox/env/.env` contains in-container connection
details (`DB_HOST=db`, `REDIS_HOST=redis`, `MAIL_HOST=mailpit`, …) you can copy
into your application's own `.env`.
