import os
import modal
import asyncio
from sqlalchemy.exc import OperationalError, DBAPIError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from mflow_workers.app import app
from mflow_workers.signal import QueueSignal
from mflow_workers.modal_image import image
from mflow_workers.queues import add_memory_nodes_queue

from m_flow.shared.logging_utils import get_logger
from m_flow.adapters.vector import get_vector_provider

logger = get_logger("memory_node_saving_worker")


class VectorDatabaseDeadlockError(Exception):
    message = "A deadlock occurred while trying to add data points to the vector database."


def is_deadlock_error(error):
    # SQLAlchemy-wrapped asyncpg
    try:
        import asyncpg

        if isinstance(error.orig, asyncpg.exceptions.DeadlockDetectedError):
            return True
    except ImportError:
        pass

    # PostgreSQL: SQLSTATE 40P01 = deadlock_detected
    if hasattr(error.orig, "pgcode") and error.orig.pgcode == "40P01":
        return True

    # SQLite: It doesn't support real deadlocks but may simulate them as "database is locked"
    if "database is locked" in str(error.orig).lower():
        return True

    return False


secret_name = os.environ.get("MODAL_SECRET_NAME", "distributed_m_flow")


@app.function(
    retries=3,
    image=image,
    timeout=86400,
    max_containers=10,
    secrets=[modal.Secret.from_name(secret_name)],
)
async def memory_node_saving_worker():
    print("Started processing of data points; starting vector engine queue.")
    vector_engine = get_vector_provider()
    # Defines how many data packets do we glue together from the modal queue before embedding call and ingestion
    BATCH_SIZE = 25
    stop_seen = False

    while True:
        if stop_seen:
            print("Finished processing all data points; stopping vector engine queue consumer.")
            return True

        if await add_memory_nodes_queue.len.aio() != 0:
            try:
                print("Remaining elements in queue:")
                print(await add_memory_nodes_queue.len.aio())

                # collect batched requests
                batched_points = {}
                for _ in range(min(BATCH_SIZE, await add_memory_nodes_queue.len.aio())):
                    add_memory_nodes_request = await add_memory_nodes_queue.get.aio(block=False)

                    if not add_memory_nodes_request:
                        continue

                    if add_memory_nodes_request == QueueSignal.STOP:
                        await add_memory_nodes_queue.put.aio(QueueSignal.STOP)
                        stop_seen = True
                        break

                    if len(add_memory_nodes_request) == 2:
                        collection_name, memory_nodes = add_memory_nodes_request
                        if collection_name not in batched_points:
                            batched_points[collection_name] = []
                        batched_points[collection_name].extend(memory_nodes)
                    else:
                        print("M-Flow worker received malformed or empty save request.")

                if batched_points:
                    for collection_name, memory_nodes in batched_points.items():
                        print(f"Adding {len(memory_nodes)} data points to '{collection_name}' collection.")

                        @retry(
                            retry=retry_if_exception_type(VectorDatabaseDeadlockError),
                            stop=stop_after_attempt(3),
                            wait=wait_exponential(multiplier=2, min=1, max=6),
                        )
                        async def persist_memory_nodes():
                            try:
                                await vector_engine.create_memory_nodes(
                                    collection_name, memory_nodes, distributed=False
                                )
                            except DBAPIError as error:
                                if is_deadlock_error(error):
                                    raise VectorDatabaseDeadlockError()
                            except OperationalError as error:
                                if is_deadlock_error(error):
                                    raise VectorDatabaseDeadlockError()

                        await persist_memory_nodes()
                        print(f"Finished adding data points to '{collection_name}'.")

            except modal.exception.DeserializationError as error:
                logger.error(f"Deserialization error: {str(error)}")
                continue

        else:
            print("M-Flow worker queue empty — entering idle wait.")
            await asyncio.sleep(5)
