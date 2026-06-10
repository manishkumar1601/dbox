# PHP Extensions

PHP extensions are baked into the PHP image at build time. Manage them with the
`ext` commands or by editing `php.extensions` in `phpbox.yml`.

```bash
phpbox ext list                 # show supported + enabled
phpbox ext install redis        # add + rebuild image
phpbox ext install xdebug
phpbox ext remove redis         # remove + rebuild
```

Each `install`/`remove` updates `phpbox.yml`, regenerates the Dockerfile, and
rebuilds the PHP image.

## How installation works

The generator groups requested extensions by install method and renders the
matching Dockerfile steps:

| Method | Mechanism | Examples |
|---|---|---|
| `core` | `docker-php-ext-install` (with `docker-php-ext-configure` when needed) | `gd`, `intl`, `zip`, `pdo_mysql`, `opcache` |
| `pecl` | `pecl install` + `docker-php-ext-enable` | `redis`, `imagick`, `mongodb`, `xdebug` |
| `builtin` | already in the base image — no action | `curl` |

Required system packages (Debian `apt`) are resolved automatically — e.g.
`gd` pulls in `libfreetype6-dev`/`libjpeg62-turbo-dev`/`libpng-dev`, `intl`
pulls `libicu-dev`, `imagick` pulls `libmagickwand-dev`.

## Extensions with first-class metadata

| Extension | Method | System packages |
|---|---|---|
| `gd` | core | libfreetype6-dev, libjpeg62-turbo-dev, libpng-dev |
| `intl` | core | libicu-dev |
| `zip` | core | libzip-dev |
| `soap` | core | libxml2-dev |
| `ldap` | core | libldap2-dev |
| `xml` | core | libxml2-dev |
| `xsl` | core | libxslt1-dev |
| `mbstring` | core | libonig-dev |
| `sodium` | core | libsodium-dev |
| `pdo_pgsql` / `pgsql` | core | libpq-dev |
| `bcmath`, `exif`, `sockets`, `opcache`, `pdo_mysql` | core | — |
| `curl` | builtin | — |
| `redis` | pecl | — |
| `imagick` | pecl | libmagickwand-dev |
| `mongodb` | pecl | — |
| `xdebug` | pecl | — |

## Other official extensions

Any extension name not in the table above is treated as a `core` install and
passed to `docker-php-ext-install`. If the base image can't build it, the
Docker build fails loudly (rather than silently dropping it) so you know to
adjust. In practice this means **all official PHP extensions** are reachable —
the table just captures the common ones with their system-package needs.

## Defaults

New projects start with `gd`, `zip`, `intl`, `pdo_mysql`, `opcache`. Framework
detection adds more (e.g. Laravel adds `bcmath`, `exif`, `redis`; Magento adds
`soap`, `xsl`, `sodium`, `mbstring`, …). Anything in `composer.json` as `ext-*`
is picked up by `phpbox init` too.

## Xdebug

```bash
phpbox ext install xdebug
phpbox start
```

Then add Xdebug settings under `php.ini` in `phpbox.yml`, e.g.:

```yaml
php:
  ini:
    xdebug.mode: debug
    xdebug.client_host: host.docker.internal
    xdebug.start_with_request: "yes"
```
