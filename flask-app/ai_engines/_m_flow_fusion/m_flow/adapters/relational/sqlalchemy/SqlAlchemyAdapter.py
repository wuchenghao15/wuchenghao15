"""
SQLAlchemy database adapter.

Provides async database operations with SQLite and PostgreSQL support.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from os import path
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy import MetaData, NullPool, Table, delete, inspect, select, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import joinedload

from m_flow.adapters.exceptions import ConceptNotFoundError
from m_flow.data.models.Data import Data
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.infra_utils.run_sync import run_sync
from m_flow.shared.logging_utils import get_logger

from ..ModelBase import Base

logger = get_logger()


class SQLAlchemyAdapter:
    """
    Async database adapter supporting SQLite and PostgreSQL.

    Handles connection management, CRUD operations, schema
    inspection, and optional S3 synchronization for SQLite.
    """

    def __init__(self, connection_string: str):
        """
        Initialize adapter with connection string.

        Args:
            connection_string: SQLAlchemy connection URL.
        """
        self.db_path: str = None
        self.db_uri: str = connection_string

        # Handle SQLite with potential S3 storage
        if "sqlite" in connection_string:
            self._init_sqlite(connection_string)
        else:
            self._init_postgres(connection_string)

        self.sessionmaker = async_sessionmaker(bind=self.engine, expire_on_commit=False)

    def _init_sqlite(self, conn_str: str):
        """Configure SQLite engine with optional S3 sync."""
        prefix, db_path = conn_str.split("///")
        self.db_path = db_path

        if "s3://" in db_path:
            storage = get_file_storage(path.dirname(db_path))
            run_sync(storage.ensure_directory_exists())

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                self.temp_db_file = tmp.name
                conn_str = f"{prefix}///{self.temp_db_file}"

            run_sync(self._pull_from_s3())

        self.engine = create_async_engine(
            conn_str,
            poolclass=NullPool,
            connect_args={"timeout": 30},
        )

    def _init_postgres(self, conn_str: str):
        """Configure PostgreSQL engine with connection pooling."""
        self.engine = create_async_engine(
            conn_str,
            pool_size=10,
            max_overflow=15,
            pool_recycle=300,
            pool_pre_ping=True,
            pool_timeout=300,
        )

    async def sync_to_remote(self) -> None:
        """Sync local SQLite database to S3."""
        if os.getenv("STORAGE_BACKEND", "").lower() != "s3":
            return
        if not hasattr(self, "temp_db_file"):
            return

        from m_flow.shared.files.storage.S3FileStorage import S3FileStorage

        s3 = S3FileStorage("")
        s3.s3.put(self.temp_db_file, self.db_path, recursive=True)

    async def _pull_from_s3(self) -> None:
        """Download SQLite database from S3."""
        from m_flow.shared.files.storage.S3FileStorage import S3FileStorage

        s3 = S3FileStorage("")
        try:
            s3.s3.get(self.db_path, self.temp_db_file, recursive=True)
        except FileNotFoundError:
            pass

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide async database session context.

        Yields:
            AsyncSession for database operations.
        """
        async with self.sessionmaker() as sess:
            try:
                yield sess
            finally:
                await sess.close()

    def get_session(self):
        """Provide sync session context (deprecated)."""
        with self.sessionmaker() as sess:
            try:
                yield sess
            finally:
                sess.close()

    async def get_datasets(self):
        """Retrieve all datasets with their data."""
        from m_flow.data.models import Dataset

        async with self.get_async_session() as sess:
            result = await sess.execute(select(Dataset).options(joinedload(Dataset.data)))
            return result.unique().scalars().all()

    async def create_table(
        self,
        schema_name: str,
        table_name: str,
        table_config: list[dict],
    ):
        """
        Create table with schema.

        Args:
            schema_name: Target schema.
            table_name: New table name.
            table_config: Column definitions.
        """
        fields = ", ".join(f"{c['name']} {c['type']}" for c in table_config)

        async with self.engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name};"))
            await conn.execute(text(f'CREATE TABLE IF NOT EXISTS {schema_name}."{table_name}" ({fields});'))

    async def delete_table(
        self,
        table_name: str,
        schema_name: Optional[str] = "public",
    ):
        """Drop table if exists."""
        async with self.engine.begin() as conn:
            if self.engine.dialect.name == "sqlite":
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}";'))
            else:
                await conn.execute(text(f'DROP TABLE IF EXISTS {schema_name}."{table_name}" CASCADE;'))

    async def insert_data(
        self,
        table_name: str,
        data: list[dict],
        schema_name: Optional[str] = "public",
    ) -> int:
        """
        Insert rows into table.

        Args:
            table_name: Target table.
            data: Rows to insert.
            schema_name: Table schema.

        Returns:
            Number of inserted rows.
        """
        if not data:
            logger.info("No data to insert")
            return 0

        try:
            async with self.engine.begin() as conn:
                if self.engine.dialect.name == "sqlite":
                    await conn.execute(text("PRAGMA foreign_keys=ON"))
                    tbl = await self._load_table(table_name)
                else:
                    tbl = await self._load_table(table_name, schema_name)

                result = await conn.execute(tbl.insert().values(data))
                return result.rowcount
        except Exception as err:
            logger.error("Insert failed: %s", str(err))
            raise

    async def get_schema_list(self) -> List[str]:
        """Get non-system schemas (PostgreSQL only)."""
        if self.engine.dialect.name != "postgresql":
            return []

        async with self.engine.begin() as conn:
            result = await conn.execute(
                text("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'pg_toast', 'information_schema');
            """)
            )
            return [row[0] for row in result.fetchall()]

    async def delete_entity_by_id(
        self,
        table_name: str,
        data_id: UUID,
        schema_name: Optional[str] = "public",
    ):
        """Delete row by ID."""
        async with self.get_async_session() as sess:
            if self.engine.dialect.name == "sqlite":
                await sess.execute(text("PRAGMA foreign_keys = ON;"))

            tbl = await self._load_table(table_name, schema_name)
            await sess.execute(tbl.delete().where(tbl.c.id == data_id))
            await sess.commit()

    async def delete_data_entity(self, data_id: UUID):
        """
        Delete data entity and associated file.

        Only deletes file if no other references exist.
        """
        async with self.get_async_session() as sess:
            if self.engine.dialect.name == "sqlite":
                await sess.execute(text("PRAGMA foreign_keys = ON;"))

            try:
                entity = (await sess.scalars(select(Data).where(Data.id == data_id))).one()
            except (ValueError, NoResultFound) as err:
                raise ConceptNotFoundError(message=f"Entity not found: {err}")

            # Check for other references to same file
            refs = (
                await sess.execute(select(Data.processed_path).where(Data.processed_path == entity.processed_path))
            ).all()

            if len(refs) == 1:
                await self._delete_associated_file(refs[0].processed_path)

            await sess.execute(delete(Data).where(Data.id == data_id))
            await sess.commit()

    async def _delete_associated_file(self, location: str):
        """Remove file if owned by system."""
        cfg = get_storage_config()
        if cfg["data_root_directory"] not in location:
            return

        storage = get_file_storage(cfg["data_root_directory"])
        filename = os.path.basename(location)

        if await storage.file_exists(filename):
            await storage.remove(filename)
        else:
            logger.error("Expected file not found: %s", filename)

    async def _load_table(
        self,
        table_name: str,
        schema_name: Optional[str] = "public",
    ) -> Table:
        """Load table metadata dynamically."""
        async with self.engine.begin() as conn:
            if self.engine.dialect.name == "sqlite":
                await conn.run_sync(Base.metadata.reflect)
                if table_name in Base.metadata.tables:
                    return Base.metadata.tables[table_name]
                raise ConceptNotFoundError(message=f"Table not found: {table_name}")

            meta = MetaData()
            await conn.run_sync(meta.reflect, schema=schema_name)
            full_name = f"{schema_name}.{table_name}"
            if full_name in meta.tables:
                return meta.tables[full_name]
            raise ConceptNotFoundError(message=f"Table not found: {full_name}")

    # Alias
    get_table = _load_table

    async def get_table_names(self) -> List[str]:
        """List all table names in database."""
        names = []
        async with self.engine.begin() as conn:
            if self.engine.dialect.name == "sqlite":
                meta = MetaData()
                await conn.run_sync(meta.reflect)
                names = list(meta.tables.keys())
            else:
                for schema in await self.get_schema_list():
                    meta = MetaData()
                    await conn.run_sync(meta.reflect, schema=schema)
                    names.extend(meta.tables.keys())
                    meta.clear()
        return names

    async def get_data(self, table_name: str, filters: dict = None):
        """Query table with optional filters."""
        async with self.engine.begin() as conn:
            query = f'SELECT * FROM "{table_name}"'
            if filters:
                conditions = " AND ".join(
                    f"{k} IN ({', '.join(f':{k}{i}' for i in range(len(v)))})" if isinstance(v, list) else f"{k} = :{k}"
                    for k, v in filters.items()
                )
                query += f" WHERE {conditions};"
                results = await conn.execute(text(query), filters)
            else:
                results = await conn.execute(text(query + ";"))
            return {r["data_id"]: r["status"] for r in results}

    async def get_all_data_from_table(
        self,
        table_name: str,
        schema: str = "public",
    ):
        """Fetch all rows from table."""
        if not table_name.isidentifier():
            raise ValueError("Invalid table name")
        if schema and not schema.isidentifier():
            raise ValueError("Invalid schema name")

        async with self.get_async_session() as sess:
            tbl = await self._load_table(
                table_name,
                None if self.engine.dialect.name == "sqlite" else schema,
            )
            result = await sess.execute(select(tbl))
            return result.mappings().all()

    async def execute_query(self, query):
        """Execute raw SQL query."""
        async with self.engine.begin() as conn:
            result = await conn.execute(text(query))
            return [dict(row) for row in result]

    async def drop_tables(self):
        """Drop permission-related tables."""
        async with self.engine.begin() as conn:
            try:
                await conn.execute(text("DROP TABLE IF EXISTS group_permission CASCADE"))
                await conn.execute(text("DROP TABLE IF EXISTS permissions CASCADE"))
                logger.debug("Tables dropped successfully")
            except Exception as err:
                logger.error("Drop tables failed: %s", err)
                raise

    async def create_database(self):
        """Create database and tables if needed."""
        if self.engine.dialect.name == "sqlite":
            directory = path.dirname(self.db_path)
            filename = path.basename(self.db_path)
            storage = get_file_storage(directory)
            if not await storage.file_exists(filename):
                await storage.ensure_directory_exists()

        async with self.engine.begin() as conn:
            if Base.metadata.tables:
                await conn.run_sync(Base.metadata.create_all)

    async def delete_database(self):
        """Remove all database content and reinitialize schema."""
        try:
            if self.engine.dialect.name == "sqlite":
                await self.engine.dispose(close=True)
                await asyncio.sleep(2)
                directory = path.dirname(self.db_path)
                filename = path.basename(self.db_path)
                storage = get_file_storage(directory)
                await storage.remove(filename)

                # Clear the LRU cache to force recreation of the engine
                from m_flow.adapters.relational.create_relational_engine import (
                    create_relational_engine,
                )

                create_relational_engine.cache_clear()
                logger.info("Relational engine cache cleared")

                # Reinitialize the engine and recreate tables
                await self._reinitialize_sqlite(directory, filename)
            else:
                async with self.engine.begin() as conn:
                    for schema in ["public", "public_staging"]:
                        meta = MetaData()
                        await conn.run_sync(meta.reflect, schema=schema)
                        for tbl in meta.sorted_tables:
                            await conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{tbl.name}" CASCADE'))
                        meta.clear()
                # Clear engine cache (mirrors SQLite branch behaviour)
                from m_flow.adapters.relational.create_relational_engine import (
                    create_relational_engine,
                )

                create_relational_engine.cache_clear()
                logger.info("Relational engine cache cleared (PostgreSQL)")

                # Recreate tables for PostgreSQL
                await self.create_database()
        except Exception as err:
            logger.error("Database deletion failed: %s", err)
            raise

        logger.info("Database deleted and schema reinitialized")

    async def _reinitialize_sqlite(self, directory: str, filename: str):
        """Reinitialize SQLite database after deletion."""
        conn_str = f"sqlite+aiosqlite:///{directory}/{filename}"
        self.db_path = path.join(directory, filename)

        # Create new engine
        self.engine = create_async_engine(
            conn_str,
            poolclass=NullPool,
            connect_args={"timeout": 30},
        )
        # CRITICAL: Update sessionmaker (used by get_async_session and get_session)
        self.sessionmaker = async_sessionmaker(bind=self.engine, expire_on_commit=False)

        # Ensure directory exists and create tables
        storage = get_file_storage(directory)
        await storage.ensure_directory_exists()

        async with self.engine.begin() as conn:
            if Base.metadata.tables:
                await conn.run_sync(Base.metadata.create_all)

        logger.info("SQLite database reinitialized with fresh schema")

    async def extract_schema(self):
        """
        Extract database schema metadata.

        Returns:
            Dict mapping table names to column/key info.
        """
        async with self.engine.begin() as conn:
            tables = await self.get_table_names()
            schema = {}

            if self.engine.dialect.name == "sqlite":
                schema = await self._extract_sqlite_schema(conn, tables)
            else:
                schema = await self._extract_postgres_schema(conn)

            return schema

    async def _extract_sqlite_schema(self, conn, tables) -> dict:
        """Extract schema from SQLite database."""
        schema = {}
        for tbl_name in tables:
            schema[tbl_name] = {
                "columns": [],
                "primary_key": None,
                "foreign_keys": [],
            }

            cols = await conn.execute(text(f"PRAGMA table_info('{tbl_name}');"))
            for col in cols.fetchall():
                schema[tbl_name]["columns"].append(
                    {
                        "name": col[1],
                        "type": col[2],
                    }
                )
                if col[5] == 1:
                    schema[tbl_name]["primary_key"] = col[1]

            fks = await conn.execute(text(f"PRAGMA foreign_key_list('{tbl_name}');"))
            for fk in fks.fetchall():
                schema[tbl_name]["foreign_keys"].append(
                    {
                        "column": fk[3],
                        "ref_table": fk[2],
                        "ref_column": fk[4],
                    }
                )
        return schema

    async def _extract_postgres_schema(self, conn) -> dict:
        """Extract schema from PostgreSQL database."""
        schema = {}

        for schema_name in await self.get_schema_list():
            tables = await conn.run_sync(lambda c: inspect(c).get_table_names(schema=schema_name))

            for tbl_name in tables:
                key = tbl_name if schema_name == "public" else f"{schema_name}.{tbl_name}"
                schema[key] = {
                    "columns": [],
                    "primary_key": None,
                    "foreign_keys": [],
                }

                def get_details(c, t, s):
                    insp = inspect(c)
                    return (
                        insp.get_columns(t, schema=s),
                        insp.get_pk_constraint(t, schema=s),
                        insp.get_foreign_keys(t, schema=s),
                    )

                cols, pk, fks = await conn.run_sync(get_details, tbl_name, schema_name)

                for col in cols:
                    schema[key]["columns"].append(
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                        }
                    )

                pk_cols = pk.get("constrained_columns", [])
                if pk_cols:
                    schema[key]["primary_key"] = pk_cols[0]

                for fk in fks:
                    for col, ref in zip(
                        fk.get("constrained_columns", []),
                        fk.get("referred_columns", []),
                    ):
                        if col and ref:
                            schema[key]["foreign_keys"].append(
                                {
                                    "column": col,
                                    "ref_table": fk.get("referred_table"),
                                    "ref_column": ref,
                                }
                            )

        return schema
