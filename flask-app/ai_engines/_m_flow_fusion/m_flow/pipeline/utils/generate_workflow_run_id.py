"""Pipeline run ID generation utility."""

from __future__ import annotations

from uuid import NAMESPACE_OID, UUID, uuid5


def generate_workflow_run_id(workflow_id: UUID, dataset_id: UUID) -> UUID:
    """Generate deterministic run ID for a pipeline.

    Uses only workflow_id and dataset_id to ensure the same logical
    pipeline always gets the same run_id. This allows INITIATED,
    STARTED, and COMPLETED records to share the same run_id,
    enabling proper status tracking and query filtering.

    Note: This means multiple executions of the same pipeline on
    the same dataset will produce records with the same run_id.
    The get_active_pipeline_runs() query uses ROW_NUMBER() to
    select only the latest status per (dataset_id, workflow_name).

    Args:
        workflow_id: The pipeline's unique identifier.
        dataset_id: The target dataset's unique identifier.

    Returns:
        A deterministic UUID based on the pipeline and dataset IDs.
    """
    seed = f"{workflow_id}_{dataset_id}"
    return uuid5(NAMESPACE_OID, seed)
