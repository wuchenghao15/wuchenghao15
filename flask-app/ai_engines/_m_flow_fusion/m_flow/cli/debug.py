"""
CLI Debug Mode Controller
=========================

Simple module-level flag for controlling debug output verbosity
in the command-line interface.
"""

from __future__ import annotations


# Module-level debug state
_debug_mode_active: bool = False


def enable_debug() -> None:
    """
    Activate debug mode for verbose CLI output.

    When enabled, the CLI will display additional diagnostic
    information during command execution.
    """
    global _debug_mode_active
    _debug_mode_active = True


def disable_debug() -> None:
    """
    Deactivate debug mode to reduce CLI output.

    Returns the CLI to normal verbosity levels.
    """
    global _debug_mode_active
    _debug_mode_active = False


def is_debug_enabled() -> bool:
    """
    Check whether debug mode is currently active.

    Returns
    -------
    bool
        True if debug output is enabled, False otherwise.
    """
    return _debug_mode_active
