from __future__ import annotations

import uuid

from .generate_edge_name import generate_edge_name

# UUID namespace used for deterministic edge identifier derivation.
# NAMESPACE_OID is the ISO OID namespace defined in RFC 4122.
_NAMESPACE = uuid.NAMESPACE_OID


def generate_edge_id(edge_id: str) -> uuid.UUID:
    """Produce a deterministic UUID-v5 for the given edge identifier.

    The raw *edge_id* string is first passed through
    :func:`generate_edge_name` for canonicalisation, then hashed with
    the OID namespace to yield a stable, collision-resistant UUID.
    """
    canonical = generate_edge_name(edge_id)
    return uuid.uuid5(_NAMESPACE, canonical)
