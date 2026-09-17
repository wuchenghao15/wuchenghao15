"""
S3 File Storage Integration Test
================================
m_flow.tests.test_s3_file_storage

Validates AWS S3 as a storage backend for m_flow:
- Data ingestion from S3 paths
- Knowledge graph construction from S3-stored content
- Multi-mode search operations
- Complete cleanup of S3-based storage
"""

import pathlib
import os
from uuid import uuid4

import m_flow
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.search.operations import get_history
from m_flow.auth.methods import get_seed_user
from m_flow.shared.logging_utils import get_logger
from m_flow.search.types import RecallMode

_logger = get_logger()


# Sample LLM content for knowledge graph construction
_LLM_CONTENT = """A large language model (LLM) is a language model notable for its ability to achieve general-purpose language generation and other natural language processing tasks such as classification. LLMs acquire these abilities by learning statistical relationships from text documents during a computationally intensive self-supervised and semi-supervised training process. LLMs can be used for text generation, a form of generative AI, by taking an input text and repeatedly predicting the next token or word.
LLMs are artificial neural networks. The largest and most capable, as of March 2024, are built with a decoder-only transformer-based architecture while some recent implementations are based on other architectures, such as recurrent neural network variants and Mamba (a state space model).
Up to 2020, fine tuning was the only way a model could be adapted to be able to accomplish specific tasks. Larger sized models, such as GPT-3, however, can be prompt-engineered to achieve similar results.[6] They are thought to acquire knowledge about syntax, semantics and "ontology" inherent in human language corpora, but also inaccuracies and biases present in the corpora.
Some notable LLMs are OpenAI's GPT series of models (e.g., GPT-3.5 and GPT-4, used in ChatGPT and Microsoft Copilot), Google's PaLM and Gemini (the latter of which is currently used in the chatbot of the same name), xAI's Grok, Meta's LLaMA family of open-source models, Anthropic's Claude models, Mistral AI's open source models, and Databricks' open source DBRX.
"""


async def main():
    """
    Primary test runner for S3 file storage integration.

    Configures S3 as storage backend and validates full functionality.
    """
    # Generate unique test run ID for S3 isolation
    s3_bucket = os.getenv("STORAGE_BUCKET_NAME")
    unique_run_id = uuid4()

    # Configure S3 storage paths
    data_s3_path = f"s3://{s3_bucket}/{unique_run_id}/data"
    system_s3_path = f"s3://{s3_bucket}/{unique_run_id}/system"

    m_flow.config.data_root_directory(data_s3_path)
    m_flow.config.system_root_directory(system_s3_path)

    # Initialize clean state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare test dataset
    ds_name = "artificial_intelligence"
    test_dir = pathlib.Path(__file__).parent
    ai_pdf_path = test_dir / "test_data" / "artificial-intelligence.pdf"

    await m_flow.add([str(ai_pdf_path)], ds_name)
    await m_flow.add([_LLM_CONTENT], ds_name)

    # Execute memorization pipeline
    await m_flow.memorize([ds_name])

    # Initialize vector search
    from m_flow.adapters.vector import get_vector_provider

    vec = get_vector_provider()

    concept_match = (await vec.search("Entity_name", "AI"))[0]
    concept_text = concept_match.payload["text"]

    # Test TRIPLET_COMPLETION mode
    completion_results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=concept_text,
    )
    assert len(completion_results) > 0, "TRIPLET_COMPLETION returned empty"
    _logger.info("Completion results: %d items", len(completion_results))

    # Test EPISODIC mode
    episodic_results = await m_flow.search(
        query_type=RecallMode.EPISODIC,
        query_text=concept_text,
    )
    assert len(episodic_results) > 0, "EPISODIC returned empty"
    _logger.info("Episodic results: %d items", len(episodic_results))

    # Validate search history
    current_user = await get_seed_user()
    history_entries = await get_history(current_user.id)
    assert len(history_entries) > 0, "History should not be empty"

    # Cleanup and verify data storage
    await m_flow.prune.prune_data()
    storage_cfg = get_storage_config()
    assert not os.path.isdir(storage_cfg["data_root_directory"]), "Local data directory persists after prune"

    # Cleanup and verify system storage
    await m_flow.prune.prune_system(metadata=True)

    # Verify vector database cleanup
    db_connection = await vec.get_connection()
    remaining_tables = await db_connection.table_names()
    assert len(remaining_tables) == 0, f"LanceDB has {len(remaining_tables)} tables after cleanup"

    # Verify relational database cleanup
    from m_flow.adapters.relational import get_db_adapter

    rel_engine = get_db_adapter()
    db_dir = os.path.dirname(rel_engine.db_path)
    db_filename = os.path.basename(rel_engine.db_path)
    storage = get_file_storage(db_dir)

    assert not await storage.file_exists(db_filename), "SQLite database file persists after cleanup"

    # Verify graph database cleanup
    from m_flow.adapters.graph import get_graph_config

    graph_cfg = get_graph_config()

    if graph_cfg.graph_database_provider.lower() == "kuzu":
        assert not os.path.exists(graph_cfg.graph_file_path), "Kuzu database file persists after cleanup"
    else:
        db_empty = not os.path.exists(graph_cfg.graph_file_path) or not os.listdir(graph_cfg.graph_file_path)
        assert db_empty, "Graph database directory not empty"

    _logger.info("S3 file storage integration test completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main(), debug=True)
