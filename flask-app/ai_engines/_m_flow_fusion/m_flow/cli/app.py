"""M-Flow CLI entry point.

Provides the ``mflow`` command with sub-commands for data ingestion,
search, memorisation, configuration and the web UI.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Type

try:
    import rich_argparse
    from rich.markdown import Markdown

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False

from m_flow.cli import DEFAULT_DOCS_URL, SupportsCliCommand
from m_flow.cli import debug as _debug
from m_flow.cli import echo as _echo
from m_flow.cli.config import CLI_DESCRIPTION
from m_flow.cli.exceptions import CliCommandException

# ---------------------------------------------------------------------------
# Argument actions
# ---------------------------------------------------------------------------

_action_taken = False


class _ToggleDebug(argparse.Action):
    """Enable verbose / debug output globally."""

    def __init__(self, option_strings: Sequence[str], dest: str = argparse.SUPPRESS, **kw: Any) -> None:
        kw.pop("dest", None)
        super().__init__(
            option_strings=option_strings, nargs=0, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, **kw
        )

    def __call__(self, *_a: Any, **_kw: Any) -> None:
        _debug.enable_debug()
        _echo.note("Debug mode enabled. Full stack traces will be shown.")


class _LaunchUi(argparse.Action):
    """Mark that the user requested the web UI."""

    def __init__(self, option_strings: Sequence[str], dest: str = argparse.SUPPRESS, **kw: Any) -> None:
        kw.pop("dest", None)
        super().__init__(
            option_strings=option_strings, nargs=0, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, **kw
        )

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, *_a: Any, **_kw: Any) -> None:
        global _action_taken
        _action_taken = True
        namespace.launch_ui = True


# ---------------------------------------------------------------------------
# Command discovery
# ---------------------------------------------------------------------------

_COMMAND_REGISTRY: List[tuple[str, str]] = [
    ("m_flow.cli.commands.add_command", "AddCommand"),
    ("m_flow.cli.commands.search_command", "SearchCommand"),
    ("m_flow.cli.commands.memorize_command", "MemorizeCommand"),
    ("m_flow.cli.commands.delete_command", "DeleteCommand"),
    ("m_flow.cli.commands.config_command", "ConfigCommand"),
]


def _load_commands() -> List[Type[SupportsCliCommand]]:
    """Lazily import command classes so the heavy ``m_flow`` package is not
    pulled in unless a command is actually invoked."""
    result: List[Type[SupportsCliCommand]] = []
    for mod_path, cls_name in _COMMAND_REGISTRY:
        try:
            mod = __import__(mod_path, fromlist=[cls_name])
            result.append(getattr(mod, cls_name))
        except (ImportError, AttributeError) as exc:
            _echo.warning(f"Could not load command {cls_name}: {exc}")
    return result


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def _version_string() -> str:
    try:
        from m_flow.version import get_version

        return f"m_flow {get_version()}"
    except Exception:
        return "m_flow (version unknown)"


def _apply_rich_formatting(root: argparse.ArgumentParser) -> None:
    """Recursively apply rich-argparse formatting when the library is present."""
    if not _RICH_AVAILABLE:
        return
    root.formatter_class = rich_argparse.RichHelpFormatter
    if root.description:
        root.description = Markdown(root.description, style="argparse.text")
    for act in root._actions:
        if isinstance(act, argparse._SubParsersAction):
            for sub in act.choices.values():
                _apply_rich_formatting(sub)


def _build_parser() -> tuple[argparse.ArgumentParser, Dict[str, SupportsCliCommand]]:
    root = argparse.ArgumentParser(
        description=f"{CLI_DESCRIPTION} Documentation: {DEFAULT_DOCS_URL}",
    )
    root.add_argument("--version", action="version", version=_version_string())
    root.add_argument("--debug", action=_ToggleDebug, help="Show full stack traces on errors")
    root.add_argument("-ui", action=_LaunchUi, help="Launch the M-Flow web interface")

    subs = root.add_subparsers(title="Commands", dest="command")

    commands: Dict[str, SupportsCliCommand] = {}
    for cls in _load_commands():
        inst = cls()
        if inst.command_string in commands:
            continue
        sp = subs.add_parser(
            inst.command_string,
            help=inst.help_string,
            description=getattr(inst, "description", None),
        )
        inst.configure_parser(sp)
        commands[inst.command_string] = inst

    _apply_rich_formatting(root)
    return root, commands


# ---------------------------------------------------------------------------
# UI server lifecycle
# ---------------------------------------------------------------------------


def _run_ui() -> int:
    """Start backend + frontend + MCP and block until interrupted."""
    from m_flow import start_ui

    child_pids: List[int] = []
    container_id: Optional[str] = None

    def _on_pid(val: Any) -> None:
        nonlocal container_id
        if isinstance(val, tuple):
            child_pids.append(val[0])
            container_id = val[1]
        else:
            child_pids.append(val)

    def _shutdown(sig: Any = None, _frame: Any = None) -> None:
        nonlocal container_id
        try:
            _echo.echo("\nShutting down…")
        except OSError:
            pass

        if container_id:
            try:
                subprocess.run(["docker", "stop", container_id], capture_output=True, timeout=10, check=False)
            except Exception:
                subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)

        for pid in child_pids:
            try:
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                else:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, check=False)
            except OSError:
                pass
        sys.exit(0)

    for sig_name in ("SIGINT", "SIGTERM", "SIGHUP"):
        sig_val = getattr(signal, sig_name, None)
        if sig_val is not None:
            signal.signal(sig_val, _shutdown)

    fe_port, be_port, mcp_port = 3000, 8000, 8001
    proc = start_ui(
        pid_callback=_on_pid,
        port=fe_port,
        open_browser=True,
        auto_download=True,
        start_backend=True,
        backend_port=be_port,
        start_mcp=True,
        mcp_port=mcp_port,
    )

    if proc is None:
        _echo.error("Failed to start UI — check logs above.")
        _shutdown()
        return 1

    _echo.success("M-Flow UI started")
    _echo.echo(f"  Frontend : http://localhost:{fe_port}")
    _echo.echo(f"  API      : http://localhost:{be_port}")
    _echo.echo(f"  MCP      : http://localhost:{mcp_port}")
    _echo.note("Press Ctrl+C to stop.")

    try:
        while proc.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()
    return 0


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def main() -> int:
    parser, commands = _build_parser()
    args = parser.parse_args()

    if getattr(args, "launch_ui", False):
        try:
            return _run_ui()
        except Exception as exc:
            _echo.error(f"UI startup failed: {exc}")
            if _debug.is_debug_enabled():
                raise
            return 1

    cmd = commands.get(args.command)
    if cmd is None:
        if not _action_taken:
            parser.print_help()
        return -1

    try:
        cmd.execute(args)
    except Exception as exc:
        docs = getattr(cmd, "docs_url", DEFAULT_DOCS_URL)
        code = -1
        cause: Optional[BaseException] = exc

        if isinstance(exc, CliCommandException):
            code = exc.error_code
            docs = exc.docs_url or docs
            cause = exc.raiseable_exception

        if cause:
            _echo.error(str(exc))
        _echo.note(f"See {docs} for help.")

        if _debug.is_debug_enabled() and cause:
            raise cause
        return code

    return 0


def _main() -> None:
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
