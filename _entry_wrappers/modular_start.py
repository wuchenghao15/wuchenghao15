#!/usr/bin/env python3
"""薄封装：实际代码已迁入 entrypoints/modular_start.py。
保持旧路径的导入 (`import modular_start`) 与 CLI (`python3 modular_start.py`) 行为不变。
"""
from __future__ import annotations

import os as _os
import runpy as _runpy
import sys as _sys

_THIS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _THIS_DIR not in _sys.path:
    _sys.path.insert(0, _THIS_DIR)

# 1) 所有公共符号重导出，保证 `from modular_start import x` 等价
from entrypoints.modular_start import *  # noqa: F401,F403,E402
from entrypoints.modular_start import (  # noqa: F401,E402
    __doc__ as _real_doc,
)

__doc__ = _real_doc

if __name__ == "__main__":
    # 2) CLI 模式：透传到真实入口，保留 __name__ == '__main__' 语义
    _target = _os.path.join(_THIS_DIR, "entrypoints", "modular_start.py")
    _runpy.run_path(_target, run_name="__main__")
