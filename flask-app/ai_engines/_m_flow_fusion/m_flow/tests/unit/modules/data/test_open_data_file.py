"""
open_data_file函数单元测试
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from m_flow.shared.files.utils.open_data_file import open_data_file


def _create_temp_file(content: str) -> str:
    """创建临时文件"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(content)
        return f.name


class TestOpenDataFile:
    """open_data_file测试套件"""

    @pytest.mark.asyncio
    async def test_regular_path(self):
        """测试普通文件路径"""
        content = "普通路径测试内容"
        path = _create_temp_file(content)
        try:
            async with open_data_file(path, mode="r") as f:
                assert f.read() == content
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_file_url_text(self):
        """测试file://URL文本模式"""
        content = "File URL文本模式测试"
        path = _create_temp_file(content)
        try:
            url = Path(path).as_uri()
            async with open_data_file(url, mode="r") as f:
                assert f.read() == content
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_file_url_binary(self):
        """测试file://URL二进制模式"""
        content = "二进制模式测试"
        path = _create_temp_file(content)
        try:
            url = Path(path).as_uri()
            async with open_data_file(url, mode="rb") as f:
                assert f.read() == content.encode("utf-8")
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_file_url_encoding(self):
        """测试file://URL编码"""
        content = "UTF-8测试: café ☕ 中文"
        path = _create_temp_file(content)
        try:
            url = Path(path).as_uri()
            async with open_data_file(url, mode="r", encoding="utf-8") as f:
                assert f.read() == content
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        """测试不存在的文件"""
        with pytest.raises(FileNotFoundError):
            async with open_data_file("file:///nonexistent/file.txt", mode="r") as f:
                f.read()

    @pytest.mark.asyncio
    async def test_double_prefix(self):
        """测试双重file://前缀"""
        content = "双前缀测试"
        path = _create_temp_file(content)
        try:
            url = f"file://{Path(path).as_uri()}"
            async with open_data_file(url, mode="r") as f:
                assert f.read() == content
        except FileNotFoundError:
            pass  # 预期行为
        finally:
            os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
