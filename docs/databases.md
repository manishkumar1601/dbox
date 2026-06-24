# Databases

Switch with `dbox db <engine>` (then `dbox start`), or set `database.engine`
in `dbox.yml`.

| Engine | Image | Default version | Container port | Data dir |
|---|---|---|---|---|
| `mariadb` (default) | `mariadb:<ver>` | `11` | 3306 | `.dbox/data/mariadb` |
| `mysql` | `mysql:<ver>` | `8.4` | 3306 | `.dbox/data/mysql` |
| `postgres` | `postgres:<ver>` | `16` | 5432 | `.dbox/data/postgres` |
| `sqlite` | — (no container) | — | — | your project files |

`dbox db postgres` also sets a sensible default `version`; you can override it
in `dbox.yml`.

## Connecting from your app

Inside the containers the database is reachable at host **`db`**.

For **Laravel, Symfony, CakePHP, and CodeIgniter 4**, DBox **auto-configures
the connection** — it injects the right environment variables into the app
container (`DB_*` for Laravel, `DATABASE_URL` for Symfony/CakePHP,
`database.default.*` for CodeIgniter 4), so a freshly created project connects
with **no manual config**. DBox also waits for the database to be *healthy*
before the app starts, so you won't hit "connection refused" on first boot.

The same values are written to `.dbox/env/.env` for reference (and for
frameworks that aren't auto-wired, like WordPress, which uses its install
wizard — enter host `db`):

```env
DB_CONNECTION=mysql      # or pgsql for postgres
DB_HOST=db
DB_PORT=3306             # 5432 for postgres
DB_DATABASE=blog
DB_USERNAME=blog
DB_PASSWORD=blog
```

From the **host** (e.g. a GUI client), connect to `localhost` on the mapped
`ports.database` (auto-selected; default 3306, or 3307+ if taken).

## Credentials

`dbox create`/`init` set the database name, user, and password all to the
**project name**, plus a `root` / `root` admin login:

```yaml
database:
  engine: mariadb
  version: "11"
  name: blog            # = project name
  user: blog            # = project name
  password: blog        # = project name
  root_password: root   # admin login is root / root
```

So for a project `blog` you can connect as **`blog` / `blog`** (normal use) or
**`root` / `root`** (admin: create/drop databases). `root_password` is also used
by `db:backup` to run `mysqldump` as root.

> **MySQL/MariaDB note:** those engines auto-create `root`, so if you set the
> `user` to `root` DBox won't try to re-create it — it just applies the root
> password. Postgres creates whatever `user` you specify (including `root`).

## phpMyAdmin

phpMyAdmin is **enabled by default** for Laravel, CodeIgniter, WordPress, and
Core PHP (and you can enable it anywhere):

```bash
dbox phpmyadmin enable
dbox start
# → http://localhost:8081  (PMA_HOST=db is configured automatically)
```

Log in with your project credentials (`blog` / `blog`) or `root` / `root`.
phpMyAdmin is ignored when the engine is SQLite.

## Backup & restore

```bash
dbox db:backup
# ✓ Saved .dbox/backups/blog-20260610-143000.sql
```

* MySQL/MariaDB → `mysqldump -u root -p<root_password> <name>`
* PostgreSQL → `pg_dump -U <user> <name>`

Restore from a dump (a bare filename resolves against `.dbox/backups/`):

```bash
dbox db:restore blog-20260610-143000.sql
```

Backups require the `db` container to be running.

## SQLite

SQLite needs no container — point your app at a file inside the project (e.g.
`database/database.sqlite`). DBox omits the `db` service and disables
phpMyAdmin automatically.

## Persistence & resetting

Database files live in `.dbox/data/<engine>/` (git-ignored). To wipe a
database completely:

```bash
dbox down -v        # removes containers + volumes
# or delete .dbox/data/<engine>/
```
