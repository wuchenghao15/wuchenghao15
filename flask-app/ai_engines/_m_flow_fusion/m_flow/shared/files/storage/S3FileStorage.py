"""S3-compatible object-store implementation of :class:`Storage`.

Requires the ``s3fs`` package (installable via ``pip install m_flow[aws]``).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, BinaryIO, Union

from m_flow.shared.files.storage.s3_config import get_s3_config
from m_flow.shared.infra_utils.run_async import run_async
from m_flow.shared.files.storage.FileBufferedReader import FileBufferedReader
from .storage import Storage

if TYPE_CHECKING:
    import s3fs


def _strip_scheme(path: str) -> str:
    """Remove the ``s3://`` prefix from an S3 URI."""
    return path.replace("s3://", "", 1)


class S3FileStorage(Storage):
    """Async-capable storage backend backed by an S3-compatible service."""

    storage_path: str
    s3: "s3fs.S3FileSystem"

    def __init__(self, root_uri: str) -> None:
        try:
            import s3fs as _s3fs
        except ImportError:
            raise ImportError('s3fs is required for S3FileStorage. Install it with: pip install m_flow"[aws]"')

        self.storage_path = root_uri
        cfg = get_s3_config()

        if cfg.aws_access_key_id is None or cfg.aws_secret_access_key is None:
            raise ValueError("AWS S3 access credentials are missing from M-Flow configuration.")

        self.s3 = _s3fs.S3FileSystem(
            key=cfg.aws_access_key_id,
            secret=cfg.aws_secret_access_key,
            token=cfg.aws_session_token,
            anon=False,
            endpoint_url=cfg.aws_endpoint_url,
            client_kwargs={"region_name": cfg.aws_region},
        )

    # -- internal helpers ----------------------------------------------

    def _key(self, rel: str) -> str:
        """Build an absolute S3 key from a relative path."""
        return os.path.join(_strip_scheme(self.storage_path), rel)

    # -- write ---------------------------------------------------------

    async def store(
        self,
        file_path: str,
        data: Union[BinaryIO, str],
        overwrite: bool = False,
    ) -> str:
        """Persist *data* at *file_path* and return an ``s3://`` URI."""
        key = self._key(file_path)
        parent = os.path.dirname(key)
        await self.ensure_directory_exists(parent)

        if not overwrite and await self.file_exists(file_path):
            return "s3://" + key

        def _write():
            if isinstance(data, str):
                with self.s3.open(key, mode="w", encoding="utf-8", newline="\n") as fh:
                    fh.write(data)
            else:
                with self.s3.open(key, mode="wb") as fh:
                    if hasattr(data, "read"):
                        data.seek(0)
                        fh.write(data.read())
                    else:
                        fh.write(data)

        await run_async(_write)
        return "s3://" + key

    # -- read ----------------------------------------------------------

    @asynccontextmanager
    async def open(self, file_path: str, mode: str = "r"):
        """Yield a :class:`FileBufferedReader` wrapping the S3 object."""
        key = self._key(file_path)

        def _open():
            return self.s3.open(key, mode=mode)

        raw = await run_async(_open)
        wrapped = FileBufferedReader(raw, name="s3://" + key)
        try:
            yield wrapped
        finally:
            wrapped.close()

    # -- query ---------------------------------------------------------

    async def file_exists(self, file_path: str) -> bool:
        return await run_async(self.s3.exists, self._key(file_path))

    async def is_file(self, file_path: str) -> bool:
        return await run_async(self.s3.isfile, self._key(file_path))

    async def get_size(self, file_path: str) -> int:
        return await run_async(self.s3.size, self._key(file_path))

    # -- directory management ------------------------------------------

    async def ensure_directory_exists(self, directory_path: str = "") -> None:
        """No-op on S3 — directories are implicit key prefixes."""
        pass

    async def copy_file(self, source_file_path: str, destination_file_path: str):
        src_key = self._key(source_file_path)
        dst_key = self._key(destination_file_path)

        def _copy():
            return self.s3.copy(src_key, dst_key, recursive=True)

        return await run_async(_copy)

    # -- deletion ------------------------------------------------------

    async def remove(self, file_path: str) -> None:
        key = self._key(file_path)

        def _rm():
            if self.s3.exists(key):
                self.s3.rm_file(key)

        await run_async(_rm)

    async def list_files(self, directory_path: str, recursive: bool = False) -> list[str]:
        """Return paths relative to the storage root."""

        def _list():
            base = _strip_scheme(self.storage_path)
            full = os.path.join(base, directory_path) if directory_path else base
            pattern = f"{full}/**" if recursive else f"{full}/*"
            try:
                hits = self.s3.glob(pattern)
                files = [p for p in hits if self.s3.isfile(p)]
                return [p[len(base) :].lstrip("/") for p in files if p.startswith(base)]
            except Exception:
                return []

        return await run_async(_list)

    async def remove_all(self, tree_path: str | None = None) -> None:
        target = _strip_scheme(self.storage_path) if tree_path is None else self._key(tree_path)
        try:
            await run_async(self.s3.rm, target, recursive=True)
        except FileNotFoundError:
            pass
