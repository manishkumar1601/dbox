"""Plugin registry — discovery and lookup of framework plugins."""

from __future__ import annotations

from pathlib import Path

from dbox.plugins.base import FrameworkPlugin
from dbox.plugins.cakephp import CakePhpPlugin
from dbox.plugins.codeigniter import CodeIgniter4Plugin
from dbox.plugins.codeigniter3 import CodeIgniter3Plugin
from dbox.plugins.corephp import CorePhpPlugin
from dbox.plugins.drupal import DrupalPlugin
from dbox.plugins.joomla import JoomlaPlugin
from dbox.plugins.laravel import LaravelPlugin
from dbox.plugins.magento import MagentoPlugin
from dbox.plugins.symfony import SymfonyPlugin
from dbox.plugins.wordpress import WordPressPlugin
from dbox.plugins.yii import YiiPlugin

# Order is not significant; selection uses the `priority` attribute.
_PLUGIN_CLASSES = [
    LaravelPlugin,
    SymfonyPlugin,
    CodeIgniter4Plugin,
    CodeIgniter3Plugin,
    CakePhpPlugin,
    YiiPlugin,
    WordPressPlugin,
    DrupalPlugin,
    MagentoPlugin,
    JoomlaPlugin,
    CorePhpPlugin,
]

REGISTRY: dict[str, FrameworkPlugin] = {cls.name: cls() for cls in _PLUGIN_CLASSES}


def all_plugins() -> list[FrameworkPlugin]:
    return list(REGISTRY.values())


def get(name: str) -> FrameworkPlugin | None:
    return REGISTRY.get(name)


def names() -> list[str]:
    return list(REGISTRY.keys())


def detect(project_dir: Path) -> FrameworkPlugin | None:
    """Return the highest-priority plugin that matches the directory."""
    matches = [p for p in all_plugins() if p.detect(project_dir)]
    if not matches:
        return None
    matches.sort(key=lambda p: p.priority, reverse=True)
    return matches[0]
