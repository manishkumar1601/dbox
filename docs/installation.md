# Installation

> **New to DBox on a brand-new machine?** Jump to
> [First-time setup on a fresh PC](#first-time-setup-on-a-fresh-pc) for a
> complete, copy-paste walkthrough. The sections below are the reference detail.

## First-time setup on a fresh PC

One command installs the **latest DBox from GitHub** — no clone needed — and
**bootstraps its own prerequisites**: if Python or Docker are missing it
installs them for you (via `winget` on Windows, Homebrew/apt on macOS/Linux).

### Step 1 — Run the one-line installer

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/manishkumar1601/dbox/master/scripts/install.ps1 | iex
```

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/manishkumar1601/dbox/master/scripts/install.sh | bash
```

The installer will, in order:

1. **Ensure Python 3.12+** — required to run the DBox CLI. Installed
   automatically if missing (`winget install Python.Python.3.12` / `brew` /
   apt-dnf-pacman), then refreshes PATH and continues.
2. **Install DBox** — a global, isolated install via
   [pipx](https://pipx.pypa.io/) (set up for you if needed), pulled from the
   GitHub source tarball, so `dbox` works in **any folder**.
3. **Ensure Docker** — required only when you *run* a project. Installed
   automatically if missing (`winget install Docker.DockerDesktop` /
   `brew install --cask docker` / Docker's official Linux script).

> ⚠️ **Docker Desktop needs a reboot + first launch.** No installer can start
> the Docker engine for you: after Docker Desktop is installed you must
> **reboot, then open Docker Desktop once** (accept the license) and wait until
> it says *running*. The installer will remind you. This is only needed before
> your first `dbox start` — installing DBox itself doesn't require Docker.

> **Running the script as a file** (e.g. from a clone) instead of piping it? You
> can pass flags: `--skip-deps` (`-SkipDeps`) to skip installing Python/Docker,
> or `--pip` (`-Pip`) to use `pip` instead of `pipx`.

### Step 2 — Open a new terminal and verify

```powershell
dbox --help
dbox doctor      # confirms Docker is installed and running
```

> A **new** terminal is required so the updated PATH (from pipx / a fresh Python
> install) is picked up.

### Step 3 — Create a new project **or** run an existing one

**New project:**

```powershell
cd C:\Users\<you>\projects
dbox create laravel blog       # also: corephp, wordpress, symfony, codeigniter, …
cd blog
dbox start
# → http://localhost:8080
```

**Existing project (clone a repo and go):**

```powershell
git clone https://github.com/acme/shop
cd shop
dbox init        # auto-detects framework, PHP version, extensions, database
dbox start
```

### Everyday commands

```powershell
dbox stop          # stop containers (data is kept)
dbox logs -f       # tail logs
dbox shell         # open a shell inside the PHP container
dbox down          # remove containers + network
dbox down -v       # …and delete the database volume
```

> The **first** `dbox start` for a project downloads images and builds the PHP
> image — this takes a few minutes. Every start after that is fast.

See [getting-started.md](getting-started.md) for the full workflow and
[commands.md](commands.md) for every command.

---

## Requirements

| Dependency | Notes |
|---|---|
| **Docker** | Docker Desktop (Windows / macOS) or Docker Engine + the Compose v2 plugin (Linux). This is the only runtime requirement for the containers themselves. |
| **Python 3.12+** | Needed only to run the DBox CLI. End users who get the standalone binary don't need Python at all. |

Verify Docker is working before you start:

```bash
docker --version
docker compose version
docker info          # must succeed — the daemon has to be running
```

DBox's `dbox doctor` will also check all of this for you.

## Install from source (editable)

```bash
git clone https://github.com/manishkumar1601/dbox
cd dbox
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -e .
dbox --help
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
python -m dbox --help
```

> On Windows terminals using a legacy code page, set `PYTHONUTF8=1` (or run in
> Windows Terminal) so the status glyphs render. DBox forces UTF-8 on its
> output streams, but the environment variable removes any ambiguity.

## Building a standalone binary

DBox ships as a single executable via [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --onefile --name dbox \
    --add-data "src/dbox/templates:dbox/templates" \
    src/dbox/__main__.py
```

Output:

| Platform | Artifact |
|---|---|
| Windows | `dist/dbox.exe` |
| Linux | `dist/dbox` |
| macOS | `dist/dbox` |

> The `--add-data` flag bundles the Jinja2 templates into the binary. The path
> separator is `:` on Linux/macOS and `;` on Windows
> (`--add-data "src/dbox/templates;dbox/templates"`).

## Updating

DBox checks GitHub for new versions in the background (at most once a day) and
shows a one-line notice on commands when an update is available. Apply it with:

```bash
dbox update
```

This reinstalls the latest from GitHub using the same method you installed with
(pipx or pip). On Windows the update completes a moment after the command exits
(a running program can't replace its own files) — open a new terminal to use the
new version. Check what you're on with `dbox version`.

> **Versioning:** the installed version is `dbox.__version__`; the update
> check compares it against the version on the `master` branch. Bump
> `__version__` (in `src/dbox/__init__.py` and `pyproject.toml`) when you cut a
> release so users are notified.

## Uninstall

The easiest way — works from anywhere, figures out pipx vs pip for you:

```bash
dbox uninstall          # add -y to skip the confirmation
```

> On Windows the removal finishes a moment after the command exits (a running
> program can't delete its own files), so open a new terminal to confirm.

Alternatively, run the uninstall script (handy if the `dbox` command itself is
broken — but you need the clone for this):

```bash
# Linux / macOS
./scripts/uninstall.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1
```

Or remove it directly:

```bash
pipx uninstall dbox     # if installed with pipx
pip uninstall dbox      # if installed with pip
```

Uninstalling does **not** touch your projects. Per-project containers and data
are removed separately, from inside each project:

```bash
dbox down -v            # removes containers + the database volume
```
