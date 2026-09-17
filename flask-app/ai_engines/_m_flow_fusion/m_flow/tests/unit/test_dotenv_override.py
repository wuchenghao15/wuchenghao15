"""
测试 dotenv override=False 修复。

验证用户在 import m_flow 前设置的环境变量不会被 .env 文件覆盖。
"""

import os
import tempfile
import pytest


class TestDotenvOverride:
    """测试 dotenv 加载行为。"""

    def test_user_env_takes_precedence_over_dotenv(self):
        """
        验证用户设置的环境变量优先于 .env 文件。

        步骤：
        1. 设置环境变量 TEST_DOTENV_PRIORITY=user_value
        2. 创建 .env 文件，包含 TEST_DOTENV_PRIORITY=dotenv_value
        3. 调用 load_dotenv(override=False)
        4. 验证环境变量值仍为 user_value
        """
        from dotenv import load_dotenv

        test_var = "TEST_DOTENV_PRIORITY"
        user_value = "user_value"
        dotenv_value = "dotenv_value"

        # 设置用户环境变量
        os.environ[test_var] = user_value

        try:
            # 创建临时 .env 文件
            with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
                f.write(f"{test_var}={dotenv_value}\n")
                env_file = f.name

            # 使用 override=False 加载（这是我们修复后的行为）
            load_dotenv(env_file, override=False)

            # 验证用户值优先
            assert os.environ.get(test_var) == user_value, f"Expected '{user_value}', got '{os.environ.get(test_var)}'"

        finally:
            # 清理
            os.environ.pop(test_var, None)
            if os.path.exists(env_file):
                os.unlink(env_file)

    def test_dotenv_loads_when_env_not_set(self):
        """
        验证当用户未设置环境变量时，.env 文件的值被正确加载。
        """
        from dotenv import load_dotenv

        test_var = "TEST_DOTENV_UNSET"
        dotenv_value = "dotenv_only_value"

        # 确保环境变量未设置
        os.environ.pop(test_var, None)

        try:
            # 创建临时 .env 文件
            with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
                f.write(f"{test_var}={dotenv_value}\n")
                env_file = f.name

            # 使用 override=False 加载
            load_dotenv(env_file, override=False)

            # 验证 .env 值被加载
            assert os.environ.get(test_var) == dotenv_value, (
                f"Expected '{dotenv_value}', got '{os.environ.get(test_var)}'"
            )

        finally:
            # 清理
            os.environ.pop(test_var, None)
            if os.path.exists(env_file):
                os.unlink(env_file)

    def test_override_true_would_override_user_env(self):
        """
        验证 override=True 会覆盖用户环境变量（这是我们修复前的行为）。
        这个测试确保我们理解了 override 参数的语义。
        """
        from dotenv import load_dotenv

        test_var = "TEST_DOTENV_OVERRIDE_TRUE"
        user_value = "user_value"
        dotenv_value = "dotenv_value"

        # 设置用户环境变量
        os.environ[test_var] = user_value

        try:
            # 创建临时 .env 文件
            with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
                f.write(f"{test_var}={dotenv_value}\n")
                env_file = f.name

            # 使用 override=True 加载（旧的问题行为）
            load_dotenv(env_file, override=True)

            # 验证 .env 值覆盖了用户值
            assert os.environ.get(test_var) == dotenv_value, (
                f"Expected '{dotenv_value}' with override=True, got '{os.environ.get(test_var)}'"
            )

        finally:
            # 清理
            os.environ.pop(test_var, None)
            if os.path.exists(env_file):
                os.unlink(env_file)


class TestMflowDotenvSourceCode:
    """测试 m_flow 源代码中的 dotenv 配置（不导入 m_flow 模块）。"""

    def test_mflow_init_uses_override_false(self):
        """
        验证 m_flow/__init__.py 使用 override=False。

        这是一个静态检查，直接读取源文件。
        """
        import pathlib

        # 找到 m_flow/__init__.py
        current_file = pathlib.Path(__file__)
        mflow_root = current_file.parent.parent.parent  # m_flow/tests/unit -> m_flow
        init_file = mflow_root / "__init__.py"

        assert init_file.exists(), f"Cannot find {init_file}"

        content = init_file.read_text()

        # 找到包含 load_dotenv() 调用的非注释行（排除 import 语句）
        lines = content.split("\n")
        load_dotenv_calls = [
            line
            for line in lines
            if "load_dotenv(" in line  # 只匹配调用，不匹配 import
            and not line.strip().startswith("#")
            and "import" not in line.lower()
        ]

        assert len(load_dotenv_calls) >= 1, "No load_dotenv() call found in m_flow/__init__.py"

        for line in load_dotenv_calls:
            assert "override=False" in line, f"Expected override=False in: {line}"
            assert "override=True" not in line, f"Found override=True in: {line}"

    def test_mflow_shared_uses_override_false(self):
        """
        验证 m_flow/shared/__init__.py 使用 override=False。
        """
        import pathlib

        # 找到 m_flow/shared/__init__.py
        current_file = pathlib.Path(__file__)
        mflow_root = current_file.parent.parent.parent  # m_flow/tests/unit -> m_flow
        shared_init = mflow_root / "shared" / "__init__.py"

        assert shared_init.exists(), f"Cannot find {shared_init}"

        content = shared_init.read_text()

        # 找到包含 load_dotenv() 调用的非注释行（排除 import 语句）
        lines = content.split("\n")
        load_dotenv_calls = [
            line
            for line in lines
            if "load_dotenv(" in line  # 只匹配调用，不匹配 import
            and not line.strip().startswith("#")
            and "import" not in line.lower()
        ]

        assert len(load_dotenv_calls) >= 1, "No load_dotenv() call found in m_flow/shared/__init__.py"

        for line in load_dotenv_calls:
            assert "override=False" in line, f"Expected override=False in: {line}"
            assert "override=True" not in line, f"Found override=True in: {line}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
