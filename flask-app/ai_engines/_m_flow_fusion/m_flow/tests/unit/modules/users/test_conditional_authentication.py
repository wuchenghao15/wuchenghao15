"""
条件认证测试
"""

from __future__ import annotations

import importlib
import os
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, patch

from m_flow.auth.models import User

_gau_mod = importlib.import_module("m_flow.auth.methods.get_authenticated_user")


def _user():
    """创建模拟用户"""
    return User(id=uuid4(), email="u@test.com", hashed_password="x", is_active=True, is_verified=True)


def _default_user():
    """创建默认用户"""
    return SimpleNamespace(id=uuid4(), email="default@test.com", is_active=True)


class TestConditionalAuth:
    """条件认证测试"""

    @pytest.mark.asyncio
    @patch.object(_gau_mod, "get_seed_user", new_callable=AsyncMock)
    async def test_no_token_returns_default(self, mock_default):
        """测试无token返回默认用户"""
        mock_default.return_value = _default_user()
        result = await _gau_mod.get_authenticated_user(user=None)
        assert result == mock_default.return_value
        mock_default.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(_gau_mod, "get_seed_user", new_callable=AsyncMock)
    async def test_valid_user_returned(self, mock_default):
        """测试有效用户返回"""
        u = _user()
        result = await _gau_mod.get_authenticated_user(user=u)
        assert result == u
        mock_default.assert_not_called()

    @pytest.mark.asyncio
    @patch.object(_gau_mod, "get_seed_user", new_callable=AsyncMock)
    async def test_auth_required_with_user(self, mock_default):
        """测试认证必需时带用户"""
        u = _user()
        result = await _gau_mod.get_authenticated_user(user=u)
        assert result == u


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_fastapi_users_dep(self):
        """测试FastAPI Users依赖"""
        from m_flow.auth.get_fastapi_users import get_fastapi_users

        fu = get_fastapi_users()
        opt_dep = fu.current_user(optional=True, active=True)
        req_dep = fu.current_user(active=True)
        assert callable(opt_dep) and callable(req_dep)

    @pytest.mark.asyncio
    async def test_function_exists(self):
        """测试函数存在"""
        from m_flow.auth.methods.get_authenticated_user import (
            REQUIRE_AUTHENTICATION,
            get_authenticated_user,
        )

        assert callable(get_authenticated_user)
        assert isinstance(REQUIRE_AUTHENTICATION, bool)


class TestEnvVars:
    """环境变量测试"""

    def test_require_auth_true(self):
        """测试REQUIRE_AUTHENTICATION=true"""
        with patch.dict(os.environ, {"REQUIRE_AUTHENTICATION": "true"}):
            mod_name = "m_flow.auth.methods.get_authenticated_user"
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            from m_flow.auth.methods.get_authenticated_user import REQUIRE_AUTHENTICATION

            assert REQUIRE_AUTHENTICATION


class TestEdgeCases:
    """边缘情况测试"""

    @pytest.mark.asyncio
    @patch.object(_gau_mod, "get_seed_user", new_callable=AsyncMock)
    async def test_default_user_exception(self, mock_default):
        """测试默认用户异常"""
        mock_default.side_effect = Exception("DB error")
        with pytest.raises(Exception, match="DB error"):
            await _gau_mod.get_authenticated_user(user=None)

    @pytest.mark.asyncio
    @patch.object(_gau_mod, "get_seed_user", new_callable=AsyncMock)
    async def test_type_consistency(self, mock_default):
        """测试类型一致性"""
        u = _user()
        du = _default_user()
        mock_default.return_value = du

        r1 = await _gau_mod.get_authenticated_user(user=u)
        r2 = await _gau_mod.get_authenticated_user(user=None)

        assert r1 == u and r2 == du
        for r in [r1, r2]:
            assert hasattr(r, "id") and hasattr(r, "email")


@pytest.mark.asyncio
class TestScenarios:
    """场景测试"""

    @patch.object(_gau_mod, "get_seed_user", new_callable=AsyncMock)
    async def test_fallback_scenarios(self, mock_default):
        """测试回退场景"""
        du = _default_user()
        mock_default.return_value = du
        result = await _gau_mod.get_authenticated_user(user=None)
        assert result == du
        mock_default.assert_called_once()

    async def test_valid_active_user(self):
        """测试有效活跃用户"""
        u = _user()
        result = await _gau_mod.get_authenticated_user(user=u)
        assert result == u
