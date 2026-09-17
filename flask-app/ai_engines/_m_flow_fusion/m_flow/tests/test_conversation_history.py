"""
Conversation History Integration Test
=====================================
m_flow.tests.test_conversation_history

End-to-end tests for conversation history and session management:
- Q&A caching in Redis
- Session isolation
- History formatting utilities
- Multi-retriever session support
"""

import pathlib

import m_flow
from m_flow.adapters.cache import get_cache_engine
from m_flow.search.types import RecallMode
from m_flow.shared.logging_utils import get_logger
from m_flow.auth.methods import get_seed_user

_logger = get_logger()


async def main():
    """
    Primary test execution for conversation history features.

    Tests session management, Q&A caching, and history retrieval.
    """
    # Configure storage
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_conversation_history").resolve()
    system_dir = (test_root / ".mflow/system" / "test_conversation_history").resolve()

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Clean start
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare test content
    ds_name = "conversation_history_test"
    content_a = """TechCorp is a technology company based in San Francisco. They specialize in artificial intelligence and machine learning."""
    content_b = """DataCo is a data analytics company. They help businesses make sense of their data."""

    await m_flow.add(data=content_a, dataset_name=ds_name)
    await m_flow.add(data=content_b, dataset_name=ds_name)
    await m_flow.memorize(datasets=[ds_name])

    user = await get_seed_user()
    cache = get_cache_engine()
    assert cache is not None, "Cache engine required for testing"

    # =========================================
    # Test 1: Session-based Q&A caching
    # =========================================
    session_graph = "test_session_graph"

    await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is TechCorp?",
        session_id=session_graph,
    )

    qa_entries = await cache.get_latest_qa(str(user.id), session_graph, last_n=10)
    assert len(qa_entries) == 1, f"Expected 1 Q&A entry, found {len(qa_entries)}"

    techcorp_qa = [e for e in qa_entries if e["question"] == "What is TechCorp?"]
    assert len(techcorp_qa) >= 1, "Should find TechCorp question"
    assert "answer" in techcorp_qa[0] and "context" in techcorp_qa[0], "Q&A must have answer and context"

    # =========================================
    # Test 2: Follow-up query uses context
    # =========================================
    follow_up = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="Tell me more about it",
        session_id=session_graph,
    )
    assert isinstance(follow_up, list) and follow_up, "Follow-up should return results"

    qa_after_followup = await cache.get_latest_qa(str(user.id), session_graph, last_n=10)
    relevant_qa = [e for e in qa_after_followup if e["question"] in ["What is TechCorp?", "Tell me more about it"]]
    assert len(relevant_qa) == 2, f"Expected 2 Q&A pairs, found {len(relevant_qa)}"

    # =========================================
    # Test 3: Session isolation
    # =========================================
    session_separate = "test_session_separate"

    dataco_result = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is DataCo?",
        session_id=session_separate,
    )
    assert isinstance(dataco_result, list) and dataco_result, "Separate session should return results"

    separate_qa = await cache.get_latest_qa(str(user.id), session_separate, last_n=10)
    dataco_entries = [e for e in separate_qa if e["question"] == "What is DataCo?"]
    assert len(dataco_entries) == 1, "Session 2 should have DataCo question"

    # =========================================
    # Test 4: Default session handling
    # =========================================
    default_result = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="Test default session",
        session_id=None,
    )
    assert isinstance(default_result, list) and default_result, "Default session should return results"

    default_qa = await cache.get_latest_qa(str(user.id), "default_session", last_n=10)
    default_entries = [e for e in default_qa if e["question"] == "Test default session"]
    assert len(default_entries) == 1, "Default session should have test question"

    # =========================================
    # Test 5: EPISODIC retriever session support
    # =========================================
    session_episodic = "test_session_episodic"

    episodic_result = await m_flow.search(
        query_type=RecallMode.EPISODIC,
        query_text="What companies are mentioned?",
        session_id=session_episodic,
    )
    assert isinstance(episodic_result, list), "EPISODIC must return list"

    # =========================================
    # Test 6: History formatting utility
    # =========================================
    from m_flow.retrieval.utils.session_cache import get_conversation_history

    formatted = await get_conversation_history(session_id=session_graph)

    assert "Previous conversation:" in formatted, "Should have header"
    assert "QUESTION:" in formatted, "Should have question prefix"
    assert "CONTEXT:" in formatted, "Should have context prefix"
    assert "ANSWER:" in formatted, "Should have answer prefix"

    # =========================================
    # Cleanup
    # =========================================
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    _logger.info("Conversation history tests completed successfully")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
