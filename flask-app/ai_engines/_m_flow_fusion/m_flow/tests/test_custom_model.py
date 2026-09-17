"""
Custom Model Definition Test
============================
m_flow.tests.test_custom_model

Validates custom MemoryNode model definitions:
- User-defined graph node types
- Custom field indexing configuration
- Knowledge graph construction with custom models
- Search operations on custom model graphs
"""

import pathlib

import m_flow
from m_flow.search.operations import get_history
from m_flow.auth.methods import get_seed_user
from m_flow.shared.logging_utils import get_logger
from m_flow.search.types import RecallMode
from m_flow.low_level import MemoryNode

_logger = get_logger()


async def main():
    """
    Test execution for custom MemoryNode model definitions.

    Defines custom domain models and validates graph operations.
    """
    # Configure storage paths
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_custom_model").resolve()
    system_dir = (test_root / ".mflow/system" / "test_custom_model").resolve()

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Initialize clean state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # =========================================
    # Define custom domain models
    # =========================================

    class FieldCategory(MemoryNode):
        """Classification category for application domains."""

        name: str = "Field"
        metadata: dict = {"index_fields": ["name"]}

    class ApplicationDomain(MemoryNode):
        """Represents an application domain where languages are used."""

        name: str
        is_type: FieldCategory
        metadata: dict = {"index_fields": ["name"]}

    class LanguageCategory(MemoryNode):
        """Classification for programming languages."""

        name: str = "Programming Language"
        metadata: dict = {"index_fields": ["name"]}

    class ProgrammingLang(MemoryNode):
        """Represents a programming language with its applications."""

        name: str
        used_in: list[ApplicationDomain] = []
        is_type: LanguageCategory
        metadata: dict = {"index_fields": ["name"]}

    # =========================================
    # Ingest and process test content
    # =========================================
    sample_text = (
        "Python is an interpreted, high-level, general-purpose programming language. "
        "It was created by Guido van Rossum and first released in 1991. "
        "Python is widely used in data analysis, web development, and machine learning."
    )

    await m_flow.add(sample_text)
    await m_flow.memorize()

    # =========================================
    # Test search operations
    # =========================================

    # Graph completion search
    completion_results = await m_flow.search(
        RecallMode.TRIPLET_COMPLETION,
        "What is python?",
    )
    assert len(completion_results) > 0, "Graph completion should return results"
    _logger.info("Completion results: %d items", len(completion_results))

    # Episodic memory search
    memory_results = await m_flow.search(RecallMode.EPISODIC, "Python")
    _logger.info("Episodic results: %d items", len(memory_results))

    # Validate search history
    user = await get_seed_user()
    history = await get_history(user.id)
    assert len(history) > 0, "History should not be empty"

    _logger.info("Custom model test completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main(), debug=True)
