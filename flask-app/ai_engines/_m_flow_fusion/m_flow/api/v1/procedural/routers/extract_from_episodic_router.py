"""
API endpoint for extracting procedural memories from existing episodic memories.

Creates a pipeline run record for Dashboard visibility, then executes
extraction in a background task. The pipeline run status is updated
as STARTED → COMPLETED/ERRORED.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from m_flow.auth.methods import get_authenticated_user
from m_flow.auth.models import User
from m_flow.shared.logging_utils import get_logger

logger = get_logger("extract_from_episodic_api")

PIPELINE_NAME = "procedural_extraction_pipeline"


class ExtractFromEpisodicRequest(BaseModel):
    dataset_id: Optional[UUID] = Field(
        default=None,
        description="Dataset ID to extract from. If None, processes all accessible datasets.",
    )
    limit: int = Field(default=100, ge=1, le=1000)
    force_reprocess: bool = Field(default=False)


class ExtractFromEpisodicResponse(BaseModel):
    success: bool
    message: str
    datasets_submitted: int = 0


def get_extract_from_episodic_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/extract-from-episodic",
        response_model=ExtractFromEpisodicResponse,
        summary="Extract procedural memories from existing episodic memories",
    )
    async def extract_from_episodic(
        request: ExtractFromEpisodicRequest,
        user: User = Depends(get_authenticated_user),
    ) -> ExtractFromEpisodicResponse:
        try:
            from m_flow.data.methods import get_authorized_existing_datasets
            from m_flow.context_global_variables import set_db_context
            from m_flow.memory.procedural.write_procedural_from_episodic import (
                extract_procedural_from_episodic,
            )
            from m_flow.adapters.relational import get_db_adapter
            from m_flow.pipeline.models import WorkflowRun, RunStatus

            authorized_datasets = await get_authorized_existing_datasets(
                [request.dataset_id] if request.dataset_id else [],
                "read",
                user,
            )

            if not authorized_datasets:
                return ExtractFromEpisodicResponse(
                    success=True,
                    message="No authorized datasets available",
                    datasets_submitted=0,
                )

            dataset_names = [ds.name for ds in authorized_datasets]

            logger.info(
                f"[extract_from_episodic] User {user.id} starting for "
                f"{len(authorized_datasets)} datasets: {dataset_names}"
            )

            async def _run_extraction():
                total_analyzed = 0
                total_procedures = 0
                total_written = 0

                for dataset in authorized_datasets:
                    run_id = uuid4()
                    pipe_id = uuid4()
                    ds_id = dataset.id if isinstance(dataset.id, UUID) else UUID(str(dataset.id))
                    engine = get_db_adapter()

                    try:
                        async with engine.get_async_session() as sess:
                            sess.add(
                                WorkflowRun(
                                    workflow_run_id=run_id,
                                    workflow_name=PIPELINE_NAME,
                                    workflow_id=pipe_id,
                                    status=RunStatus.DATASET_PROCESSING_STARTED,
                                    dataset_id=ds_id,
                                    run_detail={
                                        "data": f"Extracting procedures from {dataset.name}",
                                        "current_step": "Extracting procedures",
                                    },
                                )
                            )
                            await sess.commit()
                    except Exception as db_err:
                        logger.warning(f"[extract_from_episodic] Pipeline record write failed: {db_err}")

                    try:
                        await set_db_context(dataset.id, dataset.owner_id)

                        result = await extract_procedural_from_episodic(
                            limit=request.limit,
                            dataset_id=str(dataset.id),
                            force_reprocess=request.force_reprocess,
                            authorized_dataset_ids=[str(dataset.id)],
                        )

                        analyzed = result.get("episodes_analyzed", 0)
                        written = result.get("nodes_written", 0)
                        nodes = result.get("result", [])
                        procs = len(
                            [n for n in nodes if hasattr(n, "__class__") and n.__class__.__name__ == "Procedure"]
                        )

                        total_analyzed += analyzed
                        total_procedures += procs
                        total_written += written

                        try:
                            async with engine.get_async_session() as sess:
                                sess.add(
                                    WorkflowRun(
                                        workflow_run_id=run_id,
                                        workflow_name=PIPELINE_NAME,
                                        workflow_id=pipe_id,
                                        status=RunStatus.DATASET_PROCESSING_COMPLETED,
                                        dataset_id=ds_id,
                                        run_detail={"episodes": analyzed, "procedures": procs, "nodes": written},
                                    )
                                )
                                await sess.commit()
                        except Exception as db_err:
                            logger.warning(f"[extract_from_episodic] Pipeline complete record failed: {db_err}")

                    except Exception as e:
                        logger.error(f"[extract_from_episodic] Failed for {dataset.name}: {e}")
                        try:
                            async with engine.get_async_session() as sess:
                                sess.add(
                                    WorkflowRun(
                                        workflow_run_id=run_id,
                                        workflow_name=PIPELINE_NAME,
                                        workflow_id=pipe_id,
                                        status=RunStatus.DATASET_PROCESSING_ERRORED,
                                        dataset_id=ds_id,
                                        run_detail={"error": str(e)},
                                    )
                                )
                                await sess.commit()
                        except Exception as db_err:
                            logger.warning(f"[extract_from_episodic] Pipeline error record failed: {db_err}")

                logger.info(
                    f"[extract_from_episodic] Done: analyzed={total_analyzed}, "
                    f"procedures={total_procedures}, nodes={total_written}"
                )

            asyncio.get_event_loop().create_task(_run_extraction())

            return ExtractFromEpisodicResponse(
                success=True,
                message=f"Procedural extraction started for {len(authorized_datasets)} dataset(s): {', '.join(dataset_names)}",
                datasets_submitted=len(authorized_datasets),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"[extract_from_episodic] Failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
