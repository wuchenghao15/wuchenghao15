"""
Datasets API Module
===================

Provides a programmatic interface for dataset management operations
including listing, discovery, data access, and deletion.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.data.methods import has_dataset_data
from m_flow.auth.methods import get_seed_user
from m_flow.ingestion.core import discover_directory_datasets
from m_flow.pipeline.operations.get_workflow_status import get_workflow_status


class datasets:
    """
    Dataset management operations.

    Provides static methods for interacting with datasets
    programmatically without going through HTTP endpoints.
    """

    @staticmethod
    async def list_datasets():
        """
        Retrieve all datasets accessible to the default user.

        Returns
        -------
        list[Dataset]
            All datasets the current user has access to.
        """
        from m_flow.data.methods import get_datasets

        current_user = await get_seed_user()
        return await get_datasets(current_user.id)

    @staticmethod
    def discover_datasets(directory_path: str) -> list[str]:
        """
        Scan a directory for potential dataset sources.

        Parameters
        ----------
        directory_path : str
            Path to the directory to scan.

        Returns
        -------
        list[str]
            Names of discovered datasets.
        """
        discovered = discover_directory_datasets(directory_path)
        return list(discovered.keys())

    @staticmethod
    async def list_data(dataset_id: str):
        """
        Retrieve all data items in a dataset.

        Parameters
        ----------
        dataset_id : str
            Identifier of the dataset.

        Returns
        -------
        list[Data]
            Data items belonging to the dataset.
        """
        from m_flow.data.methods import get_dataset, fetch_dataset_items

        current_user = await get_seed_user()
        dataset = await get_dataset(current_user.id, dataset_id)
        return await fetch_dataset_items(dataset.id)

    @staticmethod
    async def has_data(dataset_id: str) -> bool:
        """
        Check if a dataset contains any data.

        Parameters
        ----------
        dataset_id : str
            Identifier of the dataset.

        Returns
        -------
        bool
            True if the dataset has data, False otherwise.
        """
        from m_flow.data.methods import get_dataset

        current_user = await get_seed_user()
        dataset = await get_dataset(current_user.id, dataset_id)
        return await has_dataset_data(dataset.id)

    @staticmethod
    async def get_status(dataset_ids: list[UUID]) -> dict:
        """
        Get processing status for datasets.

        Parameters
        ----------
        dataset_ids : list[UUID]
            Dataset identifiers to check.

        Returns
        -------
        dict
            Status information for each dataset.
        """
        return await get_workflow_status(
            dataset_ids,
            workflow_name="memorize_pipeline",
        )

    @staticmethod
    async def delete_dataset(dataset_id: str):
        """
        Remove a dataset and its data.

        Parameters
        ----------
        dataset_id : str
            Identifier of the dataset to delete.
        """
        from m_flow.data.methods import get_dataset, delete_dataset

        current_user = await get_seed_user()
        dataset = await get_dataset(current_user.id, dataset_id)
        return await delete_dataset(dataset)
