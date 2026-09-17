"""
Root conftest.py for pytest configuration.
Ensures proper Python path setup for test discovery.

This file uses pytest_configure which is one of the earliest hooks,
executed before any test collection begins.
"""

import sys
from pathlib import Path

# Add project root to Python path IMMEDIATELY when this file is loaded
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """
    Called after command line options have been parsed and all plugins
    and initial conftest files been loaded.

    This is one of the earliest hooks, executed before test collection.
    """
    # Ensure project root is in sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Pre-import m_flow to ensure it's recognized as the correct package
    # This prevents path resolution issues during test collection
    try:
        import m_flow

        # Verify m_flow is loaded from the correct location
        expected_path = str(project_root / "m_flow" / "__init__.py")
        actual_path = str(Path(m_flow.__file__).resolve())
        if actual_path != expected_path:
            # Force reload from correct path
            if "m_flow" in sys.modules:
                del sys.modules["m_flow"]
            # Also clean any sub-modules
            to_remove = [k for k in sys.modules if k.startswith("m_flow.")]
            for k in to_remove:
                del sys.modules[k]
            # Re-import
            import m_flow
    except ImportError:
        pass


def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session."""
    print("Running teardown with pytest sessionfinish...")
