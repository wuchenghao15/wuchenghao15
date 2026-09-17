"""
Dataset database provisioning.

Creates or retrieves database connections for a dataset.
"""

from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from m_flow.adapters.graph.config import get_graph_config
from m_flow.adapters.relational import get_db_adapter
from m_flow.adapters.vector import get_vectordb_config
from m_flow.auth.models import DatasetStore, User
from m_flow.data.methods import create_dataset, get_unique_dataset_id


async def get_or_create_dataset_database(
    dataset: Union[str, UUID],
    user: User,
) -> DatasetStore:
    """
    Provision database connection for dataset.

    Returns existing record or creates new one with
    vector and graph database configuration.

    Args:
        dataset: Dataset name or UUID.
        user: Owning user.

    Returns:
        DatasetStore with connection details.
    """
    engine = get_db_adapter()
    ds_id = await get_unique_dataset_id(dataset, user)

    # Ensure dataset exists when given by name
    if isinstance(dataset, str):
        async with engine.get_async_session() as session:
            await create_dataset(dataset, user, session)

    # Return existing if found
    existing = await _find_existing(ds_id, user)
    if existing:
        return existing

    # Provision new databases
    graph_info = await _provision_graph_db(ds_id, user)
    vector_info = await _provision_vector_db(ds_id, user)

    return await _create_record(ds_id, user, graph_info, vector_info)


async def _find_existing(dataset_id: UUID, user: User) -> Optional[DatasetStore]:
    """Find existing database record."""
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        stmt = select(DatasetStore).where(
            DatasetStore.owner_id == user.id,
            DatasetStore.dataset_id == dataset_id,
        )
        return await session.scalar(stmt)


async def _provision_vector_db(dataset_id: UUID, user: User) -> dict:
    """Create vector database for dataset."""
    cfg = get_vectordb_config()

    from m_flow.adapters.dataset_database_handler.supported_dataset_database_handlers import (
        supported_dataset_database_handlers,
    )

    handler = supported_dataset_database_handlers[cfg.vector_dataset_database_handler]
    return await handler["handler_instance"].create_dataset(dataset_id, user)


async def _provision_graph_db(dataset_id: UUID, user: User) -> dict:
    """Create graph database for dataset."""
    cfg = get_graph_config()

    from m_flow.adapters.dataset_database_handler.supported_dataset_database_handlers import (
        supported_dataset_database_handlers,
    )

    handler = supported_dataset_database_handlers[cfg.graph_dataset_database_handler]
    return await handler["handler_instance"].create_dataset(dataset_id, user)


async def _create_record(
    dataset_id: UUID,
    user: User,
    graph_info: dict,
    vector_info: dict,
) -> DatasetStore:
    """Persist database record."""
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        record = DatasetStore(
            owner_id=user.id,
            dataset_id=dataset_id,
            **graph_info,
            **vector_info,
        )

        try:
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record
        except IntegrityError:
            await session.rollback()
            raise
