"""
搜索功能单元测试
"""

from __future__ import annotations

import types
from uuid import uuid4

import pytest

from m_flow.search.types import RecallMode


def _mock_user(uid=None, tid=None):
    """创建 mock 用户，使用真实 UUID"""
    return types.SimpleNamespace(id=uid or uuid4(), tenant_id=tid)


def _mock_dataset(name: str = "ds", tid=None, did=None, owner=None):
    """创建 mock 数据集，使用真实 UUID"""
    return types.SimpleNamespace(
        id=did or uuid4(),
        name=name,
        tenant_id=tid or uuid4(),
        owner_id=owner or uuid4(),
    )


@pytest.fixture
def search_module():
    import importlib

    return importlib.import_module("m_flow.search.methods.search")


@pytest.fixture(autouse=True)
def patch_side_effects(monkeypatch, search_module):
    """mock外部依赖"""

    async def mock_log_q(_text, _type, _uid):
        return types.SimpleNamespace(id="qid-1")

    async def mock_log_r(*args, **kwargs):
        return None

    async def mock_prepare(result):
        if isinstance(result, tuple) and len(result) == 3:
            r, ctx, dss = result
            return {"result": r, "context": ctx, "graphs": {}, "datasets": dss}
        return {"result": None, "context": None, "graphs": {}, "datasets": []}

    monkeypatch.setattr(search_module, "send_telemetry", lambda *a, **k: None)
    monkeypatch.setattr(search_module, "log_query", mock_log_q)
    monkeypatch.setattr(search_module, "log_result", mock_log_r)
    monkeypatch.setattr(search_module, "prepare_search_result", mock_prepare)
    return


class TestSearchAccessControl:
    """搜索访问控制测试"""

    @pytest.mark.asyncio
    async def test_returns_dataset_dicts(self, monkeypatch, search_module):
        """测试返回数据集格式的字典"""
        user = _mock_user()
        ds = _mock_dataset(name="ds1")

        async def mock_authorized_search_impl(**kw):
            return [("r", ["ctx"], [ds])]

        monkeypatch.setattr(search_module, "backend_access_control_enabled", lambda: True)
        monkeypatch.setattr(search_module, "_authorized_search_impl", mock_authorized_search_impl)

        # 非详细模式
        out = await search_module.search(
            query_text="q",
            query_type=RecallMode.EPISODIC,
            dataset_ids=[ds.id],
            user=user,
            verbose=False,
        )
        assert out == [
            {
                "search_result": ["r"],
                "dataset_id": str(ds.id),
                "dataset_name": "ds1",
                "dataset_tenant_id": str(ds.tenant_id),
            }
        ]

        # 详细模式
        out_v = await search_module.search(
            query_text="q",
            query_type=RecallMode.EPISODIC,
            dataset_ids=[ds.id],
            user=user,
            verbose=True,
        )
        assert out_v == [
            {
                "search_result": ["r"],
                "dataset_id": str(ds.id),
                "dataset_name": "ds1",
                "dataset_tenant_id": str(ds.tenant_id),
                "graphs": {},
            }
        ]
