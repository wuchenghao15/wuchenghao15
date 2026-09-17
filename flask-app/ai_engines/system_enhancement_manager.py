#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SystemEnhancementManager — 系统增强管理器（轻量骨架）
========================================================
modular_start.py stage 4 调用此模块注册默认数据：
  - allocate_port(name, preferred)
  - manage_db_cluster(action, node_dict)
  - manage_ai_nodes(action, node_dict)
  - manage_layout_config(action, layout_dict)
  - manage_permission_rules(action, rule_dict)
  - register_model(model_dict)

实现策略：
  - 所有数据落 SQLite（懒建表 + 内存缓存兜底）
  - 表名 system_enhancement_* 各自独立，便于审计
  - 单例模式：`system_enhancement_manager`
"""

from __future__ import annotations

import os
import sys
import json
import time
import sqlite3
import threading
from typing import Dict, List, Any, Optional

_LOCK = threading.RLock()


def _get_db():
    """优先走 core.db_path，失败时回退到本地 app.db"""
    try:
        from core.db_path import get_db_path
        return get_db_path('app.db')
    except Exception:
        return 'app.db'


def _ensure_schema(conn):
    """懒创建 6 张表"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS se_ports (
            name TEXT PRIMARY KEY,
            port INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS se_db_cluster (
            node_id TEXT PRIMARY KEY,
            node_type TEXT,
            address TEXT,
            status TEXT,
            load REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS se_ai_nodes (
            node_id TEXT PRIMARY KEY,
            node_name TEXT,
            model TEXT,
            status TEXT,
            load REAL DEFAULT 0.0,
            capacity INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS se_layout_config (
            layout_id TEXT PRIMARY KEY,
            layout_name TEXT,
            config TEXT,
            theme TEXT,
            is_active INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS se_permission_rules (
            rule_id TEXT PRIMARY KEY,
            role TEXT,
            resource TEXT,
            action_name TEXT,
            allowed INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS se_models (
            model_id TEXT PRIMARY KEY,
            model_name TEXT,
            version TEXT,
            status TEXT,
            performance_score REAL DEFAULT 0.0,
            config TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)


class SystemEnhancementManager:
    """系统增强管理器单例"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Dict[str, Any]]] = {
            'ports': {}, 'db_cluster': {}, 'ai_nodes': {},
            'layout': {}, 'permission_rules': {}, 'models': {},
        }
        # 懒建表（首次访问触发）
        try:
            with self._conn() as c:
                _ensure_schema(c)
        except Exception:
            pass  # DB 不可用时降级到纯内存

    def _conn(self):
        conn = sqlite3.connect(_get_db(), timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------- 端口分配 ----------
    def allocate_port(self, name: str, preferred: int = 0) -> Dict[str, Any]:
        """分配/注册端口，优先使用 preferred"""
        port = int(preferred) if preferred else self._next_free_port()
        row = {'name': name, 'port': port, 'status': 'active'}
        with _LOCK:
            self._cache['ports'][name] = row
            try:
                with self._conn() as c:
                    _ensure_schema(c)
                    c.execute(
                        "INSERT OR REPLACE INTO se_ports(name, port, status) VALUES(?,?,?)",
                        (name, port, 'active'))
                    c.commit()
            except Exception:
                pass
        return {'success': True, **row}

    def _next_free_port(self) -> int:
        return 8888  # 兜底默认值

    # ---------- DB 集群 ----------
    def manage_db_cluster(self, action: str, node: Dict[str, Any]) -> Dict[str, Any]:
        return self._generic_upsert('se_db_cluster', 'node_id', action, node, self._cache['db_cluster'])

    # ---------- AI 节点 ----------
    def manage_ai_nodes(self, action: str, node: Dict[str, Any]) -> Dict[str, Any]:
        return self._generic_upsert('se_ai_nodes', 'node_id', action, node, self._cache['ai_nodes'])

    # ---------- 布局配置 ----------
    def manage_layout_config(self, action: str, layout: Dict[str, Any]) -> Dict[str, Any]:
        return self._generic_upsert('se_layout_config', 'layout_id', action, layout, self._cache['layout'])

    # ---------- 权限规则 ----------
    def manage_permission_rules(self, action: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        return self._generic_upsert('se_permission_rules', 'rule_id', action, rule, self._cache['permission_rules'])

    # ---------- 模型注册 ----------
    def register_model(self, model: Dict[str, Any]) -> Dict[str, Any]:
        return self._generic_upsert('se_models', 'model_id', 'upsert', model, self._cache['models'])

    # ---------- 通用 upsert ----------
    def _generic_upsert(self, table: str, pk: str, action: str,
                         data: Dict[str, Any], cache: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """通用 upsert 实现，处理 add/upsert/delete 三种动作"""
        if not isinstance(data, dict):
            return {'success': False, 'error': 'data 必须是 dict'}
        key = data.get(pk)
        if not key:
            return {'success': False, 'error': f'缺少主键字段 {pk}'}

        with _LOCK:
            if action == 'delete':
                cache.pop(str(key), None)
                try:
                    with self._conn() as c:
                        _ensure_schema(c)
                        c.execute(f"DELETE FROM {table} WHERE {pk}=?", (str(key),))
                        c.commit()
                except Exception:
                    pass
                return {'success': True, 'action': 'delete', pk: key}

            # add / upsert（都按 INSERT OR REPLACE 处理）
            # 序列化 config 字段（如果是 dict）
            row = dict(data)
            for k, v in list(row.items()):
                if isinstance(v, (dict, list)):
                    row[k] = json.dumps(v, ensure_ascii=False)

            cache[str(key)] = row
            try:
                with self._conn() as c:
                    _ensure_schema(c)
                    cols = list(row.keys())
                    placeholders = ','.join(['?'] * len(cols))
                    col_str = ','.join(cols)
                    # INSERT OR REPLACE 保持幂等
                    sql = f"INSERT OR REPLACE INTO {table} ({col_str}) VALUES ({placeholders})"
                    c.execute(sql, [row[c_] for c_ in cols])
                    c.commit()
            except Exception as e:
                # DB 失败不影响内存缓存
                return {'success': True, 'action': action, pk: key, 'warning': f'db skipped: {e}'}

        return {'success': True, 'action': action, pk: key}

    # ---------- 查询接口（供 API 层使用） ----------
    def list_ports(self) -> List[Dict[str, Any]]:
        return list(self._cache['ports'].values())

    def list_db_cluster(self) -> List[Dict[str, Any]]:
        return list(self._cache['db_cluster'].values())

    def list_ai_nodes(self) -> List[Dict[str, Any]]:
        return list(self._cache['ai_nodes'].values())

    def list_layouts(self) -> List[Dict[str, Any]]:
        return list(self._cache['layout'].values())

    def list_permission_rules(self) -> List[Dict[str, Any]]:
        return list(self._cache['permission_rules'].values())

    def list_models(self) -> List[Dict[str, Any]]:
        return list(self._cache['models'].values())

    def stats(self) -> Dict[str, Any]:
        return {
            'ports': len(self._cache['ports']),
            'db_cluster': len(self._cache['db_cluster']),
            'ai_nodes': len(self._cache['ai_nodes']),
            'layouts': len(self._cache['layout']),
            'permission_rules': len(self._cache['permission_rules']),
            'models': len(self._cache['models']),
        }


# 单例：兼容 "from ai_engines.system_enhancement_manager import system_enhancement_manager"
system_enhancement_manager = SystemEnhancementManager()

__all__ = ['system_enhancement_manager', 'SystemEnhancementManager']
