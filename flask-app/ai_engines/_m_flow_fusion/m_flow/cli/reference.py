"""
M-Flow CLI command protocol.

Every CLI command registered with the M-Flow command-line framework must
satisfy the ``SupportsCliCommand`` structural protocol.  This ensures a
uniform interface for argument parsing, execution, and help-text
generation across all sub-commands.
"""

from __future__ import annotations

import argparse
from abc import abstractmethod
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class SupportsCliCommand(Protocol):
    """Structural contract for M-Flow CLI sub-command handlers.

    Implementors expose metadata fields consumed by the argument-parser
    registry (``command_string``, ``help_string``, ``description``,
    ``docs_url``) and two lifecycle methods — one for declaring accepted
    arguments and one for carrying out the command logic.
    """

    command_string: str
    help_string: str
    description: Optional[str]
    docs_url: Optional[str]

    @abstractmethod
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Register flags, positional args, and sub-parsers.

        Called once during CLI bootstrap to populate the shared
        ``ArgumentParser`` tree.
        """
        ...

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """Run the command against the fully-parsed *args* namespace.

        Implementations should raise ``CliCommandException`` on
        recoverable user errors and let unexpected exceptions propagate
        for the global handler.
        """
        ...
