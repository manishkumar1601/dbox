# Companion Services

Optional containers you can toggle on per project. Each is a boolean under
`services` in `phpbox.yml`, with a convenience command. Run `phpbox start`
after toggling to apply.

| Service | Enable | In-container host | Host URL / port (default) |
|---|---|---|---|
| Redis | `phpbox redis enable` | `redis:6379` | `localhost:6379` |
| Mailpit | `phpbox mail enable` | `mailpit:1025` (SMTP) | `http://localhost:8025` (UI) |
| phpMyAdmin | `phpbox phpmyadmin enable` | — | `http://localhost:8081` |
| Meilisearch | `phpbox search meilisearch` | `meilisearch:7700` | `http://localhost:7700` |
| Elasticsearch | `phpbox search elasticsearch` | `elasticsearch:9200` | `http://localhost:9200` |

Host ports are auto-selected to avoid collisions; the defaults above shift
upward if already in use.

## Redis

```bash
phpbox redis enable
phpbox start
```

Image `redis:7-alpine`. Configure your app with `REDIS_HOST=redis`,
`REDIS_PORT=6379` (already written to `.phpbox/env/.env`).

## Mailpit

A mail catcher — your app sends SMTP to `mailpit:1025` and you read messages in
the web UI.

```bash
phpbox mail enable
phpbox start
# → http://localhost:8025
```

App config: `MAIL_HOST=mailpit`, `MAIL_PORT=1025`.

## phpMyAdmin

Web UI for MySQL/MariaDB, pre-pointed at the `db` container (`PMA_HOST=db`).
Ignored for SQLite.

```bash
phpbox phpmyadmin enable
phpbox start
# → http://localhost:8081
```

## Meilisearch

```bash
phpbox search meilisearch
phpbox start
# → http://localhost:7700
```

App config: `MEILISEARCH_HOST=http://meilisearch:7700`.

## Elasticsearch

Single-node, security disabled (dev mode), `ES_JAVA_OPTS=-Xms512m -Xmx512m`.

```bash
phpbox search elasticsearch
phpbox start
# → http://localhost:9200
```

App config: `ELASTICSEARCH_HOST=http://elasticsearch:9200`. Recommended (and
auto-enabled) for Magento.

## Framework defaults

`phpbox init` / `phpbox create` enable a sensible set of services per framework:

| Framework | Auto-enabled |
|---|---|
| Laravel | Mailpit, phpMyAdmin |
| CodeIgniter 3 & 4 | Mailpit, phpMyAdmin |
| WordPress | Mailpit, phpMyAdmin |
| Core PHP | Mailpit, phpMyAdmin |
| Symfony | Mailpit, phpMyAdmin |
| Magento | Elasticsearch, phpMyAdmin |
| CakePHP, Yii, Slim, Laminas, Drupal, Joomla | (none) |

Redis is **off by default everywhere** — enable it per project with
`phpbox redis enable`. You can toggle any service afterwards.
