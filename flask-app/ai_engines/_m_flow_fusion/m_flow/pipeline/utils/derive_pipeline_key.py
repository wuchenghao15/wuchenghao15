"""Pipeline ID generation utility."""

from __future__ import annotations

from uuid import NAMESPACE_OID, UUID, uuid5


def derive_pipeline_key(user_id: UUID, dataset_id: UUID, workflow_name: str) -> UUID:
    """Generate deterministic pipeline ID from user, dataset, and name."""
    seed = f"{user_id}{workflow_name}{dataset_id}"
    return uuid5(NAMESPACE_OID, seed)
