"""
Remote Kùzu graph database adapter via REST API.

Provides async interface to Kùzu databases hosted on remote servers,
communicating via HTTP REST API instead of embedded database.
"""

from __future__ import annotations

import asyncio
import atexit
import json
import weakref
from typing import TYPE_CHECKING, Any, List, Optional, Tuple
from uuid import UUID

import aiohttp

from m_flow.adapters.graph.kuzu.adapter import KuzuAdapter
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.utils import create_secure_ssl_context

if TYPE_CHECKING:
    pass

_log = get_logger()

# Weak reference set to track active instances for cleanup
_active_instances: weakref.WeakSet = weakref.WeakSet()


def _shutdown_cleanup():
    """Cleanup handler for application shutdown."""
    pending_sessions = []

    for inst in _active_instances:
        session = getattr(inst, "_http_session", None)
        if session and not session.closed:
            pending_sessions.append(session)

    if not pending_sessions:
        return

    try:
        loop = asyncio.get_event_loop()

        if loop.is_running():
            for s in pending_sessions:
                loop.create_task(s.close())
        else:

            async def _close_all():
                for s in pending_sessions:
                    await s.close()

            loop.run_until_complete(_close_all())

    except Exception as err:
        _log.debug(f"Shutdown cleanup error: {err}")


# Register shutdown handler
atexit.register(_shutdown_cleanup)


class _UUIDJsonEncoder(json.JSONEncoder):
    """JSON encoder with UUID support."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class RemoteKuzuAdapter(KuzuAdapter):
    """
    Remote Kùzu database adapter using REST API.

    Inherits from KuzuAdapter but overrides query execution to use
    HTTP requests instead of embedded database connections.
    """

    def __init__(self, api_url: str, username: str, password: str):
        """
        Initialize remote adapter.

        Args:
            api_url: Base URL for Kùzu REST API
            username: Authentication username
            password: Authentication password
        """
        # Initialize parent with placeholder path
        super().__init__("/tmp/kuzu_remote_placeholder")

        self._api_url = api_url.rstrip("/")
        self._username = username
        self._password = password
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._schema_ready = False

        # Register for cleanup tracking
        _active_instances.add(self)

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    # =========================================================================
    # Session Management
    # =========================================================================

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._http_session is None or self._http_session.closed:
            ssl_ctx = create_secure_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            self._http_session = aiohttp.ClientSession(connector=connector)
        return self._http_session

    async def close(self):
        """Close HTTP session."""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

    def __del__(self):
        """Destructor - best effort session cleanup."""
        session = getattr(self, "_http_session", None)
        if not session or session.closed:
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(session.close())
            else:
                loop.run_until_complete(session.close())
        except Exception:
            pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

    # =========================================================================
    # HTTP Communication
    # =========================================================================

    async def _make_request(self, endpoint: str, data: dict) -> dict:
        """
        Execute POST request to API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/query")
            data: Request payload

        Returns:
            Parsed JSON response
        """
        url = f"{self._api_url}{endpoint}"
        session = await self._get_session()

        try:
            payload = json.dumps(data, cls=_UUIDJsonEncoder)
            headers = {"Content-Type": "application/json"}

            async with session.post(url, data=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    _log.error(f"API error {resp.status}: {error_text}\nRequest: {data}")
                    raise aiohttp.ClientResponseError(
                        resp.request_info,
                        resp.history,
                        status=resp.status,
                        message=error_text,
                    )
                return await resp.json()

        except aiohttp.ClientError as err:
            _log.error(f"HTTP request failed: {err}")
            _log.error(f"Request data: {data}")
            raise

    # =========================================================================
    # Query Execution
    # =========================================================================

    async def query(self, query: str, params: Optional[dict] = None) -> List[Tuple]:
        """
        Execute Cypher query via REST API.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result tuples
        """
        try:
            # Ensure schema exists
            if not self._schema_ready:
                await self._ensure_schema()

            resp = await self._make_request(
                "/query",
                {"query": query, "parameters": params or {}},
            )

            # Parse response rows
            rows = []
            raw_data = resp.get("data", [])

            for row in raw_data:
                processed = []
                for val in row:
                    processed.append(self._process_value(val))
                rows.append(tuple(processed))

            return rows

        except Exception as err:
            _log.error(f"Query failed: {err}")
            _log.error(f"Query: {query}")
            _log.error(f"Params: {params}")
            raise

    def _process_value(self, val: Any) -> Any:
        """Process individual value from response."""
        if not isinstance(val, dict):
            return val

        if "properties" not in val:
            return val

        try:
            nested = json.loads(val["properties"])
            result = {k: v for k, v in val.items() if k != "properties"}
            result.update(nested)
            return result
        except (json.JSONDecodeError, TypeError):
            return val

    # =========================================================================
    # Schema Management
    # =========================================================================

    async def _ensure_schema(self):
        """Initialize schema if not already done."""
        if self._schema_ready:
            return

        try:
            if await self._schema_exists():
                self._schema_ready = True
                _log.info("Schema already exists")
            else:
                await self._create_tables()
        except Exception as err:
            _log.error(f"Schema initialization failed: {err}")
            raise

    async def _schema_exists(self) -> bool:
        """Check if Node table exists."""
        try:
            resp = await self._make_request(
                "/query",
                {
                    "query": "MATCH (n:Node) RETURN COUNT(n) > 0",
                    "parameters": {},
                },
            )
            data = resp.get("data", [])
            return bool(data and data[0][0])
        except Exception as err:
            _log.error(f"Schema check failed: {err}")
            return False

    async def _create_tables(self):
        """Create Node and EDGE tables."""
        try:
            # Create Node table
            node_ddl = """
                CREATE NODE TABLE IF NOT EXISTS Node (
                    id STRING,
                    name STRING,
                    type STRING,
                    properties STRING,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    PRIMARY KEY (id)
                )
            """

            try:
                await self._make_request(
                    "/query",
                    {"query": node_ddl, "parameters": {}},
                )
            except aiohttp.ClientResponseError as err:
                if "already exists" not in str(err):
                    raise

            # Create EDGE table
            edge_ddl = """
                CREATE REL TABLE IF NOT EXISTS EDGE (
                    FROM Node TO Node,
                    relationship_name STRING,
                    properties STRING,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """

            try:
                await self._make_request(
                    "/query",
                    {"query": edge_ddl, "parameters": {}},
                )
            except aiohttp.ClientResponseError as err:
                if "already exists" not in str(err):
                    raise

            self._schema_ready = True
            _log.info("Schema tables created")

        except Exception as err:
            _log.error(f"Table creation failed: {err}")
            raise

    # Compatibility alias
    @property
    def _session(self):
        return self._http_session

    @_session.setter
    def _session(self, value):
        self._http_session = value

    @property
    def _schema_initialized(self):
        return self._schema_ready

    @_schema_initialized.setter
    def _schema_initialized(self, value):
        self._schema_ready = value

    async def _initialize_schema(self):
        """Compatibility alias for _ensure_schema."""
        await self._ensure_schema()

    async def _check_schema_exists(self) -> bool:
        """Compatibility alias for _schema_exists."""
        return await self._schema_exists()


# Module-level alias for encoder
UUIDEncoder = _UUIDJsonEncoder
