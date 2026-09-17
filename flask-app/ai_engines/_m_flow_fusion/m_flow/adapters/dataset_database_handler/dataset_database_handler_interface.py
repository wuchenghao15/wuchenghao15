"""Contract for per-dataset database lifecycle management.

Implementations provision, resolve, and tear down isolated graph or
vector stores so that each dataset can be backed by its own database
in multi-tenant deployments.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from m_flow.auth.models.DatasetStore import DatasetStore
from m_flow.auth.models.User import User


class DatasetStoreHandlerInterface(ABC):
    """Protocol that dataset-scoped database handlers must satisfy.

    A handler manages three lifecycle phases for the backing store of
    every dataset:

    1. **Provisioning** — ``create_dataset`` allocates (or registers) a
       new database and returns the connection metadata that will be
       persisted in the relational catalogue.
    2. **Resolution** — ``resolve_dataset_connection_info`` translates
       stored metadata (which may contain only secret references) into
       concrete, short-lived connection parameters at connect time.
    3. **Teardown** — ``delete_dataset`` deprovisions or marks the
       backing store as retired.
    """

    __slots__ = ()

    @classmethod
    @abstractmethod
    async def create_dataset(
        cls,
        dataset_id: Optional[UUID],
        user: Optional[User],
    ) -> dict:
        """Provision a backing store for *dataset_id* and return its
        connection descriptor.

        The returned ``dict`` is written verbatim into a
        :class:`DatasetStore` row and later fed to
        :meth:`resolve_dataset_connection_info` at connection time.

        Prefer returning opaque secret references (vault paths, ARN
        identifiers, etc.) rather than plaintext credentials.

        Parameters
        ----------
        dataset_id:
            UUID of the dataset being created.  May be ``None`` when
            the caller defers ID assignment.
        user:
            The owning principal, available for tenant-aware backends.

        Returns
        -------
        dict
            Serialisable connection/resolution metadata.
        """
        ...

    @classmethod
    async def resolve_dataset_connection_info(
        cls,
        dataset_database: DatasetStore,
    ) -> DatasetStore:
        """Materialise runtime connection details from stored metadata.

        Invoked immediately before a connection is opened.  The default
        implementation is a pass-through — subclasses that store only
        secret references should override this to resolve them into
        short-lived credentials.

        **Important**: resolved credentials must never be flushed back
        to the relational catalogue; they exist only for the lifetime of
        the connection attempt.

        When separate graph and vector handlers are chained, each
        handler mutates only the fields it owns and passes the updated
        object to the next handler in line.

        Parameters
        ----------
        dataset_database:
            Persisted catalogue row carrying the stored metadata.

        Returns
        -------
        DatasetStore
            The same (or a copy of) *dataset_database* with concrete
            connection fields populated.
        """
        return dataset_database

    @classmethod
    @abstractmethod
    async def delete_dataset(
        cls,
        dataset_database: DatasetStore,
    ) -> None:
        """Deprovision the backing store described by *dataset_database*.

        Implementations should handle both hard deletion and soft
        retirement depending on the backend's capabilities.

        Parameters
        ----------
        dataset_database:
            Catalogue row carrying the connection metadata of the
            database to remove.
        """
        ...
