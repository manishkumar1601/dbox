# Command Reference

Run `dbox --help` or `dbox <command> --help` at any time. Commands that read
a project locate it by walking up from the current directory to find
`dbox.yml`.

## Environment lifecycle

### `dbox init [--force]`
Detect the current project and generate `dbox.yml` + `.dbox/`.
`--force` overwrites an existing `dbox.yml`.

### `dbox create <framework> <name>`
Scaffold a new project in `./<name>`: writes config, builds the PHP image, runs
the framework's scaffolding, and starts the stack.
See [frameworks.md](frameworks.md) for valid `<framework>` values.

### `dbox start [--build | --no-build]`
Regenerate `.dbox/` and start the containers. Builds images first by default
(`--no-build` skips the rebuild). Before launching it **re-checks ports** and
shifts any that are now occupied to the next free one, and generates a TLS
certificate if SSL is enabled and none exists. Waits for the database to be
healthy, then prints a summary with service URLs **and** the database
credentials (host, name, username, password, root login, connection string).

### `dbox stop`
Stop containers, preserving them and their data.

### `dbox restart`
Restart the running containers.

### `dbox down [-v | --volumes]`
Remove containers and the network. `-v` also removes named volumes.

### `dbox logs [--follow/-f] [service]`
Show container logs, optionally for a single service (`php`, `web`, `db`, …).

### `dbox shell [service]`
Open an interactive shell (`bash`, falling back to `sh`) inside a container.
Defaults to the `php` service.

## Inspection

### `dbox detect`
Report the framework, PHP version, required extensions, and recommended
services DBox would configure — without writing anything.

### `dbox doctor`
Run health checks: Docker installed, daemon running, `dbox.yml` present,
framework detected, PHP version supported, containers running, database/Redis
services up, recommended extensions present, SSL configured.

### `dbox version`
Print the installed DBox version (and note if a newer one is available).

### `dbox update`
Update DBox to the latest version from GitHub (same source the installer
uses). Detects whether you installed via pipx or pip. DBox checks GitHub for
new versions in the background (at most once a day) and prints a one-line notice
on commands when an update is available; this command applies it.

> On Windows the update finishes a moment after the command exits (a running
> program can't replace its own files) — open a new terminal to use the new
> version.

### `dbox uninstall [--yes | -y]`
Remove DBox from your system. It detects how DBox was installed (pipx or
pip) and runs the matching uninstall; `-y` skips the confirmation prompt. Your
projects and their `.dbox/` folders are left untouched.

> On Windows the running program can't delete its own files, so the removal is
> handed to a short detached helper that completes a second or two after the
> command exits — open a new terminal to confirm `dbox` is gone. (The
> `scripts/uninstall.*` scripts remain available too, e.g. if the `dbox`
> command itself is broken.)

## Runtime versions

### `dbox php use <version>`
Switch the PHP version (`7.4`–`8.4`) and rebuild the PHP image.

### `dbox composer use <version>`
Pin Composer to a version (e.g. `2.8`, `latest`) and rebuild.

### `dbox composer <args…>`
Run Composer inside the container, e.g. `dbox composer require monolog/monolog`.

## Web server & database

### `dbox server <nginx|apache|litespeed|caddy>`
Switch the web server. Run `dbox start` to apply. See [web-servers.md](web-servers.md).

### `dbox db <mariadb|mysql|postgres|sqlite>`
Switch the database engine (also sets a sensible default version). Run
`dbox start` to apply. See [databases.md](databases.md).

## Extensions

### `dbox ext list`
List supported extensions, marking the ones currently enabled.

### `dbox ext install <name>`
Add an extension to `php.extensions` and rebuild the image.

### `dbox ext remove <name>`
Remove an extension and rebuild.

See [extensions.md](extensions.md).

## Companion services

| Command | Effect |
|---|---|
| `dbox redis enable` / `disable` | Toggle Redis |
| `dbox mail enable` / `disable` | Toggle Mailpit |
| `dbox phpmyadmin enable` / `disable` | Toggle phpMyAdmin |
| `dbox search meilisearch` | Enable Meilisearch |
| `dbox search elasticsearch` | Enable Elasticsearch |

Run `dbox start` afterwards to apply. See [services.md](services.md).

## SSL / HTTPS

### `dbox ssl <enable|disable>`
Toggle local HTTPS. On the next `dbox start`, a certificate is generated
automatically (mkcert if installed, otherwise self-signed). See [ssl.md](ssl.md).

## Database backup & restore

### `dbox db:backup`
Dump the database to `.dbox/backups/<name>-<timestamp>.sql`
(`mysqldump` or `pg_dump` depending on the engine).

### `dbox db:restore <file.sql>`
Restore from a dump. A bare filename resolves against `.dbox/backups/`.

## Portability

### `dbox export`
Package the project into `dbox-package.zip`, excluding `.git`, `node_modules`,
`vendor`, and the `.dbox/{data,backups,cache}` directories.

### `dbox import <file.zip>`
Unpack a package into the current directory. Follow with `dbox start`.

## Framework / language CLIs

Each runs the toolchain inside the app container (`php` service for PHP,
`app` service for Go/Rust):

| Command | Runs in container | Runtime |
|---|---|---|
| `dbox artisan <args…>` | `php artisan …` | PHP (Laravel) |
| `dbox spark <args…>` | `php spark …` | PHP (CodeIgniter 4) |
| `dbox wp <args…>` | `wp --allow-root …` | PHP (WordPress) |
| `dbox cake <args…>` | `bin/cake …` | PHP (CakePHP) |
| `dbox console <args…>` | `php bin/console …` | PHP (Symfony) |
| `dbox yii <args…>` | `php yii …` | PHP (Yii) |
| `dbox drush <args…>` | `vendor/bin/drush …` | PHP (Drupal) |
| `dbox magento <args…>` | `php bin/magento …` | PHP (Magento) |
| `dbox joomla <args…>` | `php cli/joomla.php …` | PHP (Joomla) |
| `dbox composer <args…>` | `composer …` | PHP |
| **`dbox go <args…>`** | `go …` (`go mod tidy`, `go test ./...`, …) | Go |
| **`dbox cargo <args…>`** | `cargo …` (`cargo build`, `cargo test`, …) | Rust |

Unknown flags are passed straight through (e.g. `dbox artisan migrate --force`).

> PHP-only commands (`dbox composer`, `dbox php use`, `dbox ext …`) refuse to
> run on Go/Rust projects with a clear error.
