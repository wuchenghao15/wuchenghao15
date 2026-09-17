"""Hyper-Extract CLI - A command-line tool for knowledge extraction."""

from importlib.metadata import version

__version__ = version("hyperextract")
__author__ = "Yifan Feng"

from .cli import app

__all__ = ["app"]
