"""
Console output utilities for M-flow CLI.

Wraps Click's output functions with semantic helpers
for consistent command-line messaging.
"""

from __future__ import annotations

from typing import Any, Optional

import click

# Semantic color mapping
_STYLES = {
    "info": "blue",
    "warn": "yellow",
    "err": "red",
    "ok": "green",
}


def echo(
    message: str = "",
    color: Optional[str] = None,
    err: bool = False,
) -> None:
    """Output a styled message."""
    click.secho(message, fg=color, err=err)


def _styled(prefix: str, msg: str, style_key: str, to_err: bool = False) -> None:
    """Internal helper for prefixed styled output."""
    echo(f"{prefix}: {msg}", color=_STYLES[style_key], err=to_err)


def note(msg: str) -> None:
    """Print an informational note (blue)."""
    _styled("Note", msg, "info")


def warning(msg: str) -> None:
    """Print a warning (yellow)."""
    _styled("Warning", msg, "warn")


def error(msg: str) -> None:
    """Print an error to stderr (red)."""
    _styled("Error", msg, "err", to_err=True)


def success(msg: str) -> None:
    """Print a success message (green)."""
    _styled("Success", msg, "ok")


def bold(text: str) -> str:
    """Return text with bold formatting applied."""
    return click.style(text, bold=True)


def confirm(prompt_text: str, default: bool = False) -> bool:
    """Request yes/no confirmation from user."""
    return click.confirm(prompt_text, default=default)


def prompt(prompt_text: str, default: Any = None) -> str:
    """Request text input from user."""
    return click.prompt(prompt_text, default=default)
