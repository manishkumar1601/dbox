"""Plugin registry — discovery and lookup of framework plugins."""

from __future__ import annotations

from pathlib import Path

from phpbox.plugins.base import FrameworkPlugin
from phpbox.plugins.cakephp import CakePhpPlugin
from phpbox.plugins.codeigniter import CodeIgniter4Plugin
from phpbox.plugins.codeigniter3 import CodeIgniter3Plugin
from phpbox.plugins.corephp import CorePhpPlugin
from phpbox.plugins.drupal import DrupalPlugin
from phpbox.plugins.joomla import JoomlaPlugin
from phpbox.plugins.laravel import LaravelPlugin
from phpbox.plugins.magento import MagentoPlugin
from phpbox.plugins.symfony import SymfonyPlugin
from phpbox.plugins.wordpress import WordPressPlugin
from phpbox.plugins.yii import YiiPlugin

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
