#!/usr/bin/env python3
"""薄封装：测试系统主脚本，实际代码已迁入 tests/test_system.py。
保持旧路径 CLI：`python3 test_system.py` 与 `from test_system import main` 均可用。
"""
from __future__ import annotations

import os as _os
import runpy as _runpy
import sys as _sys

_THIS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _THIS_DIR not in _sys.path:
    _sys.path.insert(0, _THIS_DIR)

from tests.test_system import *  # noqa: F401,F403,E402
from tests.test_system import __doc__ as _real_doc  # noqa: F401,E402

__doc__ = _real_doc

if __name__ == "__main__":
    _target = _os.path.join(_THIS_DIR, "tests", "test_system.py")
    _runpy.run_path(_target, run_name="__main__")
