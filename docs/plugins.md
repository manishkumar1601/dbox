# Writing a Framework Plugin

Adding support for a new framework means dropping one file into
`src/phpbox/plugins/` and registering it. Plugins subclass `FrameworkPlugin`
(`src/phpbox/plugins/base.py`).

## The interface

```python
from phpbox.plugins.base import Credential, DetectionRule, FrameworkPlugin


class MyFrameworkPlugin(FrameworkPlugin):
    name = "myfw"               # used by `phpbox create myfw <name>`
    label = "MyFramework"       # shown in output
    document_root = "/public"   # web root relative to the app root
    priority = 70               # higher wins when multiple plugins match

    detection = DetectionRule(
        files=("bin/myfw",),                 # ALL must exist
        any_files=("config/app.php",),       # at least ONE must exist
        composer=("vendor/myframework",),    # composer.json requires one of these
    )

    def extensions(self) -> list[str]:
        return ["pdo_mysql", "intl", "opcache"]

    def services(self) -> list[str]:
        return ["redis"]                     # auto-enabled on create/init

    def commands(self) -> dict[str, list[str]]:
        # Exposes `phpbox myfw <args…>` → `php bin/myfw <args…>` in the container
        return {"myfw": ["php", "bin/myfw"]}

    def create_steps(self, project_name: str) -> list[str] | None:
        # Shell commands run in the PHP container to scaffold a new project.
        # Use the /tmp + copy pattern so create-project can target an empty dir.
        return [
            "composer create-project vendor/myframework-skeleton /tmp/app --no-interaction",
            "cp -a /tmp/app/. /var/www/html/ && rm -rf /tmp/app",
        ]
```

### Detection semantics

A plugin matches if **any** of these holds:

* every path in `files` exists, **or**
* any path in `any_files` exists, **or**
* `composer.json` requires any package in `composer`.

When several plugins match, the highest `priority` wins. Keep generic markers
(like a bare `public/index.php`) out of `any_files` — rely on the composer
package instead, or they'll over-match unrelated projects.

### Optional hooks

| Method | Purpose | Default |
|---|---|---|
| `extensions()` | PHP extensions the framework needs | `[]` |
| `services()` | Companion services to auto-enable | `[]` |
| `commands()` | Map `phpbox <cmd>` → in-container argv | `{}` |
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

Add it to the registry in `src/phpbox/plugins/__init__.py`:

```python
from phpbox.plugins.myfw import MyFrameworkPlugin

_PLUGIN_CLASSES = [
    LaravelPlugin,
    # …
    MyFrameworkPlugin,
]
```

That's it — detection, `phpbox create myfw`, the `phpbox myfw` CLI, and doctor
checks all pick it up automatically.

## Pass-through commands

If you add a `commands()` mapping, also register a top-level pass-through in
`cli.py` (next to `artisan`, `spark`, etc.) so `phpbox myfw …` forwards
arbitrary arguments into the container. Existing ones are a copy-paste template.

## Testing your plugin

Add cases to `tests/test_phpbox.py`:

```python
def test_detect_myfw(tmp_path):
    _mk(tmp_path, {"bin/myfw": "<?php", "config/app.php": "<?php"})
    assert detection.detect(tmp_path).framework == "myfw"
```

Run `pytest`. See [contributing.md](contributing.md).
