# Runtimes

DBox supports three language runtimes. Each new project picks one via its
plugin; `dbox.yml` carries the choice in a `runtime` field (omitted when it's
`php` so legacy projects stay byte-identical).

| Runtime | Source images | Web model | Live reload |
|---|---|---|---|
| `php` | `php:<ver>-fpm` / `php:<ver>-apache` | nginx/Apache/Caddy/LiteSpeed in front of PHP-FPM (or mod_php) | n/a — interpreted |
| `go` | `golang:1.25-bookworm` | App self-serves; container port mapped to host | [`air`](https://github.com/air-verse/air) |
| `rust` | `rust:bookworm` (alias for latest stable; pinned versions use `rust:<ver>-bookworm`) | App self-serves; container port mapped to host | [`cargo-watch`](https://crates.io/crates/cargo-watch) |

## What's the same across runtimes

- **Database, Redis, Mailpit, phpMyAdmin, Meilisearch, Elasticsearch** — all
  optional services work identically. The DB has a healthcheck and the app
  waits for it (`depends_on: condition: service_healthy`).
- **Automatic DB connection** — the framework's `app_env()` injects the right
  env vars into the app container (Laravel → `DB_*`, Symfony/Actix/Axum →
  `DATABASE_URL`, Gin/Echo → `DB_DRIVER`/`DB_HOST`/…). No manual `.env` editing.
- **Auto free ports** — `dbox start` re-checks and shifts any busy host port.
- **Generated `.dbox/` tree** — regenerated on every `start`; the only thing
  you commit is `dbox.yml`.

## What's different

- **Web server** — only PHP uses nginx/Apache/Caddy/LiteSpeed. Go/Rust apps
  include their own HTTP server and are mapped to the host via `ports.app`
  (default `7090`). No reverse proxy; SSL termination is the app's job
  (deferred from DBox for now).
- **App container service name** — `php` for PHP runtime; **`app`** for Go/Rust.
- **Caches** — Go/Rust use named Docker volumes (faster than Windows bind
  mounts and avoids Cargo's case-insensitive-filesystem issues):
  - **Go**: `dbox-go-modcache` (shared, `/go/pkg/mod`),
    `dbox-<name>-gocache` (per-project, `/root/.cache/go-build`).
  - **Rust**: `dbox-cargo-cache` (shared, `/usr/local/cargo/registry`),
    `dbox-<name>-target` (per-project, `/app/target`).

## Frameworks per runtime

| Runtime | Plain runtime | First-party frameworks |
|---|---|---|
| PHP | Core PHP | Laravel · Symfony · CodeIgniter 3 & 4 · CakePHP · Yii · WordPress · Drupal · Magento · Joomla |
| Go | `dbox create go <name>` | **Gin** (`dbox create gin <name>`), **Echo** |
| Rust | `dbox create rust <name>` | **Actix-web** (`dbox create actix <name>`), **Axum** |

Detection works the same way as PHP: Go plugins scan `go.mod` for modules,
Rust plugins scan `Cargo.toml`'s `[dependencies]` for crates.

## Live reload

- **Go** — the image preinstalls [`air`](https://github.com/air-verse/air).
  DBox writes a minimal `.dbox/app/.air.toml` and the container runs
  `air -c /app/.dbox/app/.air.toml`. Save a `.go` file → rebuild + restart.
- **Rust** — the image preinstalls [`cargo-watch`](https://github.com/watchexec/cargo-watch).
  Container runs `cargo watch -x run`. Save a `.rs` file → recompile + restart.
  First build is slow (10–60s for a small app, longer with many deps); the
  shared `cargo` registry cache and per-project `target/` named volume keep
  subsequent rebuilds incremental.

## CLI inside the app container

| Runtime | Passthrough |
|---|---|
| PHP | `dbox composer …`, `dbox artisan …`, `dbox spark …`, `dbox wp …`, … |
| Go | `dbox go …` (e.g. `dbox go mod tidy`, `dbox go test ./...`) |
| Rust | `dbox cargo …` (e.g. `dbox cargo build`, `dbox cargo test`) |

PHP-only commands (`dbox composer`, `dbox php use`, `dbox ext …`) refuse to
run on non-PHP projects with a clear error.

## SSL

`dbox ssl enable` is supported for the PHP runtime only at the moment. For Go
and Rust, terminate TLS in the app itself for now (or front the container with
a reverse proxy of your choice). A managed reverse-proxy mode for Go/Rust is on
the roadmap.
