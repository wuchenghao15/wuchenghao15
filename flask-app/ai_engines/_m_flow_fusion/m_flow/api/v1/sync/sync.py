"""
Cloud synchronization module.

Handles bidirectional sync between local M-flow and M-flow Cloud.
"""

from __future__ import annotations

import asyncio
import io
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import aiohttp
from pydantic import BaseModel

from m_flow.api.v1.memorize import memorize
from m_flow.auth.models import User
from m_flow.data.methods import fetch_dataset_items
from m_flow.data.models import Dataset
from m_flow.ingestion.pipeline_tasks.ingest_data import ingest_data
from m_flow.shared.files.storage import get_file_storage
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.sync.methods import (
    create_sync_operation,
    mark_sync_completed,
    mark_sync_failed,
    mark_sync_started,
    update_sync_operation,
)
from m_flow.shared.utils import create_secure_ssl_context

_log = get_logger("sync")

_MAX_RETRIES = 3


# ===================== Request/Response Models =====================


class LocalFileInfo(BaseModel):
    """Metadata for a local file with content hash."""

    id: str
    name: str
    mime_type: str | None
    extension: str | None
    processed_path: str
    content_hash: str
    file_size: int
    graph_scope: str | None = None


class CheckMissingHashesRequest(BaseModel):
    """Payload for hash diff check."""

    dataset_id: str
    dataset_name: str
    hashes: list[str]


class CheckHashesDiffResponse(BaseModel):
    """Result of hash comparison."""

    missing_on_remote: list[str]
    missing_on_local: list[str]


class PruneDatasetRequest(BaseModel):
    """Payload for dataset pruning."""

    items: list[str]


class SyncResponse(BaseModel):
    """Immediate response when sync starts."""

    run_id: str
    status: str
    dataset_ids: list[str]
    dataset_names: list[str]
    message: str
    timestamp: str
    user_id: str


@dataclass
class DatasetSyncResult:
    """Outcome of syncing a single dataset."""

    dataset_name: str
    dataset_id: str
    records_downloaded: int
    records_uploaded: int
    bytes_downloaded: int
    bytes_uploaded: int
    has_uploads: bool
    has_downloads: bool
    uploaded_hashes: list[str]
    downloaded_hashes: list[str]


class InMemoryDownload:
    """File-like wrapper for downloaded bytes."""

    def __init__(self, data: bytes, filename: str):
        self.file = io.BufferedReader(io.BytesIO(data))
        self.filename = filename


# ===================== Main Sync Entry =====================


async def sync(datasets: list[Dataset], user: User) -> SyncResponse:
    """
    Start background sync of datasets to M-flow Cloud.

    Args:
        datasets: Authorized datasets to sync.
        user: Authenticated user.

    Returns:
        SyncResponse with run_id for tracking.
    """
    if not datasets:
        raise ValueError("No datasets provided")

    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    names = [d.name for d in datasets]
    ids = [str(d.id) for d in datasets]

    _log.info("Initiating sync %s for datasets: %s", run_id, ", ".join(names))

    try:
        await create_sync_operation(
            run_id=run_id,
            dataset_ids=[d.id for d in datasets],
            dataset_names=names,
            user_id=user.id,
        )
    except Exception as exc:
        _log.error("Failed to create sync record: %s", exc)

    asyncio.create_task(_background_sync(run_id, datasets, user))

    return SyncResponse(
        run_id=run_id,
        status="started",
        dataset_ids=ids,
        dataset_names=names,
        message=f"Sync started for {len(datasets)} dataset(s). Track with run_id: {run_id}",
        timestamp=ts,
        user_id=str(user.id),
    )


# ===================== Background Processing =====================


async def _background_sync(run_id: str, datasets: list[Dataset], user: User) -> None:
    """Execute sync in background with retry logic."""
    t0 = datetime.now(timezone.utc)
    try:
        _log.info("Background sync %s starting", run_id)
        await mark_sync_started(run_id)

        result = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                result = await _execute_cloud_sync(datasets, user, run_id)
                break
            except Exception as exc:
                _log.error("Sync %s attempt %d failed: %s", run_id, attempt, exc)
                await update_sync_operation(run_id, retry_count=attempt)
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(2**attempt)

        if result is None:
            _log.error("Sync %s exhausted retries", run_id)
            await mark_sync_failed(run_id, f"Failed after {_MAX_RETRIES} attempts")
            return

        dl, ul, db, ub, hashes = result
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
        _log.info("Sync %s complete: ↓%d/%d bytes ↑%d/%d bytes in %.1fs", run_id, dl, db, ul, ub, elapsed)

        await mark_sync_completed(run_id, dl, ul, db, ub, hashes)

    except Exception as exc:
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
        _log.error("Sync %s failed after %.1fs: %s", run_id, elapsed, exc)
        await mark_sync_failed(run_id, str(exc))


async def _execute_cloud_sync(
    datasets: list[Dataset],
    user: User,
    run_id: str,
) -> tuple[int, int, int, int, dict]:
    """
    Perform bidirectional sync with cloud.

    Returns:
        (records_downloaded, records_uploaded, bytes_downloaded, bytes_uploaded, hash_map)
    """
    base_url = await _cloud_url()
    token = await _cloud_token(user)

    tasks = [_sync_one_dataset(d, base_url, token, user, run_id) for d in datasets]

    total_dl = total_ul = total_db = total_ub = 0
    any_uploads = any_downloads = False
    processed = []
    hash_map: dict[str, Any] = {}

    done = 0
    for coro in asyncio.as_completed(tasks):
        try:
            res = await coro
            done += 1
            pct = int(done / len(datasets) * 80)
            await _update_progress(run_id, "file_sync", progress_percentage=pct)

            if res is None:
                continue

            total_dl += res.records_downloaded
            total_ul += res.records_uploaded
            total_db += res.bytes_downloaded
            total_ub += res.bytes_uploaded
            any_uploads |= res.has_uploads
            any_downloads |= res.has_downloads
            processed.append(res.dataset_id)
            hash_map[res.dataset_id] = {
                "uploaded": res.uploaded_hashes,
                "downloaded": res.downloaded_hashes,
            }
            _log.info(
                "Dataset %s synced: ↑%d ↓%d",
                res.dataset_name,
                res.records_uploaded,
                res.records_downloaded,
            )
        except Exception as exc:
            done += 1
            _log.error("Dataset sync failed: %s", exc)
            await _update_progress(run_id, "file_sync", progress_percentage=int(done / len(datasets) * 80))

    # Remote memorize if uploads occurred
    await _update_progress(run_id, "memorize", progress_percentage=90)
    if any_uploads and processed:
        try:
            await _trigger_remote_memorize(base_url, token, datasets[0].id, run_id)
        except Exception as exc:
            _log.warning("Remote memorize failed: %s", exc)

    # Local memorize if downloads occurred
    # Disable content_routing - synced data has already been processed
    # and doesn't require sentence-level routing
    if any_downloads and processed:
        try:
            await memorize(enable_content_routing=False)
        except Exception as exc:
            _log.warning("Local memorize failed: %s", exc)

    await _update_progress(
        run_id,
        "final",
        progress_percentage=100,
        total_records_to_sync=total_ul + total_dl,
        records_downloaded=total_dl,
        records_uploaded=total_ul,
    )

    return total_dl, total_ul, total_db, total_ub, hash_map


# ===================== Per-Dataset Sync =====================


async def _sync_one_dataset(
    dataset: Dataset,
    base_url: str,
    token: str,
    user: User,
    run_id: str,
) -> DatasetSyncResult | None:
    """Sync files for a single dataset."""
    _log.info("Syncing dataset %s (%s)", dataset.name, dataset.id)

    local_files = await _extract_files(dataset, user, run_id)
    if not local_files:
        return None

    local_hashes = [f.content_hash for f in local_files]
    diff = await _check_diff(base_url, token, dataset, local_hashes, run_id)

    bytes_up = await _upload_files(base_url, token, dataset, local_files, diff.missing_on_remote, run_id)
    bytes_down = await _download_files(base_url, token, dataset, diff.missing_on_local, user)

    return DatasetSyncResult(
        dataset_name=dataset.name,
        dataset_id=str(dataset.id),
        records_downloaded=len(diff.missing_on_local),
        records_uploaded=len(diff.missing_on_remote),
        bytes_downloaded=bytes_down,
        bytes_uploaded=bytes_up,
        has_uploads=bool(diff.missing_on_remote),
        has_downloads=bool(diff.missing_on_local),
        uploaded_hashes=diff.missing_on_remote,
        downloaded_hashes=diff.missing_on_local,
    )


# ===================== File Extraction =====================


async def _extract_files(dataset: Dataset, user: User, run_id: str) -> list[LocalFileInfo]:
    """Build list of local files with hashes."""
    entries = await fetch_dataset_items(dataset.id)
    result = []
    for e in entries:
        if not e.source_digest:
            continue
        size = e.data_size or await _file_size(e.processed_path)
        result.append(
            LocalFileInfo(
                id=str(e.id),
                name=e.name,
                mime_type=e.mime_type,
                extension=e.extension,
                processed_path=e.processed_path,
                content_hash=e.source_digest,
                file_size=size,
                graph_scope=e.graph_scope,
            )
        )
    return result


async def _file_size(path: str) -> int:
    try:
        storage = get_file_storage(os.path.dirname(path))
        return await storage.get_size(os.path.basename(path))
    except Exception:
        return 0


# ===================== Cloud API Helpers =====================


async def _cloud_url() -> str:
    return os.getenv("MFLOW_CLOUD_API_URL", "http://localhost:8001")


async def _cloud_token(user: User) -> str:
    return os.getenv("MFLOW_CLOUD_AUTH_TOKEN", "default-token")


async def _check_diff(
    base_url: str,
    token: str,
    dataset: Dataset,
    hashes: list[str],
    run_id: str,
) -> CheckHashesDiffResponse:
    """Query cloud for hash diff."""
    url = f"{base_url}/api/sync/{dataset.id}/diff"
    payload = CheckMissingHashesRequest(
        dataset_id=str(dataset.id),
        dataset_name=dataset.name,
        hashes=hashes,
    )
    headers = {"X-Api-Key": token, "Content-Type": "application/json"}

    ssl_ctx = create_secure_ssl_context()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_ctx)) as sess:
        async with sess.post(url, json=payload.dict(), headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return CheckHashesDiffResponse(**data)
            text = await resp.text()
            raise ConnectionError(f"Diff check failed: {resp.status} - {text}")


async def _upload_files(
    base_url: str,
    token: str,
    dataset: Dataset,
    files: list[LocalFileInfo],
    missing: list[str],
    run_id: str,
) -> int:
    """Upload files missing on remote."""
    to_upload = [f for f in files if f.content_hash in missing]
    if not to_upload:
        return 0

    total = 0
    headers = {"X-Api-Key": token}
    ssl_ctx = create_secure_ssl_context()

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_ctx)) as sess:
        for f in to_upload:
            storage = get_file_storage(os.path.dirname(f.processed_path))
            async with storage.open(os.path.basename(f.processed_path), "rb") as fh:
                content = fh.read()

            form = aiohttp.FormData()
            form.add_field("file", content, content_type=f.mime_type, filename=f.name)
            form.add_field("dataset_id", str(dataset.id))
            form.add_field("dataset_name", dataset.name)
            form.add_field("data_id", f.id)
            form.add_field("mime_type", f.mime_type or "")
            form.add_field("extension", f.extension or "")
            form.add_field("md5", f.content_hash)

            url = f"{base_url}/api/sync/{dataset.id}/data/{f.id}"
            async with sess.put(url, data=form, headers=headers) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise ConnectionError(f"Upload failed: {resp.status} - {text}")
                total += len(content)

    return total


async def _download_files(
    base_url: str,
    token: str,
    dataset: Dataset,
    missing: list[str],
    user: User,
) -> int:
    """Download files missing locally."""
    if not missing:
        return 0

    total = 0
    headers = {"X-Api-Key": token}
    ssl_ctx = create_secure_ssl_context()

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_ctx)) as sess:
        for h in missing:
            url = f"{base_url}/api/sync/{dataset.id}/data/{h}"
            async with sess.get(url, headers=headers) as resp:
                if resp.status == 404:
                    continue
                if resp.status != 200:
                    continue
                content = await resp.read()
                fname = resp.headers.get("X-File-Name", f"file_{h}")
                await _save_file(dataset, h, fname, content, user)
                total += len(content)

    return total


async def _save_file(dataset: Dataset, h: str, name: str, data: bytes, user: User) -> None:
    """Persist downloaded file via ingestion pipeline."""
    obj = InMemoryDownload(data, name)
    await ingest_data(data=obj, dataset_name=dataset.name, user=user, dataset_id=dataset.id)


async def _trigger_remote_memorize(base_url: str, token: str, ds_id, run_id: str) -> None:
    """Trigger memorize on cloud."""
    url = f"{base_url}/api/memorize"
    headers = {"X-Api-Key": token, "Content-Type": "application/json"}
    payload = {"dataset_ids": [str(ds_id)], "run_in_background": False}

    ssl_ctx = create_secure_ssl_context()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_ctx)) as sess:
        async with sess.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                _log.warning("Remote memorize failed: %s - %s", resp.status, text)


async def _update_progress(run_id: str, stage: str, **kwargs) -> None:
    """Update sync progress (non-critical)."""
    try:
        await update_sync_operation(run_id, **kwargs)
    except Exception as exc:
        _log.warning("Progress update failed (%s): %s", stage, exc)
