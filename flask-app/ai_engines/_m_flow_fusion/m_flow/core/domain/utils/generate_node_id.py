"""
Node identifier generation utilities.
"""

from __future__ import annotations

from uuid import NAMESPACE_OID, UUID, uuid5


def _normalize(text: str) -> str:
    """Convert text to lowercase, remove quotes and spaces."""
    return text.lower().replace(" ", "_").replace("'", "").strip()


def generate_node_id(node_id: str) -> UUID:
    """
    Generate a deterministic UUID from node identifier.

    For context-dependent entities, use generate_contextual_entity_id instead.
    """
    return uuid5(NAMESPACE_OID, _normalize(node_id))


def generate_canonical_entity_name(entity_name: str) -> str:
    """
    Normalize entity name for cross-event matching.

    Used for the canonical_name field on Entity nodes.
    """
    return _normalize(entity_name)


def generate_contextual_entity_id(entity_name: str, context_id: str) -> UUID:
    """
    Generate UUID unique to both entity name and context.

    Prevents entity overwrites across different episodes/events.

    Parameters
    ----------
    entity_name
        Entity display name.
    context_id
        Unique context identifier (episode_id, event_id, etc.).
    """
    combined = f"{_normalize(entity_name)}::{context_id}"
    return uuid5(NAMESPACE_OID, combined)
