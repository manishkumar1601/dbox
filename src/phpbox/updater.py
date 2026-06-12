"""Version checking and self-update against the GitHub repository.

The update check is *throttled* and *non-blocking*: each command reads a small
cache file (instant) to decide whether to show an "update available" notice, and
refreshes that cache in a background thread at most once a day. The actual
network call never blocks the command you ran.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.request
from pathlib import Path

from phpbox import __version__

REPO = "manishkumar1601/phpbox"
BRANCH = "master"

# Source used to install/update — GitHub's source tarball, so neither `git`
# nor a manual clone is required on the user's machine.
INSTALL_SPEC = f"https://github.com/{REPO}/archive/refs/heads/{BRANCH}.tar.gz"

_VERSION_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/src/phpbox/__init__.py"
_CACHE = Path.home() / ".phpbox" / "update-check.json"
_TTL_SECONDS = 24 * 60 * 60  # check GitHub at most once per day


def current_version() -> str:
    return __version__


# ---- version comparison -------------------------------------------------


def _version_tuple(v: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", v or "")
    return tuple(int(n) for n in nums) or (0,)


def is_newer(latest: str, current: str) -> bool:
    return _version_tuple(latest) > _version_tuple(current)


def _parse_version(text: str) -> str | None:
    m = re.search(r"""__version__\s*=\s*["']([^"']+)["']""", text)
    return m.group(1) if m else None


# ---- network + cache ----------------------------------------------------


def fetch_latest_version(timeout: float = 4.0) -> str | None:
    """Fetch the version declared on the GitHub default branch (or None)."""
    try:
        req = urllib.request.Request(_VERSION_URL, headers={"User-Agent": "phpbox"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return _parse_version(resp.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _read_cache() -> dict:
    try:
        return json.loads(_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cache(data: dict) -> None:
    try:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def clear_cache() -> None:
    try:
        _CACHE.unlink(missing_ok=True)
    except Exception:
        pass


def cached_latest() -> str | None:
    """The latest version from the cache, but only if it's newer than what's
    installed. Instant (no network)."""
    latest = _read_cache().get("latest")
    if latest and is_newer(latest, current_version()):
        return latest
    return None


def _refresh() -> None:
    latest = fetch_latest_version()
    data = _read_cache()
    data["checked"] = time.time()
    if latest:
        data["latest"] = latest
    _write_cache(data)


def maybe_refresh_async() -> None:
    """If the cache is stale, refresh it in a daemon thread (never blocks)."""
    if time.time() - _read_cache().get("checked", 0) < _TTL_SECONDS:
        return
    try:
        threading.Thread(target=_refresh, daemon=True).start()
    except Exception:
        pass
