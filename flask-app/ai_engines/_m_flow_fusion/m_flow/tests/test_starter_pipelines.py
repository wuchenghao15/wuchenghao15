"""M-Flow 流水线脚本执行验证"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest


class MFlowPipelineExecutionSuite(unittest.TestCase):
    """验证各流水线脚本能正常执行完成"""

    TIMEOUT_SECONDS = 300
    REQUIRED_ENV = ("LLM_API_KEY", "EMBEDDING_API_KEY")

    def setUp(self):
        self._project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        self._pipeline_dir = os.path.join(self._project_root, "src", "pipelines")

        absent = [k for k in self.REQUIRED_ENV if not os.environ.get(k)]
        if absent:
            self.skipTest(f"环境变量未设置: {', '.join(absent)}")

    def _resolve_interpreter(self) -> str:
        venv_bin = os.path.join(self._project_root, ".venv", "bin", "python")
        return venv_bin if os.path.exists(venv_bin) else sys.executable

    def _invoke_script(self, filename: str):
        target = os.path.join(self._pipeline_dir, filename)
        interpreter = self._resolve_interpreter()

        try:
            outcome = subprocess.run(
                [interpreter, target],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
            )
            return outcome
        except subprocess.CalledProcessError as exc:
            self.fail(
                f"脚本 {filename} 异常退出 (rc={exc.returncode})\n"
                f"--- stdout ---\n{exc.stdout}\n--- stderr ---\n{exc.stderr}"
            )
        except subprocess.TimeoutExpired:
            self.fail(f"脚本 {filename} 超过 {self.TIMEOUT_SECONDS}s 未完成")

    def test_standard_pipeline(self):
        """标准流水线应成功退出"""
        res = self._invoke_script("default.py")
        self.assertEqual(res.returncode, 0)

    def test_granular_pipeline(self):
        """细粒度流水线应成功退出"""
        res = self._invoke_script("low_level.py")
        self.assertEqual(res.returncode, 0)

    def test_user_defined_model_pipeline(self):
        """用户自定义模型流水线应成功退出"""
        res = self._invoke_script("custom-model.py")
        self.assertEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
