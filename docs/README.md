# DBox Documentation

DBox is a cross-platform CLI that lets you create and run any **PHP, Go, or
Rust** project using only Docker — no language toolchain, web server, or
database installed on the host.

## Contents

1. [Installation](installation.md) — requirements, install methods, standalone binary
2. [Getting Started](getting-started.md) — your first project (`create` and `init`)
3. [Architecture](architecture.md) — components, data flow, the generation pipeline
4. [Runtimes](runtimes.md) — PHP, Go, Rust: what's the same and what differs
5. [Configuration](configuration.md) — the complete `dbox.yml` reference
6. [Commands](commands.md) — every CLI command and option
7. [Frameworks](frameworks.md) — supported frameworks, detection rules, scaffolding
8. [Web Servers](web-servers.md) — nginx, Apache, Caddy, OpenLiteSpeed (PHP runtime)
9. [Databases](databases.md) — engines, backup & restore
10. [Extensions](extensions.md) — the PHP extension manager
11. [Services](services.md) — Redis, Mailpit, phpMyAdmin, Meilisearch, Elasticsearch
12. [SSL / HTTPS](ssl.md) — local certificates
13. [Plugins](plugins.md) — writing a framework plugin
14. [Contributing](contributing.md) — dev setup, tests, conventions

## The 30-second version

```bash
# new project
dbox create laravel blog
cd blog
dbox start
# → http://localhost:8080

# existing project
git clone https://github.com/acme/shop && cd shop
dbox init      # detects framework, PHP version, extensions, services
dbox start
```

Two files describe your environment:

| File | Role |
|---|---|
| `dbox.yml` | The single source of truth. Edit it; commit it. |
| `.dbox/` | Generated Docker artifacts. Disposable — regenerated on every `start`. |

Everything else in this documentation expands on those ideas.
