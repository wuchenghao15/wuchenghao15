"""
工具函数单元测试
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from unittest.mock import mock_open, patch

from m_flow.root_dir import ensure_absolute_path
from m_flow.shared.files.utils.get_file_content_hash import get_file_content_hash
from m_flow.shared.utils import get_anonymous_id


@pytest.fixture
def tmp_home(tmp_path):
    return tmp_path


class TestAnonymousId:
    """匿名ID测试"""

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open, read_data=str(uuid4()))
    def test_get_anonymous_id(self, mock_file, mock_dirs, tmp_home):
        os.environ["HOME"] = str(tmp_home)
        aid = get_anonymous_id()
        assert isinstance(aid, str) and len(aid) > 0


class TestFileContentHash:
    """文件内容哈希测试"""

    @pytest.mark.asyncio
    async def test_hash_from_file(self):
        """测试文件哈希"""
        content = "Test content: café ☕"
        expected = hashlib.md5(content.encode("utf-8")).hexdigest()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
            f.write(content)
            path = f.name

        try:
            result = await get_file_content_hash(path)
            assert result == expected
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_hash_from_stream(self):
        """测试流哈希"""
        data = b"test_data"
        expected = hashlib.md5(data).hexdigest()

        stream = BytesIO(data)
        result = await get_file_content_hash(stream)
        assert result == expected


class TestEnsureAbsolutePath:
    """绝对路径验证测试"""

    @pytest.mark.asyncio
    async def test_absolute_path(self):
        """测试绝对路径处理"""
        abs_path = "C:/path" if os.name == "nt" else "/path"
        result = ensure_absolute_path(abs_path)
        assert result == str(Path(abs_path).resolve())

    @pytest.mark.asyncio
    async def test_relative_path_raises(self):
        """测试相对路径抛出错误"""
        with pytest.raises(ValueError, match="Expected an absolute path"):
            ensure_absolute_path("relative/path")

    @pytest.mark.asyncio
    async def test_none_path_raises(self):
        """测试None路径抛出错误"""
        with pytest.raises(ValueError, match="cannot be None"):
            ensure_absolute_path(None)
