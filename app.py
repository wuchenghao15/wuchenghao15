#!/usr/bin/env python3
"""MTSCOS AI Project Main Application"""

import os
import sys
import time

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

try:
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception as _e:
    sys.stderr.write(f"[WARN] db_path patch failed: {_e}\n")

# _path_setup.py 已归档至 _config/，注入 _config 目录后再 import
_config_dir = os.path.join(_BASE_DIR, '_config')
if _config_dir not in sys.path:
    sys.path.insert(0, _config_dir)

import _path_setup

print(f"[DEBUG START] app.py started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

import logging
import traceback
import argparse
import sqlite3
# 原 smart_db_router_simple 是一层薄封装，直接导入真实模块以触发相同的路径 patch/路由注册副作用
from core.services import smart_db_router as smart_db_router_simple  # noqa: F401
import hashlib
import time
import json
import random
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from flask import jsonify, render_template, request, redirect, session, make_