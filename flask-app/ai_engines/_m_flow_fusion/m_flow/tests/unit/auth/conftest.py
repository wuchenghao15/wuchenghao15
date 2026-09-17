"""
Pytest configuration for auth module tests.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _load_security_check_module():
    """Load security_check module with mocked dependencies."""
    # Create mock modules for m_flow.shared.logging_utils
    mock_logger = MagicMock()

    mock_logging_utils = types.ModuleType("m_flow.shared.logging_utils")
    mock_logging_utils.get_logger = lambda *args, **kwargs: mock_logger

    # Create parent modules
    mock_m_flow = types.ModuleType("m_flow")
    mock_shared = types.ModuleType("m_flow.shared")
    mock_auth = types.ModuleType("m_flow.auth")
    mock_tests = types.ModuleType("m_flow.tests")
    mock_unit = types.ModuleType("m_flow.tests.unit")
    mock_auth_tests = types.ModuleType("m_flow.tests.unit.auth")

    # Register in sys.modules
    sys.modules.setdefault("m_flow", mock_m_flow)
    sys.modules.setdefault("m_flow.shared", mock_shared)
    sys.modules.setdefault("m_flow.shared.logging_utils", mock_logging_utils)
    sys.modules.setdefault("m_flow.auth", mock_auth)
    sys.modules.setdefault("m_flow.tests", mock_tests)
    sys.modules.setdefault("m_flow.tests.unit", mock_unit)
    sys.modules.setdefault("m_flow.tests.unit.auth", mock_auth_tests)

    # Find the path to the actual security_check module
    test_dir = Path(__file__).parent
    auth_dir = test_dir.parent.parent.parent / "auth"
    security_check_path = auth_dir / "security_check.py"

    if security_check_path.exists():
        spec = importlib.util.spec_from_file_location("m_flow.auth.security_check", security_check_path)
        security_check_module = importlib.util.module_from_spec(spec)
        sys.modules["m_flow.auth.security_check"] = security_check_module
        spec.loader.exec_module(security_check_module)
        return security_check_module
    return None


# Load module immediately when conftest is loaded
security_check = _load_security_check_module()
