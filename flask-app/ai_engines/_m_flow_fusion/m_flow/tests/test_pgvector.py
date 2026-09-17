"""
PGVector Integration Test Module
================================
m_flow.tests.test_pgvector

Tests PostgreSQL with pgvector extension as vector storage backend:
- Vector storage and similarity search
- Integration with relational PostgreSQL database
- Multi-mode search operations
- Data lifecycle and cleanup
"""

import pathlib
import hashlib
import os

import m_flow
from m_flow.shared.files.storage import get_storage_config
from m_flow.search.operations import get_history
from m_flow.shared.logging_utils import get_logger
from m_flow.data.models import Data
from m_flow.search.types import RecallMode
from m_flow.auth.methods import get_seed_user

_logger = get_logger()


async def verify_file_lifecycle(text_content: str, external_path: str):
    """
    Tests file deletion behavior for m_flow data entries.

    Verifies:
    1. m_flow-generated files are removed with data entities
    2. External files remain after data entity deletion
    """
    from sqlalchemy import select
    from m_flow.adapters.relational import get_db_adapter

    db = get_db_adapter()

    # Test: Internal file cleanup
    async with db.get_async_session() as session:
        digest = hashlib.md5(text_content.encode("utf-8")).hexdigest()
        record = (await session.scalars(select(Data).where(Data.content_hash == digest))).one()

        path = record.processed_path.replace("file://", "")
        assert os.path.isfile(path), f"Missing: {record.processed_path}"

        await db.delete_data_entity(record.id)
        assert not os.path.exists(path), f"Not deleted: {record.processed_path}"

    # Test: External file preservation
    async with db.get_async_session() as session:
        external_uri = f"file://{external_path}"
        record = (await session.scalars(select(Data).where(Data.source_path == external_uri))).one()

        path = record.source_path.replace("file://", "")
        assert os.path.isfile(path), f"Missing: {record.source_path}"

        await db.delete_data_entity(record.id)
        assert os.path.exists(path), f"External deleted: {record.source_path}"


async def verify_document_access(dataset: str):
    """Tests document retrieval for search with access control."""
    from m_flow.auth.permissions.methods import get_document_ids_for_user

    user = await get_seed_user()

    # Dataset-filtered retrieval
    filtered = await get_document_ids_for_user(user.id, [dataset])
    assert len(filtered) == 1, f"Expected 1 in dataset, got {len(filtered)}"

    # Full access retrieval
    all_docs = await get_document_ids_for_user(user.id)
    assert len(all_docs) == 2, f"Expected 2 total, got {len(all_docs)}"


async def verify_unlimited_search():
    """Confirms vector search without limits returns all results."""
    test_dir = pathlib.Path(__file__).parent

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await m_flow.add(str(test_dir / "test_data" / "Quantum_computers.txt"))
    await m_flow.add(str(test_dir / "test_data" / "Natural_language_processing.txt"))
    await m_flow.memorize()

    from m_flow.adapters.vector import get_vector_provider

    vec = get_vector_provider()

    query = "Tell me about Quantum computers"
    embedding = (await vec.embedding_engine.embed_text([query]))[0]

    results = await vec.search(
        collection_name="Entity_name",
        query_vector=embedding,
        limit=None,
    )

    # Verify no hidden limits (common: 5, 10, 15)
    assert len(results) > 15, f"Only {len(results)} results returned"


# Sample quantum computing content for testing
_QUANTUM_SAMPLE = """A quantum computer is a computer that takes advantage of quantum mechanical phenomena.
At small scales, physical matter exhibits properties of both particles and waves, and quantum computing leverages this behavior, specifically quantum superposition and entanglement, using specialized hardware that supports the preparation and manipulation of quantum states.
Classical physics cannot explain the operation of these quantum devices, and a scalable quantum computer could perform some calculations exponentially faster (with respect to input size scaling) than any modern "classical" computer. In particular, a large-scale quantum computer could break widely used encryption schemes and aid physicists in performing physical simulations; however, the current state of the technology is largely experimental and impractical, with several obstacles to useful applications. Moreover, scalable quantum computers do not hold promise for many practical tasks, and for many important tasks quantum speedups are proven impossible.
The basic unit of information in quantum computing is the qubit, similar to the bit in traditional digital electronics. Unlike a classical bit, a qubit can exist in a superposition of its two "basis" states. When measuring a qubit, the result is a probabilistic output of a classical bit, therefore making quantum computers nondeterministic in general. If a quantum computer manipulates the qubit in a particular way, wave interference effects can amplify the desired measurement results. The design of quantum algorithms involves creating procedures that allow a quantum computer to perform calculations efficiently and quickly.
Physically engineering high-quality qubits has proven challenging. If a physical qubit is not sufficiently isolated from its environment, it suffers from quantum decoherence, introducing noise into calculations. Paradoxically, perfectly isolating qubits is also undesirable because quantum computations typically need to initialize qubits, perform controlled qubit interactions, and measure the resulting quantum states. Each of those operations introduces errors and suffers from noise, and such inaccuracies accumulate.
In principle, a non-quantum (classical) computer can solve the same computational problems as a quantum computer, given enough time. Quantum advantage comes in the form of time complexity rather than computability, and quantum complexity theory shows that some quantum algorithms for carefully selected tasks require exponentially fewer computational steps than the best known non-quantum algorithms. Such tasks can in theory be solved on a large-scale quantum computer whereas classical computers would not finish computations in any reasonable amount of time. However, quantum speedup is not universal or even typical across computational tasks, since basic tasks such as sorting are proven to not allow any asymptotic quantum speedup. Claims of quantum supremacy have drawn significant attention to the discipline, but are demonstrated on contrived tasks, while near-term practical use cases remain limited.
"""


async def main():
    """
    Primary test runner for PGVector integration.

    Configures PostgreSQL+pgvector and validates full functionality.
    """
    # Configure pgvector as vector backend
    m_flow.config.set_vector_db_config(
        {
            "vector_db_url": "",
            "vector_db_key": "",
            "vector_db_provider": "pgvector",
        }
    )

    # Configure PostgreSQL as relational backend
    m_flow.config.set_relational_db_config(
        {
            "db_path": "",
            "db_name": "mflow_store",
            "db_host": "127.0.0.1",
            "db_port": "5432",
            "db_username": "m_flow",
            "db_password": "m_flow",
            "db_provider": "postgres",
        }
    )

    # Initialize storage paths
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_pgvector").resolve()
    system_dir = (test_root / ".mflow/system" / "test_pgvector").resolve()

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Clean start
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare test data
    nlp_ds = "natural_language"
    quantum_ds = "quantum"

    nlp_file = test_root / "test_data" / "Natural_language_processing.txt"
    await m_flow.add([str(nlp_file)], nlp_ds)
    await m_flow.add([_QUANTUM_SAMPLE], quantum_ds)

    await m_flow.memorize([quantum_ds, nlp_ds])

    # Validate document access
    await verify_document_access(nlp_ds)

    # Search tests
    from m_flow.adapters.vector import get_vector_provider

    vec = get_vector_provider()

    concept_hit = (await vec.search("Entity_name", "Quantum computer"))[0]
    concept_text = concept_hit.payload["text"]

    # TRIPLET_COMPLETION mode
    completion = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=concept_text,
    )
    assert len(completion) > 0, "TRIPLET_COMPLETION returned empty"
    _logger.info("Graph completion: %d results", len(completion))

    # EPISODIC mode
    episodic = await m_flow.search(
        query_type=RecallMode.EPISODIC,
        query_text=concept_text,
        datasets=[quantum_ds],
    )
    _logger.info("Episodic: %d results", len(episodic))

    # Filtered completion
    filtered = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=concept_text,
    )
    assert len(filtered) > 0, "Filtered completion empty"

    # History validation
    user = await get_seed_user()
    history = await get_history(user.id)
    assert len(history) > 0, "History should not be empty"

    # File lifecycle test
    await verify_file_lifecycle(_QUANTUM_SAMPLE, str(nlp_file))

    # Cleanup verification
    await m_flow.prune.prune_data()
    storage_cfg = get_storage_config()
    assert not os.path.isdir(storage_cfg["data_root_directory"]), "Data dir exists"

    await m_flow.prune.prune_system(metadata=True)
    # PGVector shares the PostgreSQL instance with the relational ORM.
    # After prune, ORM metadata tables (~30) are recreated by create_all(),
    # but all vector collection tables should be dropped.
    for coll in ["Entity_name", "Episode_summary", "ContentFragment_text"]:
        assert not await vec.has_collection(coll), f"Vector collection '{coll}' still exists after cleanup"

    # Unlimited search test
    await verify_unlimited_search()

    _logger.info("PGVector integration tests completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
