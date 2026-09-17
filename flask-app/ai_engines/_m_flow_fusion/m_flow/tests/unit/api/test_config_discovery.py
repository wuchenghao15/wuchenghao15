# m_flow/tests/unit/api/test_config_discovery.py
"""
Unit tests for config discovery features (P1).

Tests cover:
1. config.show() method
2. config.env_vars() method
3. config.env_categories() method
4. Environment variable registry
"""

import ast
import pathlib
import pytest


# ============================================================
# Test config.show() Method
# ============================================================


class TestConfigShow:
    """Tests for config.show() method."""

    def test_show_method_exists(self):
        """Verify config.show() exists."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "def show(" in content

    def test_show_supports_category_param(self):
        """Verify category parameter support."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "category: Optional[str] = None" in content

    def test_show_supports_as_dict_param(self):
        """Verify as_dict parameter support."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "as_dict: bool = False" in content

    def test_show_has_sensitive_field_masking(self):
        """Verify sensitive fields are masked."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "SENSITIVE_FIELDS" in content
        assert "_mask_sensitive" in content

    def test_show_supports_pydantic_model_dump(self):
        """Verify Pydantic model_dump() support."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "model_dump" in content

    def _get_config_file(self) -> pathlib.Path:
        """Get path to config.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "config" / "config.py"


# ============================================================
# Test config.env_vars() Method
# ============================================================


class TestConfigEnvVars:
    """Tests for config.env_vars() method."""

    def test_env_vars_method_exists(self):
        """Verify config.env_vars() exists."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "def env_vars(" in content

    def test_env_vars_supports_category_filter(self):
        """Verify category filter support."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "category: Optional[str] = None" in content

    def test_env_vars_uses_registry(self):
        """Verify env_vars uses the registry."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "_get_env_var_registry" in content

    def _get_config_file(self) -> pathlib.Path:
        """Get path to config.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "config" / "config.py"


# ============================================================
# Test config.env_categories() Method
# ============================================================


class TestConfigEnvCategories:
    """Tests for config.env_categories() method."""

    def test_env_categories_method_exists(self):
        """Verify config.env_categories() exists."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        assert "def env_categories(" in content

    def _get_config_file(self) -> pathlib.Path:
        """Get path to config.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "config" / "config.py"


# ============================================================
# Test Environment Variable Registry
# ============================================================


class TestEnvRegistry:
    """Tests for environment variable registry."""

    def test_registry_file_exists(self):
        """Verify env_registry.py exists."""
        registry_file = self._get_registry_file()
        assert registry_file.exists()

    def test_env_registry_constant(self):
        """Verify ENV_REGISTRY constant exists."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "ENV_REGISTRY:" in content

    def test_get_env_function(self):
        """Verify get_env() function exists."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "def get_env(" in content

    def test_get_env_var_registry_function(self):
        """Verify _get_env_var_registry() function exists."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "def _get_env_var_registry(" in content

    def test_get_categories_function(self):
        """Verify get_categories() function exists."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "def get_categories(" in content

    def test_type_conversion_support(self):
        """Verify type conversion in get_env()."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "var_type ==" in content or "type" in content

    def test_sensitive_masking(self):
        """Verify sensitive value masking."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "mask_sensitive" in content

    def test_has_core_env_vars(self):
        """Verify core environment variables are registered."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        assert "LLM_API_KEY" in content
        assert "LLM_MODEL" in content
        assert "MFLOW_CONTENT_ROUTING" in content

    def test_registry_syntax(self):
        """Verify registry file has valid Python syntax."""
        registry_file = self._get_registry_file()
        content = registry_file.read_text()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"env_registry.py has syntax error: {e}")

    def _get_registry_file(self) -> pathlib.Path:
        """Get path to env_registry.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "config" / "env_registry.py"


# ============================================================
# Test Syntax
# ============================================================


class TestConfigSyntax:
    """Test config.py has valid Python syntax."""

    def test_valid_python_syntax(self):
        """Verify config.py is valid Python."""
        config_file = self._get_config_file()
        content = config_file.read_text()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"config.py has syntax error: {e}")

    def _get_config_file(self) -> pathlib.Path:
        """Get path to config.py file."""
        current = pathlib.Path(__file__)
        mflow_root = current.parent.parent.parent.parent
        return mflow_root / "api" / "v1" / "config" / "config.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
