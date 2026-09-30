#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""孤儿模块挂载器 (M1) - 系统正规化治理核心组件

功能:
  1. 扫描 ai_engines/ 下所有 .py 模块
  2. 智能分类 (引擎/员工/代理/工具/服务)
  3. 容错 import + 注册到主库 mt_orphan_mount_registry
  4. 提供统一调度接口 get_module/get_all_by_category/health_check
  5. 挂载后供治理中枢/EigenFlux/决策引擎统一调用

使用:
  from ai_engines.orphan_module_loader import OrphanModuleLoader
  loader = OrphanModuleLoader()
  report = loader.mount_all()          # 挂载全部孤儿
  mod = loader.get_module("ai_engine") # 按名获取
  engines = loader.list_by_category("engine")  # 按类获取
"""
from __future__ import annotations
import importlib
import inspect
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("orphan_module_loader")

AI_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = AI_DIR.parent
MAIN_DB = os.environ.get(
    "MT_MAIN_DB_PATH",
    str(AI_DIR / "app.db"),
)

# 已知的非业务模块 (基础设施, 不参与挂载计数)
_SKIP = {
    "__init__", "_cron_engine_runner", "schema_aligner",
    "log_action_decision_engine", "ai_governance_db",
    "pcap_anomaly_parser", "orphan_module_loader",
}

# 分类规则 (按文件名关键词)
_CATEGORY_RULES = [
    ("engine", ["engine", "core", "system"]),
    ("employee", ["employee", "worker", "staff"]),
    ("agent", ["agent"]),
    ("service", ["service", "manager", "controller"]),
    ("question_exam", ["question", "exam", "test", "grade", "homework"]),
    ("security", ["security", "safe", "vulnerability", "cybersecurity"]),
    ("maintenance", ["maintenance", "auto", "upgrade", "repair", "fix", "healing"]),
    ("data_db", ["db", "data", "sync", "cloud", "schema"]),
    ("learning", ["learning", "train", "self", "reinforcement", "federated", "meta"]),
    ("monitor", ["monitor", "analyz", "log", "patrol", "audit"]),
    ("utils", ["util", "helper", "common", "base", "config", "settings"]),
]


def _classify(name: str) -> str:
    nl = name.lower()
    for cat, keywords in _CATEGORY_RULES:
        if any(kw in nl for kw in keywords):
            return cat
    return "other"


def _extract_classes(module) -> List[str]:
    """提取模块中的公开类名 (用于调度提示)."""
    try:
        return [name for name, obj in inspect.getmembers(module, inspect.isclass)
                if obj.__module__ == module.__name__ and not name.startswith("_")]
    except Exception:
        return []


class OrphanModuleLoader:
    """孤儿模块统一挂载器."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or MAIN_DB
        self._cache: Dict[str, Any] = {}
        self._registry: List[Dict[str, Any]] = []
        # 确保 ai_engines 在 path
        ai_str = str(AI_DIR)
        if ai_str not in sys.path:
            sys.path.insert(0, ai_str)
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

    def _ensure_table(self, conn: sqlite3.Connection):
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_orphan_mount_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT UNIQUE,
            category TEXT,
            file_path TEXT,
            mounted INTEGER DEFAULT 0,
            class_names TEXT,
            error TEXT,
            mounted_at TEXT,
            last_health TEXT,
            health_ok INTEGER DEFAULT 0,
            call_count INTEGER DEFAULT 0
        )""")
        conn.commit()

    def scan_all(self) -> List[Dict[str, Any]]:
        """扫描 ai_engines/ 下所有 .py 模块 (排除 __init__ 和已知基础设施)."""
        modules = []
        for p in sorted(AI_DIR.glob("*.py")):
            name = p.stem
            if name in _SKIP or name.startswith("__"):
                continue
            modules.append({
                "name": name,
                "category": _classify(name),
                "file": str(p),
                "size": p.stat().st_size,
            })
        return modules

    def mount_one(self, name: str, category: str = "") -> Dict[str, Any]:
        """挂载单个模块: import + 提取类 + 注册主库."""
        cat = category or _classify(name)
        try:
            # 优先 ai_engines.X, 失败则直接 X
            mod = None
            for full in (f"ai_engines.{name}", name):
                try:
                    mod = importlib.import_module(full)
                    break
                except Exception:
                    continue
            if mod is None:
                raise ImportError(f"无法 import: {name}")
            classes = _extract_classes(mod)
            self._cache[name] = mod
            return {
                "name": name, "category": cat, "mounted": True,
                "classes": classes, "error": None,
                "mounted_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "name": name, "category": cat, "mounted": False,
                "classes": [], "error": f"{type(e).__name__}: {e}",
                "mounted_at": datetime.now().isoformat(),
            }

    def mount_all(self) -> Dict[str, Any]:
        """挂载全部孤儿模块, 返回报告."""
        t0 = time.time()
        modules = self.scan_all()
        results = []
        ok = 0
        fail = 0
        by_cat: Dict[str, int] = {}

        # 写入主库
        conn = sqlite3.connect(self.db_path, timeout=15)
        self._ensure_table(conn)
        for m in modules:
            r = self.mount_one(m["name"], m["category"])
            results.append(r)
            if r["mounted"]:
                ok += 1
                by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
            else:
                fail += 1
            # upsert 主库
            conn.execute("""INSERT OR REPLACE INTO mt_orphan_mount_registry
                (module_name, category, file_path, mounted, class_names, error, mounted_at, health_ok)
                VALUES (?,?,?,?,?,?,?,?)""",
                (r["name"], r["category"], m["file"],
                 1 if r["mounted"] else 0,
                 json.dumps(r["classes"], ensure_ascii=False),
                 r["error"], r["mounted_at"],
                 1 if r["mounted"] else 0))
        conn.commit()
        conn.close()

        self._registry = results
        return {
            "total": len(modules),
            "mounted_ok": ok,
            "mounted_fail": fail,
            "by_category": by_cat,
            "took_sec": round(time.time() - t0, 2),
            "results": results,
            "at": datetime.now().isoformat(),
        }

    def get_module(self, name: str):
        """按名获取已挂载模块 (含懒加载)."""
        if name in self._cache:
            return self._cache[name]
        r = self.mount_one(name)
        return self._cache.get(name)

    def list_by_category(self, category: str) -> List[str]:
        """按类别列出已挂载模块名."""
        return [r["name"] for r in self._registry
                if r["category"] == category and r["mounted"]]

    def health_check(self) -> Dict[str, Any]:
        """健康检查: 统计已挂载/失败/分类分布."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            total = conn.execute("SELECT COUNT(*) FROM mt_orphan_mount_registry").fetchone()[0]
            ok = conn.execute("SELECT COUNT(*) FROM mt_orphan_mount_registry WHERE mounted=1").fetchone()[0]
            fail = conn.execute("SELECT COUNT(*) FROM mt_orphan_mount_registry WHERE mounted=0").fetchone()[0]
            cats = conn.execute("""SELECT category, COUNT(*) FROM mt_orphan_mount_registry
                                   WHERE mounted=1 GROUP BY category ORDER BY COUNT(*) DESC""").fetchall()
        except Exception:
            total = ok = fail = 0
            cats = []
        conn.close()
        return {
            "total": total, "mounted": ok, "failed": fail,
            "mount_rate": f"{round(ok*100/max(total,1),1)}%",
            "by_category": dict(cats),
        }


# 模块级便捷实例 (供治理中枢直接 import)
_loader_instance: Optional[OrphanModuleLoader] = None


def get_loader() -> OrphanModuleLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = OrphanModuleLoader()
    return _loader_instance


def mount_all_orphans() -> Dict[str, Any]:
    """一键挂载全部孤儿模块 (治理中枢/决策引擎调用入口)."""
    return get_loader().mount_all()


def orphan_health() -> Dict[str, Any]:
    """孤儿挂载健康度 (治理面板调用)."""
    return get_loader().health_check()


if __name__ == "__main__":
    import pprint
    print("=== 孤儿模块挂载器 - 自检 ===")
    loader = OrphanModuleLoader()
    report = loader.mount_all()
    print(f"总数: {report['total']}")
    print(f"挂载成功: {report['mounted_ok']}")
    print(f"挂载失败: {report['mounted_fail']}")
    print(f"耗时: {report['took_sec']}s")
    print("分类分布:")
    pprint.pprint(report["by_category"])
    print("\n健康检查:")
    pprint.pprint(loader.health_check())
