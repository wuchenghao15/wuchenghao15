"""
Bearer token transport for API authentication.

Configures FastAPI-Users BearerTransport for API key endpoints.
"""

from __future__ import annotations

from fastapi_users.authentication import BearerTransport

_TOKEN_ENDPOINT = "/api/v1/auth/token"
_TRANSPORT_NAME = "bearer"

# Transport instance for API bearer authentication
api_bearer_transport = BearerTransport(tokenUrl=_TOKEN_ENDPOINT)
api_bearer_transport.name = _TRANSPORT_NAME
