# Writing a Framework Plugin

Adding support for a new framework means dropping one file into
`src/dbox/plugins/` and registering it. Plugins subclass `FrameworkPlugin`
(`src/dbox/plugins/base.py`).

## The interface

```python
from dbox.plugins.base import Credential, DetectionRule, FrameworkPlugin


class MyFrameworkPlugin(FrameworkPlugin):
    name = "myfw"               # used by `dbox create myfw <name>`
    label = "MyFramework"       # shown in output
    runtime = "php"             # "php" | "go" | "rust" (default "php")
    document_root = "/public"   # web root relative to the app root (PHP only)
    default_app_port = 8080     # container port the app listens on (Go/Rust)
    priority = 70               # higher wins when multiple plugins match

    detection = DetectionRule(
        files=("bin/myfw",),                 # ALL must exist
        any_files=("config/app.php",),       # at least ONE must exist
        composer=("vendor/myframework",),    # composer.json requires one of these
        # Go plugins: go_modules=("github.com/labstack/echo/v4",)
        # Rust plugins: cargo_crates=("actix-web",)
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "intl", "opcache"]    # PHP only

    def services(self) -> list[str]:
        return ["redis"]                     # auto-enabled on create/init

    def commands(self) -> dict[str, list[str]]:
        # Exposes `dbox myfw <args…>` → `php bin/myfw <args…>` in the container
        return {"myfw": ["php", "bin/myfw"]}

    def app_env(self, db) -> dict[str, str]:
        # Env vars injected into the app container (e.g. DB connection details).
        # Default returns {}; override to auto-wire your framework to the DB.
        return {"DB_HOST": "db", "DB_PORT": "3306", "DB_NAME": db.name}

    def create_steps(self, project_name: str) -> list[str] | None:
        # Shell commands run in the app container to scaffold a new project.
        # Steps are joined with newlines under `set -e`, so heredocs work.
        return [
            "composer create-project vendor/myframework-skeleton /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
        ]
```

### Detection semantics

A plugin matches if **any** of these holds:

* every path in `files` exists, **or**
* any path in `any_files` exists, **or**
* `composer.json` requires any package in `composer`, **or**
* `go.mod` requires any module in `go_modules` (Go plugins), **or**
* `Cargo.toml`'s `[dependencies]` lists any crate in `cargo_crates` (Rust plugins).

When several plugins match, the highest `priority` wins. Keep generic markers
(like a bare `public/index.php`) out of `any_files` — rely on the composer
package, go module, or cargo crate instead, or they'll over-match unrelated
projects.

### Optional hooks

| Method | Purpose | Default |
|---|---|---|
| `extensions()` | PHP extensions the framework needs (PHP only) | `[]` |
| `services()` | Companion services to auto-enable | `[]` |
| `commands()` | Map `dbox <cmd>` → in-container argv | `{}` |
| `app_env(db)` | Env vars injected into the app container (e.g. DB connection) | `{}` |
| `create_steps(name)` | Scaffolding shell commands | `None` (no scaffolding) |
| `create_credentials()` | Secrets to collect before scaffolding | `[]` |
| `create_env(creds)` | Turn collected secrets into container env vars | passthrough |
| `post_create_note()` | Guidance printed after `create` | `None` |

### Credentials (for authenticated scaffolding)

When scaffolding needs secrets (as Magento does), declare them:

```python
def create_credentials(self) -> list[Credential]:
    return [
        Credential("MYFW_TOKEN", "MyFramework API token", secret=True),
    ]

def create_env(self, credentials: dict[str, str]) -> dict[str, str]:
    # Returned dict is injected into the scaffolding container via `-e`.
    return {"COMPOSER_AUTH": build_auth(credentials["MYFW_TOKEN"])}
```

The CLI fills each `Credential` from its `env` variable if set, otherwise
prompts interactively (`hide_input=secret`).

## Registering the plugin

Add it to the registry in `src/dbox/plugins/__init__.py`:

```python
from dbox.plugins.myfw import MyFrameworkPlugin

_PLUGIN_CLASSES = [
    LaravelPlugin,
    # …
    MyFrameworkPlugin,
]
```

That's it — detection, `dbox create myfw`, the `dbox myfw` CLI, and doctor
checks all pick it up automatically.

## Pass-through commands

If you add a `commands()` mapping, also register a top-level pass-through in
`cli.py` (next to `artisan`, `spark`, etc.) so `dbox myfw …` forwards
arbitrary arguments into the container. Existing ones are a copy-paste template.

## Testing your plugin

Add cases to `tests/test_dbox.py`:

```python
def test_detect_myfw(tmp_path):
    _mk(tmp_path, {"bin/myfw": "<?php", "config/app.php": "<?php"})
    assert detection.detect(tmp_path).framework == "myfw"
```

Run `pytest`. See [contributing.md](contributing.md).
