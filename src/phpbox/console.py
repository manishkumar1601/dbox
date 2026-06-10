"""Shared Rich console helpers for consistent CLI output."""

from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.theme import Theme

# On legacy Windows code pages (e.g. cp1252) the default stdout/stderr can't
# encode the Unicode status glyphs, especially when output is piped. Force the
# streams to UTF-8 so PHPBox renders identically everywhere.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

_theme = Theme(
    {
        "info": "cyan",
        "ok": "bold green",
        "warn": "yellow",
        "err": "bold red",
        "muted": "dim",
        "title": "bold magenta",
    }
)

console = Console(theme=_theme)


def info(message: str) -> None:
    console.print(f"[info]•[/info] {message}")


def success(message: str) -> None:
    console.print(f"[ok]✓[/ok] {message}")


def warn(message: str) -> None:
    console.print(f"[warn]![/warn] {message}")


def error(message: str) -> None:
    console.print(f"[err]✗[/err] {message}")


def step(message: str) -> None:
    console.print(f"[title]»[/title] {message}")


def fatal(message: str, code: int = 1) -> "typer.Exit":
    """Print an error and raise a typer.Exit to abort the command."""
    error(message)
    return typer.Exit(code)
