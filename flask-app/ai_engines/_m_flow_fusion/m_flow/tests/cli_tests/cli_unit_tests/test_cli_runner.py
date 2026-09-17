"""
CLI测试运行器
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_UNIT_TESTS = [
    "test_cli_main.py",
    "test_cli_commands.py",
    "test_cli_utils.py",
    "test_cli_edge_cases.py",
]

_INTEGRATION_TESTS = ["test_cli_integration.py"]


def collect_tests() -> list[str]:
    """收集所有CLI测试文件"""
    base = Path(__file__).parent
    integ = base.parent.parent / "integration" / "cli"

    paths = []
    for name in _UNIT_TESTS:
        p = base / name
        if p.exists():
            paths.append(str(p))

    for name in _INTEGRATION_TESTS:
        p = integ / name
        if p.exists():
            paths.append(str(p))

    return paths


def run_all() -> int:
    """运行所有CLI测试"""
    return pytest.main(["-v", "--tb=short", *collect_tests()])


def run_single(filename: str) -> int:
    """运行单个测试文件"""
    path = Path(__file__).parent / filename
    if not path.exists():
        print(f"文件不存在: {filename}")
        return 1
    return pytest.main(["-v", "--tb=short", str(path)])


if __name__ == "__main__":
    code = run_single(sys.argv[1]) if len(sys.argv) > 1 else run_all()
    sys.exit(code)
