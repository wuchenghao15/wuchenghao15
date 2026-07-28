#!/usr/bin/env python3
"""
路径初始化 - 在系统启动时添加 services 各子目录到 Python 路径
用于文件整理后保持旧导入路径兼容
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICE_DIRS = [
    'core/services',
    'services/ai',
    'services/education',
    'services/education/campus',
    'services/education/career',
    'services/education/community',
    'services/education/curriculum',
    'services/education/finance',
    'services/education/lab',
    'services/education/library',
    'services/education/management',
    'services/education/research',
    'services/education/security',
    'services/education/special',
    'services/education/student',
    'services/education/info',
    'services/education/platform',
    'services/api',
    'services/data',
    'services/misc',
    'services/notification',
    'services/platform',
    'services/security',
    'services/system',
]

_added = set()

def setup_paths():
    for d in SERVICE_DIRS:
        full_path = os.path.join(BASE_DIR, d)
        if os.path.isdir(full_path) and full_path not in _added:
            sys.path.insert(0, full_path)
            _added.add(full_path)

setup_paths()
