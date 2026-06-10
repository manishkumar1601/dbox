# Databases

Switch with `phpbox db <engine>` (then `phpbox start`), or set `database.engine`
in `phpbox.yml`.

| Engine | Image | Default version | Container port | Data dir |
|---|---|---|---|---|
| `mariadb` (default) | `mariadb:<ver>` | `11` | 3306 | `.phpbox/data/mariadb` |
| `mysql` | `mysql:<ver>` | `8.4` | 3306 | `.phpbox/data/mysql` |
| `postgres` | `postgres:<ver>` | `16` | 5432 | `.phpbox/data/postgres` |
| `sqlite` | — (no container) | — | — | your project files |

`phpbox db postgres` also sets a sensible default `version`; you can override it
in `phpbox.yml`.

## Connecting from your app

Inside the containers the database is reachable at host **`db`**. PHPBox writes
the relevant values to `.phpbox/env/.env` for you to copy into your app's `.env`:

```env
DB_CONNECTION=mysql      # or pgsql for postgres
DB_HOST=db
DB_PORT=3306             # 5432 for postgres
DB_DATABASE=blog
DB_USERNAME=blog
DB_PASSWORD=secret
```

From the **host** (e.g. a GUI client), connect to `localhost` on the mapped
`ports.database` (auto-selected; default 3306, or 3307+ if taken).

## Credentials

Set under `database` in `phpbox.yml`:

```yaml
database:
  engine: mariadb
  version: "11"
  name: blog
  user: blog
  password: secret
  root_password: root
```

`root_password` is used by `db:backup` to run `mysqldump` as root.

## phpMyAdmin

For MySQL/MariaDB, enable a web UI:

```bash
phpbox phpmyadmin enable
phpbox start
# → http://localhost:8081  (PMA_HOST=db is configured automatically)
```

phpMyAdmin is ignored when the engine is SQLite.

## Backup & restore

```bash
phpbox db:backup
# ✓ Saved .phpbox/backups/blog-20260610-143000.sql
```

* MySQL/MariaDB → `mysqldump -u root -p<root_password> <name>`
* PostgreSQL → `pg_dump -U <user> <name>`

Restore from a dump (a bare filename resolves against `.phpbox/backups/`):

```bash
phpbox db:restore blog-20260610-143000.sql
```

Backups require the `db` container to be running.

## SQLite

SQLite needs no container — point your app at a file inside the project (e.g.
`database/database.sqlite`). PHPBox omits the `db` service and disables
phpMyAdmin automatically.

## Persistence & resetting

Database files live in `.phpbox/data/<engine>/` (git-ignored). To wipe a
database completely:

```bash
phpbox down -v        # removes containers + volumes
# or delete .phpbox/data/<engine>/
```
