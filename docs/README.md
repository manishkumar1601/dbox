# PHPBox Documentation

PHPBox is a cross-platform CLI that lets you create and run any PHP framework or
CMS using only Docker — no PHP, Composer, web server, or database installed on
the host.

## Contents

1. [Installation](installation.md) — requirements, install methods, standalone binary
2. [Getting Started](getting-started.md) — your first project (`create` and `init`)
3. [Architecture](architecture.md) — components, data flow, the generation pipeline
4. [Configuration](configuration.md) — the complete `phpbox.yml` reference
5. [Commands](commands.md) — every CLI command and option
6. [Frameworks](frameworks.md) — supported frameworks, detection rules, scaffolding
7. [Web Servers](web-servers.md) — nginx, Apache, Caddy, OpenLiteSpeed
8. [Databases](databases.md) — engines, backup & restore
9. [Extensions](extensions.md) — the PHP extension manager
10. [Services](services.md) — Redis, Mailpit, phpMyAdmin, Meilisearch, Elasticsearch
11. [SSL / HTTPS](ssl.md) — local certificates
12. [Plugins](plugins.md) — writing a framework plugin
13. [Contributing](contributing.md) — dev setup, tests, conventions

## The 30-second version

```bash
# new project
phpbox create laravel blog
cd blog
phpbox start
# → http://localhost:8080

# existing project
git clone https://github.com/acme/shop && cd shop
phpbox init      # detects framework, PHP version, extensions, services
phpbox start
```

Two files describe your environment:

| File | Role |
|---|---|
| `phpbox.yml` | The single source of truth. Edit it; commit it. |
| `.phpbox/` | Generated Docker artifacts. Disposable — regenerated on every `start`. |

Everything else in this documentation expands on those ideas.
