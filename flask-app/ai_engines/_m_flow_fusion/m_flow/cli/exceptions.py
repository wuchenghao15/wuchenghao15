"""
M-Flow CLI error types.

Defines a two-tier exception model for command-line operations:

* ``CliCommandException`` – user-visible errors carrying a shell exit code
  and an optional documentation URL for guided troubleshooting.
* ``CliCommandInnerException`` – internal errors that are caught and
  wrapped before reaching the end user.
"""

from __future__ import annotations

from typing import Optional

_DEFAULT_EXIT_CODE = 1


class CliCommandException(Exception):
    """Terminal-facing error raised when a CLI command fails.

    Attributes
    ----------
    error_code : int
        Process exit code forwarded to the calling shell.
    docs_url : str | None
        Optional hyperlink to relevant troubleshooting documentation.
    raiseable_exception : Exception | None
        The underlying exception, if any, that triggered this error.
    """

    error_code: int
    docs_url: Optional[str]
    raiseable_exception: Optional[Exception]

    def __init__(
        self,
        description: str,
        *,
        error_code: int = _DEFAULT_EXIT_CODE,
        docs_url: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(description)
        self.error_code = error_code
        self.docs_url = docs_url
        self.raiseable_exception = cause

    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"[exit {self.error_code}] {base_msg}"


class CliCommandInnerException(Exception):
    """Internal error produced during command execution.

    Instances of this class are intercepted by the CLI framework and
    translated into ``CliCommandException`` instances with appropriate
    exit codes before they reach the user.
    """
