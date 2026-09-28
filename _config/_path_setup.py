#!/usr/bin/env python3
r"""
路径初始化 - 在系统启动时添加 services 各子目录到 Python 路径
用于文件整理后保持旧导入路径兼容。

文件重组后本文件归档至 _config/，实际应用代码位于项目根下的 flask-app/。
故 BASE_DIR 必须指向 flask-app（services/、core/services/、ai_engines/ 等真实所在），
否则 bare 导入（`import auth_manager` 等）全部失败。
"""
import os
import sys

# 本文件位于 <项目根>/_config/_path_setup.py，应用根为同级 flask-app/
_SELF_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SELF_DIR)
BASE_DIR = os.path.join(_PROJECT_ROOT, 'flask-app')

# 旧的 bare 导入兼容：core/services/ 与 services/ 顶层均含 auth_manager 等
SERVICE_DIRS = [
    r'core/services',
    r'services',
    r'services/ai',
    r'services/ai_modules',
    r'services/api',
    r'services/copy_hub',
    r'services/data',
    r'services/education',
    r'services/education/campus',
    r'services/education/career',
    r'services/education/community',
    r'services/education/curriculum',
    r'services/education/finance',
    r'services/education/lab',
    r'services/education/library',
    r'services/education/management',
    r'services/education/research',
    r'services/education/security',
    r'services/education/special',
    r'services/education/student',
    r'services/education/info',
    r'services/education/platform',
    r'services/misc',
    r'services/notification',
    r'services/platform',
    r'services/security',
    r'services/student',
    r'services/system',
    # AI 引擎：ai_engine、ai_brain 等为 bare 导入
    r'ai_engines',
    r'ai_engines/ai_engines',
    r'ai_engines/brain',
    r'ai_engines/data',
    r'ai_engines/learning',
    r'ai_engines/management',
    r'ai_engines/monitoring',
    r'ai_engines/security',
    r'ai_engines/utils',
    r'engines',
]

_added = set()


def setup_paths():
    for d in SERVICE_DIRS:
        full_path = os.path.join(BASE_DIR, d)
        if os.path.isdir(full_path) and full_path not in _added:
            sys.path.insert(0, full_path)
            _added.add(full_path)


setup_paths()
