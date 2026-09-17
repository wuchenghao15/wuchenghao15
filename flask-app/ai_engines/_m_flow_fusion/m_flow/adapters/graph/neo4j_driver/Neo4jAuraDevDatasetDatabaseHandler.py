"""
Neo4j Aura database handler for multi-tenant deployments.

Creates isolated Neo4j Aura instances per dataset for development/PoC.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import os
from typing import Optional
from uuid import UUID

import requests
from cryptography.fernet import Fernet

from m_flow.adapters.dataset_database_handler import DatasetStoreHandlerInterface
from m_flow.adapters.graph import get_graph_config
from m_flow.auth.models import DatasetStore, User


class Neo4jAuraDevDatasetStoreHandler(DatasetStoreHandlerInterface):
    """
    Development handler for Neo4j Aura multi-tenant setup.

    Creates a new Aura instance per dataset. Connection credentials
    are encrypted and stored in the relational database.

    Note: For production, use a proper secret manager instead
    of storing encrypted credentials in the database.
    """

    _AURA_TOKEN_URL = "https://api.neo4j.io/oauth/token"
    _AURA_INSTANCES_URL = "https://api.neo4j.io/v1/instances"
    _MAX_PROVISION_WAIT = 30  # ~5 minutes with 10s intervals

    @classmethod
    async def create_dataset(
        cls,
        dataset_id: Optional[UUID],
        user: Optional[User],
    ) -> dict:
        """
        Provision new Neo4j Aura instance for dataset.

        Returns:
            Connection config dict for the new instance.

        Raises:
            ValueError: Invalid configuration or missing credentials.
            TimeoutError: Instance did not become ready.
        """
        cfg = get_graph_config()

        if cfg.graph_database_provider != "neo4j":
            raise ValueError("Handler requires Neo4j provider")

        # Load credentials
        client_id = os.environ.get("NEO4J_CLIENT_ID")
        client_secret = os.environ.get("NEO4J_CLIENT_SECRET")
        tenant_id = os.environ.get("NEO4J_TENANT_ID")

        if not all([client_id, client_secret, tenant_id]):
            raise ValueError("NEO4J_CLIENT_ID, NEO4J_CLIENT_SECRET, NEO4J_TENANT_ID required")

        # Encryption setup
        enc_key = cls._derive_encryption_key()
        cipher = Fernet(enc_key)

        # Get OAuth token
        token = cls._fetch_aura_token(client_id, client_secret)

        # Create instance
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        payload = {
            "version": "5",
            "region": "europe-west1",
            "memory": "1GB",
            "name": str(dataset_id)[:29],  # Aura name limit
            "type": "professional-db",
            "tenant_id": tenant_id,
            "cloud_provider": "gcp",
        }

        resp = requests.post(cls._AURA_INSTANCES_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()["data"]

        instance_id = data["id"]
        await cls._wait_for_ready(instance_id, headers)

        # Encrypt password
        enc_password = cipher.encrypt(data["password"].encode()).decode()

        return {
            "graph_database_name": "neo4j",  # Aura requires 'neo4j'
            "graph_database_url": data["connection_url"],
            "graph_database_provider": "neo4j",
            "graph_database_key": token,
            "graph_dataset_database_handler": "neo4j_aura_dev",
            "graph_database_connection_info": {
                "graph_database_username": data["username"],
                "graph_database_password": enc_password,
            },
        }

    @classmethod
    async def resolve_dataset_connection_info(
        cls,
        dataset_database: DatasetStore,
    ) -> DatasetStore:
        """Decrypt connection credentials."""
        enc_key = cls._derive_encryption_key()
        cipher = Fernet(enc_key)

        conn_info = dataset_database.graph_database_connection_info
        enc_pwd = conn_info["graph_database_password"].encode()

        conn_info["graph_database_password"] = cipher.decrypt(enc_pwd).decode()
        return dataset_database

    @classmethod
    async def delete_dataset(cls, dataset_database: DatasetStore):
        """Delete Aura instance (not yet implemented)."""
        pass

    @classmethod
    def _derive_encryption_key(cls) -> bytes:
        """Derive Fernet key from env variable."""
        raw_key = os.environ.get("NEO4J_ENCRYPTION_KEY", "test_key")
        return base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode()).digest())

    @classmethod
    def _fetch_aura_token(cls, client_id: str, client_secret: str) -> str:
        """Get OAuth token from Aura API."""
        resp = requests.post(
            cls._AURA_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    @classmethod
    async def _wait_for_ready(cls, instance_id: str, headers: dict) -> None:
        """Poll until instance is running."""
        url = f"{cls._AURA_INSTANCES_URL}/{instance_id}"

        for _ in range(cls._MAX_PROVISION_WAIT):
            resp = requests.get(url, headers=headers)
            status = resp.json()["data"]["status"]

            if status.lower() == "running":
                return

            await asyncio.sleep(10)

        raise TimeoutError(f"Neo4j instance {instance_id} not ready after 5 minutes")
