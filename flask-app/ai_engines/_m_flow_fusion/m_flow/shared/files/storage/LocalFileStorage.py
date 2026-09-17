"""Concrete :class:`Storage` backend for the **local filesystem**.

Every operation is synchronous.  Paths are resolved relative to
*root* (the ``storage_path``).
"""

from __future__ import annotations

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, List, Optional, Union
from urllib.parse import urlparse

from .FileBufferedReader import FileBufferedReader
from .storage import Storage


# ── path helpers ──────────────────────────────────────────────────


def _to_native_path(raw: str) -> str:
    """Convert a ``file://``, ``http://``, or plain path to a native OS path."""
    if "://" not in raw:
        return os.path.normpath(raw)
    parsed = urlparse(raw)
    result = parsed.path
    if os.name == "nt" and result.startswith("/") and len(result) > 2 and result[2] == ":":
        result = result[1:]
    return os.path.normpath(result)


# alias
get_parsed_path = _to_native_path


# ── implementation ────────────────────────────────────────────────


class LocalFileStorage(Storage):
    storage_path: Optional[str] = None

    def __init__(self, root: str) -> None:
        self.storage_path = root

    def _abs(self, relative: str) -> str:
        return os.path.join(_to_native_path(self.storage_path), relative)

    # ── write ─────────────────────────────────────────────────────

    def store(self, file_path: str, data: Union[BinaryIO, str], overwrite: bool = False) -> str:
        dest = self._abs(file_path)
        self.ensure_directory_exists(os.path.dirname(dest))
        if not overwrite and os.path.exists(dest):
            return "file://" + dest
        if isinstance(data, str):
            with open(dest, "w", encoding="utf-8", newline="\n") as out:
                out.write(data)
        else:
            with open(dest, "wb") as out:
                if hasattr(data, "read"):
                    data.seek(0)
                    out.write(data.read())
                else:
                    out.write(data)
        return "file://" + dest

    # ── read ──────────────────────────────────────────────────────

    @contextmanager
    def open(self, file_path: str, mode: str = "rb", *args, **kwargs):
        base = _to_native_path(self.storage_path)
        full = os.path.join(base, file_path)
        if not os.path.exists(full):
            snippet = []
            if os.path.isdir(base):
                try:
                    snippet = os.listdir(base)[:10]
                except OSError:
                    snippet = ["<inaccessible>"]
            raise FileNotFoundError(
                f"'{full}' does not exist.  "
                f"Base='{base}', requested='{file_path}', "
                f"dir_exists={os.path.isdir(base)}, sample={snippet}"
            )
        raw = open(full, mode=mode, *args, **kwargs)
        wrapped = FileBufferedReader(raw, name="file://" + full)
        try:
            yield wrapped
        finally:
            wrapped.close()

    # ── queries ───────────────────────────────────────────────────

    def file_exists(self, file_path: str) -> bool:
        return os.path.exists(self._abs(file_path))

    def is_file(self, file_path: str) -> bool:
        return os.path.isfile(self._abs(file_path))

    def get_size(self, file_path: str) -> int:
        p = self._abs(file_path)
        return os.path.getsize(p) if os.path.exists(p) else 0

    # ── directory management ──────────────────────────────────────

    def ensure_directory_exists(self, directory_path: str = "") -> None:
        target = directory_path.strip() if directory_path else _to_native_path(self.storage_path)
        os.makedirs(target, exist_ok=True)

    def copy_file(self, src: str, dst: str) -> str:
        base = _to_native_path(self.storage_path)
        return shutil.copy2(os.path.join(base, src), os.path.join(base, dst))

    # ── deletion ──────────────────────────────────────────────────

    def remove(self, file_path: str) -> None:
        p = self._abs(file_path)
        if os.path.exists(p):
            os.remove(p)

    def list_files(self, directory_path: str, recursive: bool = False) -> List[str]:
        base = _to_native_path(self.storage_path)
        root = Path(os.path.join(base, directory_path) if directory_path else base)
        if not root.is_dir():
            return []
        entries = root.rglob("*") if recursive else root.iterdir()
        return [os.path.relpath(str(e), base).replace(os.sep, "/") for e in entries if e.is_file()]

    def remove_all(self, tree_path: str | None = None) -> None:
        base = _to_native_path(self.storage_path)
        target = base if tree_path is None else os.path.join(base, tree_path)
        shutil.rmtree(target, ignore_errors=True)
