"""_governance_helpers — AI 治理中心共享辅助函数

供 eigenflux_routes / brain_bank_routes / neural_array_routes / devflow_routes 复用:
  - 数据库连接 (SSOT: _runtime/databases/Database/app.db)
  - 权限校验 (登录/管理员)
  - 安全查询 (row_factory=sqlite3.Row, 异常吞并返回空列表)
  - 行转 dict / 分页

遵循:
  - 开发规则.md SSOT 原则 (数据库为唯一权威源, 禁止假数据)
  - 用户权限.md @system_container 装饰器 (此处用辅助函数式校验, 与 maintenance_routes 一致)
"""
from __future__ import annotations

import os
import sqlite3
from typing import Any, Iterable

from flask import jsonify, request


def _project_root() -> str:
    """返回项目根目录 (flask-app 的父目录)"""
    # 本文件位于 flask-app/routes/_governance_helpers.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_db_path() -> str:
    """获取主库路径 (SSOT: _runtime/databases/Database/app.db)

    失败回退到 core.db_path.get_db_path (若可用)
    """
    try:
        from core.db_path import get_db_path
        p = get_db_path('app.db')
        if p and os.path.exists(p):
            return p
    except Exception:
        pass
    return os.path.join(_project_root(), '_runtime', 'databases', 'Database', 'app.db')


def _get_conn(read_only: bool = True):
    """获取数据库连接 (默认只读, 避免误写)"""
    path = _get_db_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f'数据库不存在: {path}')
    uri = f'file:{path}?mode=ro' if read_only else f'file:{path}?mode=rwc'
    conn = sqlite3.connect(uri, uri=True, timeout=3)
    conn.row_factory = sqlite3.Row
    return conn


def _query(sql: str, args: Iterable = (), limit: int | None = None) -> list[dict]:
    """安全执行 SELECT 查询, 返回 list[dict]. 失败返回空列表 (禁止抛异常打断请求)."""
    try:
        with _get_conn(read_only=True) as c:
            cur = c.execute(sql, tuple(args))
            rows = cur.fetchmany(limit) if limit else cur.fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def _query_one(sql: str, args: Iterable = ()) -> dict | None:
    """安全查询单行, 返回 dict 或 None"""
    try:
        with _get_conn(read_only=True) as c:
            cur = c.execute(sql, tuple(args))
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception:
        return None


def _count(table: str, where: str = '', args: Iterable = ()) -> int:
    """安全 COUNT 查询, 失败返回 0"""
    try:
        sql = f'SELECT COUNT(*) AS n FROM "{table}"'
        if where:
            sql += f' WHERE {where}'
        r = _query_one(sql, args)
        return int((r or {}).get('n', 0)) if r else 0
    except Exception:
        return 0


def _table_exists(table: str) -> bool:
    """检查表是否存在"""
    try:
        r = _query_one(
            "SELECT name AS n FROM sqlite_master WHERE type='table' AND name=?",
            (table,))
        return bool(r)
    except Exception:
        return False


def _current_safe_user() -> dict:
    """获取当前登录用户 (从 server_real_db 复用, 失败返回空 dict)"""
    try:
        from server_real_db import _current_safe_user as _f
        u = _f() or {}
        if not u or not u.get('logged_in'):
            # 兼容直接从 session 读取
            try:
                from flask import session
                if session.get('logged_in'):
                    u = {
                        'logged_in': True,
                        'username': session.get('username', ''),
                        'role': session.get('role_canonical', session.get('role', 'user')),
                        'is_super_admin': bool(session.get('username') == 'wuchenghao15'),
                    }
            except Exception:
                pass
        return u if u else {}
    except Exception:
        try:
            from flask import session
            if session.get('logged_in'):
                return {
                    'logged_in': True,
                    'username': session.get('username', ''),
                    'role': session.get('role_canonical', session.get('role', 'user')),
                    'is_super_admin': bool(session.get('username') == 'wuchenghao15'),
                }
        except Exception:
            return {}


def _check_login() -> tuple[bool, dict, tuple | None]:
    """校验登录. 返回 (ok, user, error_response)"""
    u = _current_safe_user()
    if not u.get('logged_in'):
        return False, u, (401, {'success': False, 'message': '未登录'})
    return True, u, None


def _check_admin() -> tuple[bool, dict, tuple | None]:
    """校验管理员. 超级管理员 wuchenghao15 无条件放行"""
    ok, u, err = _check_login()
    if not ok:
        return ok, u, err
    if u.get('is_super_admin'):
        return True, u, None
    role = (u.get('role') or '').lower()
    if role in ('super_admin', 'sadmin', 'admin', 'school_admin', 'sysadmin'):
        return True, u, None
    return False, u, (403, {'success': False, 'message': '需要管理员权限'})


def _ok(data: dict | list, **extra) -> 'jsonify':
    """统一成功响应"""
    payload = {'success': True}
    if isinstance(data, dict):
        payload.update(data)
    else:
        payload['items'] = data
    if extra:
        payload.update(extra)
    return jsonify(payload)


def _fail(msg: str, code: int = 500) -> 'jsonify':
    """统一失败响应"""
    return jsonify({'success': False, 'message': msg}), code


def _arg_int(name: str, default: int = 0, minimum: int = 0, maximum: int = 1000) -> int:
    """安全获取整数参数"""
    try:
        v = request.args.get(name, type=int)
        if v is None:
            return default
        v = int(v)
        if minimum is not None:
            v = max(minimum, v)
        if maximum is not None:
            v = min(maximum, v)
        return v
    except Exception:
        return default


def _arg_str(name: str, default: str = '', max_len: int = 200) -> str:
    """安全获取字符串参数"""
    v = request.args.get(name, default) or default
    v = str(v).strip()[:max_len]
    return v
