"""
Cache management with storage backend abstraction.

Provides a unified caching layer that works with local filesystem
and cloud storage (S3) through the StorageManager interface.
"""

from __future__ import annotations

import hashlib
import logging
import os
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING, Optional

import aiohttp

from m_flow.base_config import get_base_config
from m_flow.shared.files.storage.get_file_storage import get_file_storage
from m_flow.shared.utils import create_secure_ssl_context

if TYPE_CHECKING:
    from m_flow.shared.files.storage.StorageManager import StorageManager

_logger = logging.getLogger(__name__)

# HTTP timeout settings
_HEAD_TIMEOUT = aiohttp.ClientTimeout(total=30)
_GET_TIMEOUT = aiohttp.ClientTimeout(total=60)
_CHUNK_SIZE = 8192


def _compute_short_hash(content: str) -> str:
    """Compute a truncated MD5 hash for cache keys."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


class StorageAwareCache:
    """
    Cache manager supporting multiple storage backends.

    Abstracts caching operations to work with local filesystem,
    S3, and other storage systems through StorageManager.

    Attributes:
        storage_manager: The underlying storage abstraction.
    """

    def __init__(self, subdir: str = "cache") -> None:
        """
        Initialize the cache manager.

        Args:
            subdir: Subdirectory name for cache storage (unused, kept for API compat).
        """
        config = get_base_config()
        self._base_path = ""
        self.storage_manager: StorageManager = get_file_storage(
            config.cache_root_directory,
        )

        # Log storage location
        storage_path = self.storage_manager.storage.storage_path
        if not storage_path.startswith("s3://"):
            storage_path = os.path.abspath(storage_path)
        _logger.info("Cache storage path: %s", storage_path)

    def _join_path(self, *parts: str) -> str:
        """Join path components, handling empty base path."""
        non_empty = [p for p in parts if p]
        return "/".join(non_empty) if non_empty else "."

    def _get_absolute_path(self, relative: str) -> str:
        """Convert relative cache path to absolute path."""
        storage_path = self.storage_manager.storage.storage_path

        if storage_path.startswith("s3://"):
            return relative  # S3 paths are already "absolute"

        if hasattr(self.storage_manager.storage, "storage_path"):
            base = os.path.abspath(storage_path)
            return os.path.join(base, relative) if relative != "." else base

        return relative

    async def get_cache_dir(self) -> str:
        """Retrieve the root cache directory path."""
        path = self._base_path or "."
        await self.storage_manager.ensure_directory_exists(path)
        return path

    async def get_cache_subdir(self, name: str) -> str:
        """
        Get or create a named subdirectory in the cache.

        Args:
            name: Subdirectory name.

        Returns:
            Absolute path to the subdirectory.
        """
        path = self._join_path(self._base_path, name)
        await self.storage_manager.ensure_directory_exists(path)
        return self._get_absolute_path(path)

    async def delete_cache(self) -> None:
        """Remove all cached content."""
        _logger.info("Clearing cache...")
        try:
            await self.storage_manager.remove_all(self._base_path)
            _logger.info("Cache cleared successfully")
        except Exception as err:
            _logger.error("Failed to clear cache: %s", err)
            raise

    async def _read_version(self, cache_dir: str) -> Optional[str]:
        """Read cached version identifier."""
        version_path = f"{cache_dir}/version.txt"
        if not await self.storage_manager.file_exists(version_path):
            return None
        try:
            async with self.storage_manager.open(version_path, "r") as fp:
                import asyncio

                content = await asyncio.to_thread(fp.read)
                return content.strip()
        except Exception:
            return None

    async def _is_cache_valid(self, cache_dir: str, expected: str) -> bool:
        """Check if cached content matches expected version."""
        cached = await self._read_version(cache_dir)
        return cached == expected

    async def _check_freshness(
        self,
        url: str,
        cache_dir: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if remote content has changed since caching.

        Uses HTTP ETag or Last-Modified headers for comparison.

        Returns:
            Tuple of (is_fresh, new_identifier).
        """
        try:
            ssl_ctx = create_secure_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.head(url, timeout=_HEAD_TIMEOUT) as resp:
                    resp.raise_for_status()
                    etag = resp.headers.get("ETag", "").strip('"')
                    modified = resp.headers.get("Last-Modified", "")

            remote_id = etag or modified
            if not remote_id:
                return True, None  # No freshness headers

            # Compare with cached identifier
            id_path = f"{cache_dir}/content_id.txt"
            if await self.storage_manager.file_exists(id_path):
                async with self.storage_manager.open(id_path, "r") as fp:
                    import asyncio

                    cached_id = (await asyncio.to_thread(fp.read)).strip()
                    if cached_id == remote_id:
                        return True, None
                    return False, remote_id

            return False, remote_id

        except Exception as err:
            _logger.debug("Freshness check failed: %s", err)
            return True, None

    async def _clear_dir(self, path: str) -> None:
        """Remove contents of a cache directory."""
        try:
            await self.storage_manager.remove_all(path)
        except Exception as err:
            _logger.debug("Failed to clear %s: %s", path, err)

    async def download_and_extract_zip(
        self,
        url: str,
        subdir_name: str,
        version: str,
        force: bool = False,
    ) -> str:
        """
        Download and extract a ZIP archive to cache.

        Checks for existing cached content and validates freshness
        before downloading. Stores version and content identifiers
        for future validation.

        Args:
            url: URL of the ZIP file.
            subdir_name: Target subdirectory name.
            version: Version identifier for cache validation.
            force: Skip cache validation and re-download.

        Returns:
            Path to the extracted content directory.
        """
        cache_dir = await self.get_cache_subdir(subdir_name)

        # Check existing cache validity
        if not force and await self._is_cache_valid(cache_dir, version):
            is_fresh, _ = await self._check_freshness(url, cache_dir)
            if is_fresh:
                _logger.debug("Using cached content for version %s", version)
                return cache_dir
            _logger.info("Cached content is stale, refreshing...")

        # Clear and re-download
        await self._clear_dir(cache_dir)
        _logger.info("Downloading from %s", url)

        # Fetch ZIP content
        buffer = BytesIO()
        etag = ""
        modified = ""

        ssl_ctx = create_secure_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=_GET_TIMEOUT) as resp:
                resp.raise_for_status()
                etag = resp.headers.get("ETag", "").strip('"')
                modified = resp.headers.get("Last-Modified", "")

                async for chunk in resp.content.iter_chunked(_CHUNK_SIZE):
                    buffer.write(chunk)

        buffer.seek(0)

        # Extract archive
        await self.storage_manager.ensure_directory_exists(cache_dir)

        with zipfile.ZipFile(buffer, "r") as zf:
            for info in zf.infolist():
                target = f"{cache_dir}/{info.filename}"
                if info.is_dir():
                    await self.storage_manager.ensure_directory_exists(target)
                else:
                    data = zf.read(info.filename)
                    await self.storage_manager.store(target, BytesIO(data), overwrite=True)

        # Store metadata for future validation
        await self.storage_manager.store(
            f"{cache_dir}/version.txt",
            version,
            overwrite=True,
        )

        content_id = etag or modified
        if content_id:
            await self.storage_manager.store(
                f"{cache_dir}/content_id.txt",
                content_id,
                overwrite=True,
            )

        _logger.info("Content cached successfully")
        return cache_dir

    async def file_exists(self, path: str) -> bool:
        """Check if a file exists in cache."""
        return await self.storage_manager.file_exists(path)

    async def read_file(self, path: str, encoding: str = "utf-8"):
        """Open a cached file for reading."""
        return self.storage_manager.open(path, encoding=encoding)

    async def list_files(self, directory: str) -> list[str]:
        """List files in a cache directory as absolute paths."""
        try:
            files = await self.storage_manager.list_files(directory)

            storage_path = self.storage_manager.storage.storage_path
            if storage_path.startswith("s3://"):
                return [f"{storage_path}/{f}" for f in files]

            base = os.path.abspath(storage_path)
            result: list[str] = []
            for f in files:
                if os.path.isabs(f):
                    result.append(f)
                else:
                    result.append(os.path.join(base, f))
            return result

        except Exception as err:
            _logger.debug("Error listing %s: %s", directory, err)
            return []


# Singleton instance
_instance: Optional[StorageAwareCache] = None


def get_cache_manager() -> StorageAwareCache:
    """Retrieve the singleton cache manager."""
    global _instance
    if _instance is None:
        _instance = StorageAwareCache()
    return _instance


def generate_content_hash(url: str, extra: str = "") -> str:
    """Generate a short content hash for cache keys."""
    return _compute_short_hash(f"{url}:{extra}")


# API wrappers


async def delete_cache() -> None:
    """Clear the M-flow cache."""
    await get_cache_manager().delete_cache()


async def get_cache_dir() -> str:
    """Get the base cache directory."""
    return await get_cache_manager().get_cache_dir()


async def get_cache_subdir(name: str) -> str:
    """Get a named cache subdirectory."""
    return await get_cache_manager().get_cache_subdir(name)


async def download_and_extract_zip(
    url: str,
    cache_dir_name: str,
    version_or_hash: str,
    force: bool = False,
) -> str:
    """Download and extract a ZIP to cache."""
    return await get_cache_manager().download_and_extract_zip(url, cache_dir_name, version_or_hash, force)


async def get_tutorial_data_dir() -> str:
    """Get the tutorial data cache directory."""
    return await get_cache_subdir("tutorial_data")


async def cache_file_exists(path: str) -> bool:
    """Check if a file exists in cache."""
    return await get_cache_manager().file_exists(path)


async def read_cache_file(path: str, encoding: str = "utf-8"):
    """Read a file from cache."""
    return await get_cache_manager().read_file(path, encoding)


async def list_cache_files(directory: str) -> list[str]:
    """List files in a cache directory."""
    return await get_cache_manager().list_files(directory)
