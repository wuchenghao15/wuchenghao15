"""
Allow running the toolkit from the command line via ``python -m m_flow``.

Delegates to the CLI entry-point defined in ``m_flow.cli.app``.
"""

from __future__ import annotations


def _boot() -> None:
    """Import and invoke the CLI main function."""
    from m_flow.cli.app import main as _entry  # late import keeps startup fast

    _entry()


if __name__ == "__main__":
    _boot()
