"""Thin wrapper around ``BufferedReader`` carrying a caller-supplied name.

Downstream code often inspects ``file.name`` to build storage URIs or log
messages.  The standard ``BufferedReader`` derives *name* from the
underlying raw stream which may be a temporary or anonymous handle.
This subclass lets callers inject a canonical name at construction time.
"""

from io import BufferedReader


class FileBufferedReader(BufferedReader):
    """BufferedReader that exposes an explicit ``name`` property."""

    __slots__ = ("_wrapped", "_label")

    def __init__(self, raw_stream, name: str) -> None:
        super().__init__(raw_stream)
        self._wrapped = raw_stream
        self._label = name

    # -- public interface ------------------------------------------------

    @property
    def name(self) -> str:  # noqa: D401
        """Canonical name supplied at construction time."""
        return self._label

    def read(self, n: int = -1) -> bytes:
        """Delegate reading to the wrapped stream."""
        return self._wrapped.read(n)
