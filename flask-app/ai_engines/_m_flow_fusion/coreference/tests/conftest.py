"""
Shared fixtures for regression tests.
These tests capture the CURRENT behavior as the golden standard.
Any refactoring must preserve these exact outputs.
"""

import sys
import os
import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def zh_resolver():
    """Chinese coreference resolver (session-scoped, expensive to init)."""
    from coreference_module import CoreferenceResolver

    return CoreferenceResolver()


@pytest.fixture
def fresh_zh_resolver():
    """Fresh Chinese resolver (reset per test)."""
    from coreference_module import CoreferenceResolver

    r = CoreferenceResolver()
    r.reset()
    return r


@pytest.fixture(scope="session")
def en_resolver():
    """English coreference resolver (session-scoped)."""
    from english_coreference.coreference import CoreferenceResolver

    return CoreferenceResolver()


@pytest.fixture(scope="session")
def tokenizer():
    """Chinese tokenizer."""
    from coreference_module import ChineseTokenizer

    return ChineseTokenizer()
