"""
Core Library Integration Test
=============================
m_flow.tests.test_library

Comprehensive integration test for m_flow core functionality:
- Data ingestion and knowledge graph construction
- Multi-mode search operations
- Document update/refresh functionality
- Complete system cleanup and verification
"""

import pathlib
import os

import m_flow
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.search.operations import get_history
from m_flow.auth.methods import get_seed_user
from m_flow.shared.logging_utils import get_logger
from m_flow.search.types import RecallMode
from m_flow import update

_logger = get_logger()


# Sample LLM content for knowledge graph construction
_LLM_SAMPLE = """A large language model (LLM) is a language model notable for its ability to achieve general-purpose language generation and other natural language processing tasks such as classification. LLMs acquire these abilities by learning statistical relationships from text documents during a computationally intensive self-supervised and semi-supervised training process. LLMs can be used for text generation, a form of generative AI, by taking an input text and repeatedly predicting the next token or word.
LLMs are artificial neural networks. The largest and most capable, as of March 2024, are built with a decoder-only transformer-based architecture while some recent implementations are based on other architectures, such as recurrent neural network variants and Mamba (a state space model).
Up to 2020, fine tuning was the only way a model could be adapted to be able to accomplish specific tasks. Larger sized models, such as GPT-3, however, can be prompt-engineered to achieve similar results.[6] They are thought to acquire knowledge about syntax, semantics and "ontology" inherent in human language corpora, but also inaccuracies and biases present in the corpora.
Some notable LLMs are OpenAI's GPT series of models (e.g., GPT-3.5 and GPT-4, used in ChatGPT and Microsoft Copilot), Google's PaLM and Gemini (the latter of which is currently used in the chatbot of the same name), xAI's Grok, Meta's LLaMA family of open-source models, Anthropic's Claude models, Mistral AI's open source models, and Databricks' open source DBRX.
"""


async def main():
    """
    Primary test execution for m_flow core library.

    Tests ingestion, search, update, and cleanup workflows.
    """
    # Configure storage locations
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_library").resolve()
    system_dir = (test_root / ".mflow/system" / "test_library").resolve()

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Initialize clean state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare test dataset
    ds_name = "artificial_intelligence"
    ai_pdf = test_root / "test_data" / "artificial-intelligence.pdf"

    await m_flow.add([str(ai_pdf)], ds_name)
    await m_flow.add([_LLM_SAMPLE], ds_name)

    # Execute memorization and capture run info
    pipeline_results = await m_flow.memorize([ds_name])

    # Initialize vector search
    from m_flow.adapters.vector import get_vector_provider

    vec = get_vector_provider()

    concept_result = (await vec.search("Entity_name", "AI"))[0]
    concept_text = concept_result.payload["text"]

    # Test TRIPLET_COMPLETION mode
    completion = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=concept_text,
    )
    assert len(completion) > 0, "TRIPLET_COMPLETION returned empty"
    _logger.info("Graph completion: %d results", len(completion))

    # Test EPISODIC mode
    episodic = await m_flow.search(
        query_type=RecallMode.EPISODIC,
        query_text=concept_text,
    )
    _logger.info("Episodic: %d results", len(episodic))

    # Validate search history
    current_user = await get_seed_user()
    history = await get_history(current_user.id)
    assert len(history) > 0, "History should not be empty"

    # =========================================
    # Test document update functionality
    # =========================================
    run_detail = list(pipeline_results.values())[0]

    for data_entry in run_detail.processing_results:
        # Replace content with new information about Mark and Cindy
        await update(
            dataset_id=run_detail.dataset_id,
            data_id=data_entry["data_id"],
            data="Mark met with Cindy at a cafe.",
        )

    # Verify updated content is searchable
    updated_results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What information do you contain?",
        dataset_ids=[run_detail.dataset_id],
    )

    assert len(updated_results) > 0, "Update failed: search returned no results"

    # =========================================
    # Cleanup and verification
    # =========================================

    # Clean data storage
    await m_flow.prune.prune_data()
    storage_cfg = get_storage_config()
    assert not os.path.isdir(storage_cfg["data_root_directory"]), "Data directory persists after cleanup"

    # Clean system storage
    await m_flow.prune.prune_system(metadata=True)

    # Verify vector database is empty
    db_conn = await vec.get_connection()
    remaining_tables = await db_conn.table_names()
    assert len(remaining_tables) == 0, f"LanceDB has {len(remaining_tables)} tables after cleanup"

    # Verify relational database is clean (delete_database resets to empty schema)
    from m_flow.adapters.relational import get_db_adapter

    rel_engine = get_db_adapter()
    data_after = await rel_engine.get_all_data_from_table("data")
    assert len(data_after) == 0, f"Relational DB not empty after cleanup: {len(data_after)} records"

    # Verify graph database is removed
    from m_flow.adapters.graph import get_graph_config

    graph_cfg = get_graph_config()

    if graph_cfg.graph_database_provider.lower() == "kuzu":
        assert not os.path.exists(graph_cfg.graph_file_path), "Kuzu database persists after cleanup"
    else:
        db_empty = not os.path.exists(graph_cfg.graph_file_path) or not os.listdir(graph_cfg.graph_file_path)
        assert db_empty, "Graph database directory not empty"

    _logger.info("Core library integration test completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main(), debug=True)
