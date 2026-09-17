"""Produce an MD5 hex digest for arbitrary file content.

Works with both on-disk paths (routed through the storage layer)
and already-open binary handles.
"""

from __future__ import annotations

import hashlib
import os
from typing import BinaryIO, Union

from ..storage import get_file_storage
from ..exceptions import FileContentHashingError


def _hex_digest_of(reader: BinaryIO) -> str:
    """Consume *reader* in fixed-size chunks and return the MD5 hex string."""
    hasher = hashlib.md5()
    while chunk := reader.read(hasher.block_size):
        hasher.update(chunk)
    return hasher.hexdigest()


async def get_file_content_hash(source: Union[str, BinaryIO]) -> str:
    """Compute and return the MD5 hex digest of *source*.

    *source* may be a filesystem path (``str``) **or** a readable
    binary stream.  Paths are opened via the configured storage
    backend so that S3 objects work transparently.
    """
    try:
        if isinstance(source, str):
            clean = os.path.normpath(source)
            directory, name = os.path.split(clean)
            backend = get_file_storage(directory)
            async with backend.open(name, "rb") as fh:
                return _hex_digest_of(fh)
        return _hex_digest_of(source)
    except IOError as err:
        raise FileContentHashingError(
            message=f"Hashing failed for {source!r}: {err}",
        ) from err
