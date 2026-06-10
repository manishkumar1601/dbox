# Installation

> **New to PHPBox on a brand-new machine?** Jump to
> [First-time setup on a fresh PC](#first-time-setup-on-a-fresh-pc) for a
> complete, copy-paste walkthrough. The sections below are the reference detail.

## First-time setup on a fresh PC

The install script **bootstraps its own prerequisites** — if Python or Docker
are missing, it installs them for you (via `winget` on Windows, Homebrew/apt on
macOS/Linux). So a fresh machine is essentially: *clone → run the script*.

### Step 1 — Clone and run the install script

```powershell
# Windows (PowerShell)
git clone https://github.com/your-org/phpbox
cd phpbox
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

```bash
# macOS / Linux
git clone https://github.com/your-org/phpbox
cd phpbox
./scripts/install.sh
```

The script will, in order:

1. **Ensure Python 3.12+** — required to run the PHPBox CLI. Installed
   automatically if missing (`winget install Python.Python.3.12` / `brew` /
   apt-dnf-pacman). The script then refreshes PATH and continues.
2. **Install PHPBox** — a global, isolated install via
   [pipx](https://pipx.pypa.io/) (set up for you if needed), so `phpbox` works
   in **any folder**. The install is *non-editable*, so the clone is disposable.
3. **Ensure Docker** — required only when you *run* a project. Installed
   automatically if missing (`winget install Docker.DockerDesktop` /
   `brew install --cask docker` / Docker's official Linux script).

> ⚠️ **Docker Desktop needs a reboot + first launch.** No installer can start
> the Docker engine for you: after Docker Desktop is installed you must
> **reboot, then open Docker Desktop once** (accept the license) and wait until
> it says *running*. The script will remind you. This is only needed before your
> first `phpbox start` — installing PHPBox itself doesn't require Docker.

> **Don't want auto-install of Python/Docker?** Pass `-SkipDeps`
> (`scripts\install.ps1 -SkipDeps`) or `--skip-deps`
> (`./scripts/install.sh --skip-deps`) to install only PHPBox.
>
> **Prefer `pip` over `pipx`?** Pass `-Pip` / `--pip`.

### Step 2 — Open a new terminal and verify

```powershell
phpbox --help
phpbox doctor      # confirms Docker is installed and running
```

> A **new** terminal is required so the updated PATH (from pipx / a fresh Python
> install) is picked up.

You no longer need the clone:

```powershell
cd ..
Remove-Item -Recurse -Force phpbox      # macOS/Linux: rm -rf phpbox
```

### Step 3 — Create a new project **or** run an existing one

**New project:**

```powershell
cd C:\Users\<you>\projects
phpbox create laravel blog       # also: corephp, wordpress, symfony, codeigniter, …
cd blog
phpbox start
# → http://localhost:8080
```

**Existing project (clone a repo and go):**

```powershell
git clone https://github.com/acme/shop
cd shop
phpbox init        # auto-detects framework, PHP version, extensions, database
phpbox start
```

### Everyday commands

```powershell
phpbox stop          # stop containers (data is kept)
phpbox logs -f       # tail logs
phpbox shell         # open a shell inside the PHP container
phpbox down          # remove containers + network
phpbox down -v       # …and delete the database volume
```

> The **first** `phpbox start` for a project downloads images and builds the PHP
> image — this takes a few minutes. Every start after that is fast.

See [getting-started.md](getting-started.md) for the full workflow and
[commands.md](commands.md) for every command.

---

## Requirements

| Dependency | Notes |
|---|---|
| **Docker** | Docker Desktop (Windows / macOS) or Docker Engine + the Compose v2 plugin (Linux). This is the only runtime requirement for the containers themselves. |
| **Python 3.12+** | Needed only to run the PHPBox CLI. End users who get the standalone binary don't need Python at all. |

Verify Docker is working before you start:

```bash
docker --version
docker compose version
docker info          # must succeed — the daemon has to be running
```

PHPBox's `phpbox doctor` will also check all of this for you.

## Install from source (editable)

```bash
git clone https://github.com/your-org/phpbox
cd phpbox
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -e .
phpbox --help
```

The `-e` (editable) install means changes to the source are picked up
immediately — ideal for development.

## Install with dev tools

```bash
pip install -e ".[dev]"     # adds pytest and pyinstaller
pytest                      # run the test suite
```

## Run without installing

From the repository root you can always run the module directly:

```bash
python -m phpbox --help
```

> On Windows terminals using a legacy code page, set `PYTHONUTF8=1` (or run in
> Windows Terminal) so the status glyphs render. PHPBox forces UTF-8 on its
> output streams, but the environment variable removes any ambiguity.

## Building a standalone binary

PHPBox ships as a single executable via [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --onefile --name phpbox \
    --add-data "src/phpbox/templates:phpbox/templates" \
    src/phpbox/__main__.py
```

Output:

| Platform | Artifact |
|---|---|
| Windows | `dist/phpbox.exe` |
| Linux | `dist/phpbox` |
| macOS | `dist/phpbox` |

> The `--add-data` flag bundles the Jinja2 templates into the binary. The path
> separator is `:` on Linux/macOS and `;` on Windows
> (`--add-data "src/phpbox/templates;phpbox/templates"`).

## Uninstall

The easiest way — works from anywhere, figures out pipx vs pip for you:

```bash
phpbox uninstall          # add -y to skip the confirmation
```

> On Windows the removal finishes a moment after the command exits (a running
> program can't delete its own files), so open a new terminal to confirm.

Alternatively, run the uninstall script (handy if the `phpbox` command itself is
broken — but you need the clone for this):

```bash
# Linux / macOS
./scripts/uninstall.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1
```

Or remove it directly:

```bash
pipx uninstall phpbox     # if installed with pipx
pip uninstall phpbox      # if installed with pip
```

Uninstalling does **not** touch your projects. Per-project containers and data
are removed separately, from inside each project:

```bash
phpbox down -v            # removes containers + the database volume
```
