"""
Neptune Analytics utility functions.

Provides helpers for URL parsing, validation, configuration building,
and error formatting for AWS Neptune Analytics connections.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from m_flow.shared.logging_utils import get_logger

_log = get_logger("NeptuneUtils")

# AWS region pattern: us-east-1, eu-west-2, etc.
_REGION_PATTERN = re.compile(r"^[a-z]{2,3}-[a-z]+-\d+$")

# Graph ID pattern: alphanumeric with hyphens, 1-63 chars
_GRAPH_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}$")

# Default settings
_DEFAULT_REGION = "us-east-1"
_DEFAULT_TIMEOUT = 300  # 5 minutes


def parse_neptune_url(url: str) -> tuple[str, str]:
    """
    Extract graph ID and region from Neptune URL.

    Format: neptune-graph://<GRAPH_ID>?region=<REGION>

    Args:
        url: Neptune Analytics URL.

    Returns:
        Tuple of (graph_id, region).

    Raises:
        ValueError: Invalid URL format.
    """
    try:
        parsed = urlparse(url)

        if parsed.scheme != "neptune-graph":
            raise ValueError(f"Expected scheme 'neptune-graph', got '{parsed.scheme}'")

        graph_id = parsed.hostname or parsed.path.lstrip("/")
        if not graph_id:
            raise ValueError("Unable to extract Neptune graph identifier from the provided URL")

        # Extract region from query string
        region = _DEFAULT_REGION
        if parsed.query:
            params = dict(p.split("=", 1) for p in parsed.query.split("&") if "=" in p)
            region = params.get("region", region)

        return graph_id, region

    except Exception as e:
        raise ValueError(f"Invalid Neptune URL '{url}': {e}") from e


def validate_graph_id(graph_id: str) -> bool:
    """Check if graph ID follows AWS naming rules."""
    return bool(graph_id and _GRAPH_ID_PATTERN.match(graph_id))


def validate_aws_region(region: str) -> bool:
    """Check if region follows AWS format."""
    return bool(region and _REGION_PATTERN.match(region))


def build_neptune_config(
    graph_id: str,
    region: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None,
    **extra,
) -> dict[str, Any]:
    """
    Assemble Neptune connection configuration.

    Args:
        graph_id: Neptune Analytics graph identifier.
        region: AWS region.
        aws_access_key_id: AWS access key.
        aws_secret_access_key: AWS secret key.
        aws_session_token: Session token for temporary credentials.
        **extra: Additional config parameters.

    Returns:
        Configuration dictionary.
    """
    cfg: dict[str, Any] = {
        "graph_id": graph_id,
        "service_name": "neptune-graph",
    }

    if region:
        cfg["region"] = region
    if aws_access_key_id:
        cfg["aws_access_key_id"] = aws_access_key_id
    if aws_secret_access_key:
        cfg["aws_secret_access_key"] = aws_secret_access_key
    if aws_session_token:
        cfg["aws_session_token"] = aws_session_token

    cfg.update(extra)
    return cfg


def get_neptune_endpoint_url(graph_id: str, region: str) -> str:
    """Build Neptune Analytics API endpoint URL."""
    return f"https://neptune-graph.{region}.amazonaws.com/graphs/{graph_id}"


def format_neptune_error(error: Exception) -> str:
    """Convert Neptune exceptions to user-friendly messages."""
    msg = str(error)

    mappings = {
        "AccessDenied": "Access denied. Check AWS credentials and permissions.",
        "GraphNotFound": "Graph not found. Verify graph ID and region.",
        "InvalidParameter": "Invalid parameter. Check request parameters.",
        "ThrottlingException": "Request throttled. Retry with backoff.",
        "InternalServerError": "Internal error. Try again later.",
    }

    for err_type, friendly in mappings.items():
        if err_type in msg:
            return f"{friendly} (Original: {msg})"

    return msg


def get_default_query_timeout() -> int:
    """Return default query timeout in seconds."""
    return _DEFAULT_TIMEOUT


def get_default_connection_config() -> dict[str, Any]:
    """Return default connection settings."""
    return {
        "query_timeout": _DEFAULT_TIMEOUT,
        "max_retries": 3,
        "retry_delay": 1.0,
        "preferred_query_language": "openCypher",
    }
