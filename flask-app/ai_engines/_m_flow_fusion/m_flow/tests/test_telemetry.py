"""
遥测功能单元测试
"""

from __future__ import annotations

import os
import sys
import uuid
import unittest
from unittest.mock import MagicMock, patch

from m_flow.shared.utils import send_telemetry


class TestTelemetry(unittest.TestCase):
    """遥测测试套件"""

    def _ensure_anon_id(self) -> str:
        """确保.anon_id文件存在"""
        proj_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(proj_root, ".anon_id")

        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write("test-machine")
            print(f"创建 {path}", file=sys.stderr)

        self.assertTrue(os.path.exists(path))

        with open(path) as f:
            content = f.read().strip()

        self.assertTrue(len(content) > 0)
        return path

    @patch("m_flow.shared.utils._TELEMETRY_ENDPOINT", "https://fake-endpoint.test")
    @patch("m_flow.shared.utils.requests.post")
    def test_enabled(self, mock_post: MagicMock):
        """测试启用遥测"""
        self._ensure_anon_id()

        mock_resp = MagicMock(status_code=200)
        mock_post.return_value = mock_resp

        os.environ.pop("TELEMETRY_DISABLED", None)
        orig_env = os.environ.get("ENV")
        os.environ["ENV"] = "prod"

        try:
            uid = str(uuid.uuid4())
            send_telemetry("test_event", uid, {"key": "val"})

            mock_post.assert_called_once()
            _, kw = mock_post.call_args
            payload = kw["json"]

            self.assertEqual(payload.get("event_name"), "test_event")
            self.assertEqual(payload["user_properties"].get("user_id"), uid)
            self.assertEqual(payload["properties"].get("user_id"), uid)
            self.assertEqual(payload["properties"].get("key"), "val")
        finally:
            if orig_env:
                os.environ["ENV"] = orig_env
            else:
                os.environ.pop("ENV", None)

    @patch("m_flow.shared.utils.requests.post")
    def test_disabled(self, mock_post: MagicMock):
        """测试禁用遥测"""
        os.environ["TELEMETRY_DISABLED"] = "1"

        try:
            send_telemetry("disabled_event", "user1", {"k": "v"})
            mock_post.assert_not_called()
        finally:
            os.environ.pop("TELEMETRY_DISABLED", None)

    @patch("m_flow.shared.utils.requests.post")
    def test_dev_env(self, mock_post: MagicMock):
        """测试开发环境禁用遥测"""
        orig = os.environ.get("ENV")
        os.environ["ENV"] = "dev"
        os.environ.pop("TELEMETRY_DISABLED", None)

        try:
            send_telemetry("dev_event", "user1", {"k": "v"})
            mock_post.assert_not_called()
        finally:
            if orig:
                os.environ["ENV"] = orig
            else:
                os.environ.pop("ENV", None)


if __name__ == "__main__":
    unittest.main()
