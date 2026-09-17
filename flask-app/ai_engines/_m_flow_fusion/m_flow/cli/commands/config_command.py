"""
CLI 'config' command for M-flow settings management.

Provides subcommands to view, modify, and reset M-flow
configuration values via the command line.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Tuple

import m_flow.cli.echo as output
from m_flow.cli import DEFAULT_DOCS_URL
from m_flow.cli.exceptions import CliCommandException, CliCommandInnerException
from m_flow.cli.reference import SupportsCliCommand


# Mapping of config keys to (setter_method, default_value)
_SETTINGS_REGISTRY: Dict[str, Tuple[str, Any]] = {
    "llm_provider": ("set_llm_provider", "openai"),
    "llm_model": ("set_llm_model", "gpt-5-mini"),
    "llm_api_key": ("set_llm_api_key", ""),
    "llm_endpoint": ("set_llm_endpoint", ""),
    "graph_database_provider": ("set_graph_database_provider", "kuzu"),
    "vector_db_provider": ("set_vector_db_provider", "lancedb"),
    "vector_db_url": ("set_vector_db_url", ""),
    "vector_db_key": ("set_vector_db_key", ""),
    "chunk_size": ("set_chunk_size", 1500),
    "chunk_overlap": ("set_chunk_overlap", 10),
}

_DESCRIPTION = """\
Manage M-flow configuration settings.

Subcommands:
  get [KEY]     Display current value(s)
  set KEY VAL   Update a setting
  unset KEY     Reset to default
  list          Show available keys
  reset         Restore all defaults
"""


def _parse_value(raw: str) -> Any:
    """Attempt JSON parse, fallback to string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


class ConfigCommand(SupportsCliCommand):
    """Handler for configuration management."""

    command_string = "config"
    help_string = "Manage M-flow configuration"
    docs_url = DEFAULT_DOCS_URL
    description = _DESCRIPTION

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Set up subparsers for config actions."""
        subs = parser.add_subparsers(dest="action", help="Config actions")

        # get
        p_get = subs.add_parser("get", help="Retrieve setting(s)")
        p_get.add_argument("key", nargs="?", help="Specific key (omit for all)")

        # set
        p_set = subs.add_parser("set", help="Modify a setting")
        p_set.add_argument("key", help="Setting key")
        p_set.add_argument("value", help="New value")

        # list
        subs.add_parser("list", help="Available settings keys")

        # unset
        p_unset = subs.add_parser("unset", help="Reset to default")
        p_unset.add_argument("key", help="Key to reset")
        p_unset.add_argument("--force", "-f", action="store_true")

        # reset
        p_reset = subs.add_parser("reset", help="Reset all")
        p_reset.add_argument("--force", "-f", action="store_true")

    def execute(self, args: argparse.Namespace) -> None:
        """Dispatch to action handler."""
        try:
            import m_flow  # noqa: F401

            action = getattr(args, "action", None)
            if not action:
                output.error("Specify action: get | set | unset | list | reset")
                return

            handler = getattr(self, f"_do_{action}", None)
            if handler:
                handler(args)
            else:
                output.error(f"Unknown action: {action}")

        except CliCommandInnerException as err:
            raise CliCommandException(str(err), error_code=1) from err
        except Exception as err:
            raise CliCommandException(f"Config error: {err}", error_code=1) from err

    def _do_get(self, args: argparse.Namespace) -> None:
        """Handle 'get' subcommand."""
        import m_flow

        cfg = m_flow.config
        if args.key:
            if hasattr(cfg, "get"):
                try:
                    val = cfg.get(args.key)
                    output.echo(f"{args.key}: {val}")
                except Exception:
                    output.error(f"Key '{args.key}' not found")
            else:
                output.warning("config.get() not available")
        else:
            if hasattr(cfg, "get_all"):
                data = cfg.get_all()
                if data:
                    output.echo("Current settings:")
                    for k, v in data.items():
                        output.echo(f"  {k}: {v}")
                else:
                    output.echo("No settings stored")
            else:
                output.warning("config.get_all() not available")

    def _do_set(self, args: argparse.Namespace) -> None:
        """Handle 'set' subcommand."""
        import m_flow

        val = _parse_value(args.value)
        try:
            m_flow.config.set(args.key, val)
            output.success(f"Updated {args.key} = {val}")
        except Exception as err:
            output.error(f"Failed to set '{args.key}': {err}")

    def _do_unset(self, args: argparse.Namespace) -> None:
        """Handle 'unset' subcommand."""
        import m_flow

        if not args.force:
            if not output.confirm(f"Reset '{args.key}' to default?"):
                output.echo("Cancelled")
                return

        if args.key not in _SETTINGS_REGISTRY:
            output.error(f"Unknown key: {args.key}")
            output.note("Run 'mflow config list' for available keys")
            return

        method_name, default_val = _SETTINGS_REGISTRY[args.key]
        try:
            setter = getattr(m_flow.config, method_name)
            setter(default_val)
            output.success(f"Reset {args.key} to {default_val}")
        except AttributeError:
            output.error(f"Method {method_name} not found")
        except Exception as err:
            output.error(f"Reset failed: {err}")

    def _do_list(self, args: argparse.Namespace) -> None:
        """Handle 'list' subcommand."""
        output.echo("Available settings keys:")
        for key in _SETTINGS_REGISTRY:
            output.echo(f"  {key}")
        output.echo("")
        output.echo("Usage:")
        output.echo("  mflow config get [key]")
        output.echo("  mflow config set <key> <value>")
        output.echo("  mflow config unset <key>")
        output.echo("  mflow config reset")

    def _do_reset(self, args: argparse.Namespace) -> None:
        """Handle 'reset' subcommand."""
        if not args.force:
            if not output.confirm("Reset all settings to defaults?"):
                output.echo("Cancelled")
                return

        output.warning("Full reset not yet implemented")
        output.echo("Would restore all settings to defaults")
