# Web Servers

Switch with `phpbox server <type>` (then `phpbox start`), or set `server.type`
in `phpbox.yml`. Four servers are supported.

| Type | Image | Topology | PHP link |
|---|---|---|---|
| `nginx` (default) | `nginx:alpine` | separate `web` container | FastCGI → `php:9000` |
| `caddy` | `caddy:alpine` | separate `web` container | FastCGI → `php:9000` |
| `litespeed` | `litespeedtech/openlitespeed` | separate `web` container | external FastCGI → `php:9000` |
| `apache` | `php:<ver>-apache` | **combined** with `php` (mod_php) | in-process |

## nginx

The default. A `nginx:alpine` container serves static files and proxies `.php`
to the PHP-FPM container. Config is generated at `.phpbox/nginx/default.conf`
with the document root, a `try_files … /index.php?$query_string` front-controller
rule, and (when SSL is on) a `listen 443 ssl` block.

## Caddy

`caddy:alpine` with the one-line `php_fastcgi php:9000` directive. When SSL is
enabled, a `:443` site block points at the generated cert/key. Config lives at
`.phpbox/caddy/Caddyfile`.

## Apache

Apache is special: instead of a separate web container, the PHP image is built
`FROM php:<ver>-apache` (mod_php), so Apache and PHP run together in the `php`
container. PHPBox enables `mod_rewrite` and `mod_ssl`, sets the `DocumentRoot`,
and allows `.htaccess` overrides. This is the most reliable Apache setup and
avoids brittle FastCGI proxy configuration. When SSL is enabled, a `:443` vhost
is generated at `.phpbox/apache/ssl.conf` and mounted into the container.

## OpenLiteSpeed

`litespeedtech/openlitespeed` runs as a separate `web` container and connects to
the PHP-FPM container over FastCGI. PHPBox generates two configs:

* `.phpbox/litespeed/httpd_config.conf` — server config: the listener(s), the
  external FastCGI processor, and the script handler mapping `.php`.
* `.phpbox/litespeed/vhconf.conf` — the virtual host: document root, index
  files, and a front-controller rewrite.

> **Implementation note.** Because PHP-FPM runs in a *separate* container,
> OpenLiteSpeed must not try to launch it. The external processor is declared
> with `autoStart 0` and a placeholder `path`; without this, OLS drops the PHP
> handler and serves `.php` as a static file, returning **403 Forbidden**. This
> is handled for you — it's documented here only so the generated config makes
> sense if you read it.

## SSL across servers

All four servers support HTTPS via `phpbox ssl enable`. Certificates are
generated automatically and mounted at `/etc/phpbox/certs/` (nginx, Caddy,
LiteSpeed) or referenced by the Apache vhost. See [ssl.md](ssl.md).

## Choosing

* **nginx** — the safe default; fast, well understood.
* **Caddy** — simplest config; great if you like its philosophy.
* **Apache** — choose when your app depends on `.htaccess` / mod_php behaviour.
* **OpenLiteSpeed** — when you want to mirror a LiteSpeed production host.
