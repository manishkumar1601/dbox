# SSL / HTTPS

DBox can serve any project over HTTPS locally, with certificates generated
automatically — no host tooling required.

```bash
dbox ssl enable
dbox start
# ✓ Certificate ready (self-signed).
# ✓ App:        https://localhost:8443
```

Disable with `dbox ssl disable`.

## How certificates are generated

On the first `dbox start` after enabling SSL (when no cert exists yet), DBox
creates `cert.pem` + `key.pem` in `.dbox/certs/` using, in order of preference:

1. **mkcert** — if [`mkcert`](https://github.com/FiloSottile/mkcert) is on your
   PATH, DBox runs `mkcert -install` and issues a certificate for `localhost`,
   `127.0.0.1`, `::1`, and your configured `ssl.host`. These are **trusted by
   your browser** (no warning).
2. **Self-signed (fallback)** — otherwise DBox generates a self-signed
   certificate *inside the PHP container* using PHP's built-in OpenSSL. This
   needs no host tooling and works identically on Windows, macOS, and Linux, but
   browsers will show the usual "not trusted" warning you can click through for
   local dev.

For a frictionless trusted experience, install mkcert once and re-run
`dbox ssl enable && dbox start` (delete `.dbox/certs/` first to force
regeneration).

## Configuration

```yaml
ssl:
  enabled: true
  host: app.localhost      # common name for the generated cert
ports:
  https: 8443              # host port for HTTPS (auto-adjusted if taken)
```

## Per-server wiring

The certificate is mounted at `/etc/dbox/certs/` and referenced by each server:

| Server | HTTPS wiring |
|---|---|
| nginx | a `listen 443 ssl;` block with `ssl_certificate` / `ssl_certificate_key`, plus `fastcgi_param HTTPS on` |
| Caddy | a `:443` site block with `tls /etc/dbox/certs/cert.pem /etc/dbox/certs/key.pem` |
| Apache | a generated `:443` vhost (`.dbox/apache/ssl.conf`) with `mod_ssl` enabled |
| OpenLiteSpeed | a secure `listener` with `keyFile` / `certFile` |

HTTP on `ports.http` keeps working alongside HTTPS.

## Regenerating / trusting

* Delete `.dbox/certs/` and run `dbox start` to regenerate.
* Self-signed certs are valid for ~825 days.
* To trust a self-signed cert system-wide, import `.dbox/certs/cert.pem` into
  your OS/browser trust store — or just use mkcert, which does this for you.
