# -*- coding: utf-8 -*-
"""系统版本单一权威源 (Single Source of Truth for the system version).

版本号只允许有一个事实来源:
    flask-app/VERSION   —— 构建期/代码期权威常量(纯文本, 如 "v22.2.0")

运行时展示权威为数据库 system_versions 表(由 server_real_db.get_version_info
解密读取), 与 VERSION 文件在正式升级流程(§14 步骤10)中被同一处写入并保持一致。

历史教训: 版本号曾在 app/services/version_service.py、core/services/version_manager.py、
services/system_upgrade_engine.py、app/version.py、根 version_manager.py 等多处各自硬编码
(14.0.0 / 18.1.0 / 17.20.0 / v22.11.0 / 15.4.0), 彼此脱节且长期漂移。
现统一收敛: 上述模块一律从本模块派生, 禁止再硬编码系统版本号。

设计约束:
    - 仅依赖标准库(os/re), 不导入 Flask/DB/任何业务模块, 无循环依赖;
    - VERSION 路径按本文件位置(core/version_source.py → ../VERSION)解析, 不依赖工作目录;
    - 任何读取/解析异常都回退安全默认值, 绝不抛错影响导入;
    - 只读暴露, 不在各处缓存可漂移的副本。
"""

import os
import re

# 三级语义化版本: MAJOR.MINOR.PATCH, 允许前导 v 与后缀 tag(如 v22.2.0 / 22.2.0-sysnorm)
_VERSION_RE = re.compile(r'^\s*[vV]?(\d{1,2})\.(\d{1,2})\.(\d{1,3})(?:[.\-+].*)?\s*$')

# VERSION 文件缺失/损坏时的安全回退(与最近一次正式升级保持一致, 仅兜底不做主路径)
_SAFE_FALLBACK = '22.2.0'


def version_file_path():
    """返回 VERSION 文件绝对路径 (flask-app/VERSION)。本文件位于 flask-app/core/。"""
    core_dir = os.path.dirname(os.path.abspath(__file__))
    flask_root = os.path.dirname(core_dir)
    return os.path.join(flask_root, 'VERSION')


def read_raw_version():
    """读取 VERSION 文件原始版本字符串(去首尾空白), 读不到返回 None。"""
    try:
        with open(version_file_path(), 'r', encoding='utf-8') as f:
            txt = f.read().strip()
        return txt or None
    except Exception:
        return None


def parse_version(ver):
    """解析版本串为 (major, minor, patch); 非法返回 None。"""
    if not ver:
        return None
    m = _VERSION_RE.match(str(ver))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def get_version_parts():
    """返回 (major, minor, patch) 整数三元组, 任何异常回退安全默认值。"""
    parts = parse_version(read_raw_version())
    if parts is None:
        parts = parse_version(_SAFE_FALLBACK)
    return parts


def get_system_version():
    """返回核心版本号(无前缀 v), 如 '22.2.0'。任何异常回退安全默认, 绝不抛错。"""
    major, minor, patch = get_version_parts()
    return f'{major}.{minor}.{patch}'


def get_system_version_tagged():
    """返回带 v 前缀的版本号, 如 'v22.2.0'。"""
    return 'v' + get_system_version()


def get_version_info():
    """返回版本信息 dict(major/minor/patch/tag), 供兼容层与前端使用。"""
    major, minor, patch = get_version_parts()
    return {
        'major': major,
        'minor': minor,
        'patch': patch,
        'tag': 'release',
        'version': get_system_version_tagged(),
    }
