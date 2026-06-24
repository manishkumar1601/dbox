# Contributing

## Project layout

```
dbox/
├── pyproject.toml          packaging, dependencies, tool config
├── README.md  ·  LICENSE
├── src/
│   └── dbox/             the package (src-layout)
│       ├── cli.py          Typer CLI
│       ├── config.py       dbox.yml model
│       ├── detection.py    framework/PHP/extension inference
│       ├── generator.py    renders .dbox/ from the config
│       ├── engine.py       docker compose wrapper
│       ├── extensions.py   extension install metadata
│       ├── certs.py        TLS certificate generation
│       ├── ports.py        free-port detection
│       ├── doctor.py       health checks
│       ├── console.py      Rich output helpers
│       ├── plugins/        framework plugins + registry
│       └── templates/      Jinja2 templates
├── tests/                  pytest suite
└── docs/                   this documentation
```

The package uses **src-layout**: the importable code lives under `src/dbox/`,
which keeps test runs honest (they import the installed package, not the working
directory) and avoids the awkward `dbox/dbox/` nesting.

## Dev setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   Unix: source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

The suite (`tests/test_dbox.py`) covers detection, config round-trips,
extension resolution, generator output for every server/database combination,
SSL/LiteSpeed artifacts, and the Magento credential flow. It needs **no Docker**
— it validates the generated artifacts, not running containers.

> On legacy Windows terminals, prefix with `PYTHONUTF8=1` if you see encoding
> errors in CLI output during manual testing.

## Manual end-to-end check

```bash
mkdir /tmp/demo && cd /tmp/demo && echo "<?php phpinfo();" > index.php
dbox init
dbox start
curl http://localhost:8080
dbox down -v
```

## Coding conventions

* **Match the surrounding style.** Type hints, dataclasses for config, small
  focused modules.
* **The config is the source of truth.** New environment features should be a
  field in `dbox.yml` that the generator turns into an artifact — not
  imperative state hidden in the CLI.
* **Templates over string-building.** Generated files come from `templates/*.j2`.
* **Shell out to `docker compose`** via `engine.py` rather than adding a new
  Docker client.
* **Keep output cross-platform.** Use the helpers in `console.py`.

## Adding features

| To add… | Touch… |
|---|---|
| A framework | `plugins/<name>.py` + registry — see [plugins.md](plugins.md) |
| A language runtime | `config.py` (`SUPPORTED_RUNTIMES` + a new `<lang>Config`), a base plugin with `runtime="<lang>"`, `templates/<lang>/Dockerfile.j2`, a `{% if runtime == '<lang>' %}` block in `docker-compose.yml.j2`, dispatch in `generator.py`, and an entry in `engine.APP_SERVICE_BY_RUNTIME` |
| An extension | `extensions.py` (metadata) |
| A service | `templates/docker-compose.yml.j2`, `config.py` (`ServicesConfig`), `cli.py` toggle |
| A web server | `generator.py` (image + render), a template, `config.py` `SUPPORTED_SERVERS` |
| A config field | the relevant dataclass in `config.py`, then use it in `generator.py` / templates |

## Building a release binary

See [installation.md](installation.md#building-a-standalone-binary).

## Commit / PR notes

* Run `pytest` before pushing.
* Keep `dbox.yml` behaviour backward-compatible — `config.from_dict` tolerates
  missing keys via defaults, so additive fields are safe.
