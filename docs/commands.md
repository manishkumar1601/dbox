# Command Reference

Run `phpbox --help` or `phpbox <command> --help` at any time. Commands that read
a project locate it by walking up from the current directory to find
`phpbox.yml`.

## Environment lifecycle

### `phpbox init [--force]`
Detect the current project and generate `phpbox.yml` + `.phpbox/`.
`--force` overwrites an existing `phpbox.yml`.

### `phpbox create <framework> <name>`
Scaffold a new project in `./<name>`: writes config, builds the PHP image, runs
the framework's scaffolding, and starts the stack.
See [frameworks.md](frameworks.md) for valid `<framework>` values.

### `phpbox start [--build | --no-build]`
Regenerate `.phpbox/` and start the containers. Builds images first by default
(`--no-build` skips the rebuild). Generates a TLS certificate first if SSL is
enabled and none exists. Prints the resulting URLs.

### `phpbox stop`
Stop containers, preserving them and their data.

### `phpbox restart`
Restart the running containers.

### `phpbox down [-v | --volumes]`
Remove containers and the network. `-v` also removes named volumes.

### `phpbox logs [--follow/-f] [service]`
Show container logs, optionally for a single service (`php`, `web`, `db`, …).

### `phpbox shell [service]`
Open an interactive shell (`bash`, falling back to `sh`) inside a container.
Defaults to the `php` service.

## Inspection

### `phpbox detect`
Report the framework, PHP version, required extensions, and recommended
services PHPBox would configure — without writing anything.

### `phpbox doctor`
Run health checks: Docker installed, daemon running, `phpbox.yml` present,
framework detected, PHP version supported, containers running, database/Redis
services up, recommended extensions present, SSL configured.

### `phpbox version`
Print the PHPBox version.

### `phpbox uninstall [--yes | -y]`
Remove PHPBox from your system. It detects how PHPBox was installed (pipx or
pip) and runs the matching uninstall; `-y` skips the confirmation prompt. Your
projects and their `.phpbox/` folders are left untouched.

> On Windows the running program can't delete its own files, so the removal is
> handed to a short detached helper that completes a second or two after the
> command exits — open a new terminal to confirm `phpbox` is gone. (The
> `scripts/uninstall.*` scripts remain available too, e.g. if the `phpbox`
> command itself is broken.)

## Runtime versions

### `phpbox php use <version>`
Switch the PHP version (`7.4`–`8.4`) and rebuild the PHP image.

### `phpbox composer use <version>`
Pin Composer to a version (e.g. `2.8`, `latest`) and rebuild.

### `phpbox composer <args…>`
Run Composer inside the container, e.g. `phpbox composer require monolog/monolog`.

## Web server & database

### `phpbox server <nginx|apache|litespeed|caddy>`
Switch the web server. Run `phpbox start` to apply. See [web-servers.md](web-servers.md).

### `phpbox db <mariadb|mysql|postgres|sqlite>`
Switch the database engine (also sets a sensible default version). Run
`phpbox start` to apply. See [databases.md](databases.md).

## Extensions

### `phpbox ext list`
List supported extensions, marking the ones currently enabled.

### `phpbox ext install <name>`
Add an extension to `php.extensions` and rebuild the image.

### `phpbox ext remove <name>`
Remove an extension and rebuild.

See [extensions.md](extensions.md).

## Companion services

| Command | Effect |
|---|---|
| `phpbox redis enable` / `disable` | Toggle Redis |
| `phpbox mail enable` / `disable` | Toggle Mailpit |
| `phpbox phpmyadmin enable` / `disable` | Toggle phpMyAdmin |
| `phpbox search meilisearch` | Enable Meilisearch |
| `phpbox search elasticsearch` | Enable Elasticsearch |

Run `phpbox start` afterwards to apply. See [services.md](services.md).

## SSL / HTTPS

### `phpbox ssl <enable|disable>`
Toggle local HTTPS. On the next `phpbox start`, a certificate is generated
automatically (mkcert if installed, otherwise self-signed). See [ssl.md](ssl.md).

## Database backup & restore

### `phpbox db:backup`
Dump the database to `.phpbox/backups/<name>-<timestamp>.sql`
(`mysqldump` or `pg_dump` depending on the engine).

### `phpbox db:restore <file.sql>`
Restore from a dump. A bare filename resolves against `.phpbox/backups/`.

## Portability

### `phpbox export`
Package the project into `phpbox-package.zip`, excluding `.git`, `node_modules`,
`vendor`, and the `.phpbox/{data,backups,cache}` directories.

### `phpbox import <file.zip>`
Unpack a package into the current directory. Follow with `phpbox start`.

## Framework CLIs

Each runs the framework's native tool inside the PHP container:

| Command | Runs in container |
|---|---|
| `phpbox artisan <args…>` | `php artisan …` (Laravel) |
| `phpbox spark <args…>` | `php spark …` (CodeIgniter 4) |
| `phpbox wp <args…>` | `wp --allow-root …` (WordPress) |
| `phpbox cake <args…>` | `bin/cake …` (CakePHP) |
| `phpbox console <args…>` | `php bin/console …` (Symfony) |
| `phpbox yii <args…>` | `php yii …` (Yii) |
| `phpbox drush <args…>` | `vendor/bin/drush …` (Drupal) |
| `phpbox magento <args…>` | `php bin/magento …` (Magento) |
| `phpbox joomla <args…>` | `php cli/joomla.php …` (Joomla) |

Unknown flags are passed straight through (e.g. `phpbox artisan migrate --force`).
