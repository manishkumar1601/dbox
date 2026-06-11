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

The generated `Dockerfile` installs every requested extension with
[`install-php-extensions`](https://github.com/mlocati/docker-php-extension-installer):

```dockerfile
COPY --from=mlocati/php-extension-installer:latest /usr/bin/install-php-extensions /usr/local/bin/
RUN install-php-extensions gd zip intl pdo_mysql opcache redis ...
```

This tool pulls **prebuilt binaries where available** and resolves the needed
system libraries (libicu, libpng, etc.) automatically — so builds are much
faster than compiling each extension from source, and there's no apt list to
maintain. It supports core, PECL, and bundled extensions alike (`gd`, `intl`,
`redis`, `imagick`, `xdebug`, `mysqli`, …).

## Extensions with first-class metadata

PHPBox keeps lightweight metadata for the common extensions (used by framework
defaults and the `ext list` view); any other valid extension name is passed
straight to `install-php-extensions`.

`gd`, `intl`, `zip`, `soap`, `ldap`, `xml`, `xsl`, `mbstring`, `sodium`,
`pdo_mysql`, `mysqli`, `pdo_pgsql`, `pgsql`, `bcmath`, `exif`, `sockets`,
`opcache`, `curl`, `redis`, `imagick`, `mongodb`, `xdebug`

## Other official extensions

Any extension name not listed above is still passed to `install-php-extensions`,
which supports the full catalogue of official PHP extensions. If it can't be
installed, the Docker build fails loudly (rather than silently dropping it) so
you know to adjust.

## Defaults

New projects start with `gd`, `zip`, `intl`, `pdo_mysql`, `opcache`. Each
framework adds what it needs (e.g. Laravel adds `bcmath`, `exif`; WordPress adds
`mysqli`, `imagick`; Magento adds `soap`, `xsl`, `sodium`, `mbstring`, …).
Anything in `composer.json` as `ext-*` is picked up by `phpbox init` too.

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
