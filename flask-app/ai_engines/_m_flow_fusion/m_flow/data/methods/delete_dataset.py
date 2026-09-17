"""
Dataset Deletion Module
=======================

Handles complete removal of datasets including their associated
graph and vector database storage.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from m_flow.auth.models import DatasetStore
from m_flow.data.models import Dataset
from m_flow.adapters.relational import get_db_adapter
from m_flow.adapters.utils.get_vector_dataset_database_handler import (
    get_vector_dataset_database_handler,
)
from m_flow.adapters.utils.get_graph_dataset_database_handler import (
    get_graph_dataset_database_handler,
)
from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)


async def delete_dataset(dataset: Dataset):
    """
    Remove a dataset and all its associated storage.

    This function performs a cascading delete that includes:
    1. Clear per-dataset workflow_state from linked Data objects
    2. Graph database contents for the dataset
    3. Vector database contents for the dataset
    4. The dataset record itself (CASCADE deletes dataset_data)

    Clearing workflow_state is essential: dataset IDs are deterministic
    (uuid5 of name + user), so re-creating a dataset with the same name
    would reuse the same ID.  Without clearing, incremental loading would
    see stale COMPLETED markers and skip the add task chain entirely,
    leaving the new dataset with no data associations.

    Parameters
    ----------
    dataset : Dataset
        The dataset entity to delete.

    Returns
    -------
    bool
        True if deletion was successful.
    """
    db = get_db_adapter()

    # --- Step 1: Clear workflow_state entries for this dataset ---
    # Must run BEFORE delete_entity_by_id, because fetch_dataset_items
    # relies on dataset_data JOIN which is CASCADE-deleted with the dataset.
    await _clear_pipeline_status_for_dataset(db, dataset)

    # --- Step 2: Delete graph and vector storage ---
    async with db.get_async_session() as session:
        query = select(DatasetStore).where(DatasetStore.dataset_id == dataset.id)
        db_record: DatasetStore = await session.scalar(query)

        if db_record is not None:
            graph_handler_info = get_graph_dataset_database_handler(db_record)
            vector_handler_info = get_vector_dataset_database_handler(db_record)

            await graph_handler_info["handler_instance"].delete_dataset(db_record)
            await vector_handler_info["handler_instance"].delete_dataset(db_record)

    # --- Step 3: Delete the dataset row (CASCADE deletes dataset_data) ---
    return await db.delete_entity_by_id(dataset.__tablename__, dataset.id)


async def _clear_pipeline_status_for_dataset(db, dataset: Dataset) -> None:
    """
    Remove this dataset's entries from workflow_state of all linked Data rows.

    workflow_state structure: {"add_pipeline": {"<dataset_id>": "..."}, ...}
    We delete the inner key so incremental loading won't treat the data as
    already processed when the same dataset name (and thus same ID) is recreated.
    """
    from m_flow.data.methods.fetch_dataset_items import fetch_dataset_items

    data_items = await fetch_dataset_items(dataset.id)
    if not data_items:
        return

    ds_key = str(dataset.id)
    cleaned = 0

    async with db.get_async_session() as session:
        for item in data_items:
            if not item.workflow_state:
                continue

            item = await session.merge(item)
            changed = False

            for workflow_name in list(item.workflow_state.keys()):
                inner = item.workflow_state.get(workflow_name, {})
                if ds_key in inner:
                    del inner[ds_key]
                    changed = True

            if changed:
                flag_modified(item, "workflow_state")
                cleaned += 1

        if cleaned:
            await session.commit()
            _log.info(
                "Cleared workflow_state for dataset %s from %d data items",
                ds_key,
                cleaned,
            )
