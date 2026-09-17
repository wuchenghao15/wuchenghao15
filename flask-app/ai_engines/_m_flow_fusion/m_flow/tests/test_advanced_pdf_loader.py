"""
高级PDF加载器测试
"""

from __future__ import annotations

import sys

import pytest
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

from m_flow.shared.loaders.external.advanced_pdf_loader import AdvancedPdfLoader

_pdf_loader_mod = sys.modules.get("m_flow.shared.loaders.external.advanced_pdf_loader")


class _Element:
    """模拟元素"""

    def __init__(self, cat: str, txt: str, meta: dict):
        self.category = cat
        self.text = txt
        self.metadata = meta

    def to_dict(self):
        return {"type": self.category, "text": self.text, "metadata": self.metadata}


@pytest.fixture
def loader():
    return AdvancedPdfLoader()


@pytest.mark.parametrize(
    "ext,mime,ok",
    [
        ("pdf", "application/pdf", True),
        ("txt", "text/plain", False),
        ("pdf", "text/plain", False),
        ("doc", "application/pdf", False),
    ],
)
def test_can_handle(loader, ext, mime, ok):
    """测试can_handle方法"""
    assert loader.can_handle(ext, mime) == ok


@pytest.mark.asyncio
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.open", new_callable=mock_open)
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.get_file_metadata", new_callable=AsyncMock)
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.get_storage_config")
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.get_file_storage")
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.PyPdfLoader")
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.partition_pdf")
async def test_unstructured_flow(mock_part, mock_py, mock_fs, mock_cfg, mock_meta, mock_op, loader):
    """测试unstructured正常流程"""
    elements = [
        _Element("Title", "Attention Is All You Need", {"page_number": 1}),
        _Element("NarrativeText", "基于复杂RNN或CNN的序列转导模型。", {"page_number": 1}),
        _Element(
            "Table",
            "表格数据",
            {"page_number": 2, "text_as_html": "<table><tr><td>D</td></tr></table>"},
        ),
    ]
    mock_part.return_value = elements
    mock_meta.return_value = {"content_hash": "abc123"}

    storage = MagicMock()
    storage.store = AsyncMock(return_value="/stored/text_abc123.txt")
    mock_fs.return_value = storage
    mock_cfg.return_value = {"data_root_directory": "/data"}

    result = await loader.load("/path/doc.pdf")

    assert result == "/stored/text_abc123.txt"
    mock_part.assert_called_once()
    mock_py.assert_not_called()


@pytest.mark.asyncio
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.open", new_callable=mock_open)
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.get_file_metadata", new_callable=AsyncMock)
@patch("m_flow.shared.loaders.external.advanced_pdf_loader.PyPdfLoader")
@patch(
    "m_flow.shared.loaders.external.advanced_pdf_loader.partition_pdf",
    side_effect=Exception("fail"),
)
async def test_fallback(mock_part, mock_py, mock_meta, mock_op, loader):
    """测试异常时回退到PyPdfLoader"""
    fb = MagicMock()
    fb.load = AsyncMock(return_value="/fallback.txt")
    mock_py.return_value = fb
    mock_meta.return_value = {"content_hash": "x"}

    result = await loader.load("/path/doc.pdf")

    assert result == "/fallback.txt"
    mock_part.assert_called_once()
    fb.load.assert_awaited_once()
