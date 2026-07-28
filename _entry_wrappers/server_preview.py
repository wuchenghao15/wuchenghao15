#!/usr/bin/env python3
"""薄封装：实际代码已迁入 entrypoints/server_preview.py。
保持旧路径的导入 (`import server_preview`) 与 CLI (`python3 server_preview.py`) 行为不变。
"""
from __future__ import annotations

import os as _os
import runpy as _runpy
import sys as _sys

_THIS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _THIS_DIR not in _sys.path:
    _sys.path.insert(0, _THIS_DIR)

from entrypoints.server_preview import *  # noqa: F401,F403,E402
from entrypoints.server_preview import __doc__ as _real_doc  # noqa: F401,E402

__doc__ = _real_doc

if __name__ == "__main__":
    _target = _os.path.join(_THIS_DIR, "entrypoints", "server_preview.py")
    _runpy.run_path(_target, run_name="__main__")
