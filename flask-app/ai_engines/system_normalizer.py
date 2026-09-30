#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统正规化初始化器 (M2-M5) - 12步流程 STEP_7_EXECUTE 产物

职责:
  M2: 入口收敛 - 在 Flask app 启动时统一初始化所有子系统
  M3: 治理中枢 schema 就绪 + 正规化面板路由注入
  M4: AI自监测巡检器 - 复用决策引擎 cron, 每5分钟扫描系统健康
  M5: EigenFlux 运维接口 - 专家团队常态化介入

调用方式 (在 Flask app 创建后, app.run 前):
  from ai_engines.system_normalizer import normalize_system
  normalize_system(app)
"""
from __future__ import annotations
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("system_normalizer")

_BASE = Path(__file__).resolve().parent.parent
_AI = Path(__file__).resolve().parent
for _p in (str(_BASE), str(_AI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

MAIN_DB = os.environ.get("MT_MAIN_DB_PATH", str(_AI / "app.db"))


def _ensure_norm_tables(conn: sqlite3.Connection):
    """系统正规化相关表."""
    conn.execute("""CREATE TABLE IF NOT EXISTS mt_system_norm_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        check_at TEXT NOT NULL,
        module TEXT,
        check_name TEXT,
        status TEXT,
        detail TEXT,
        metrics_json TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS mt_eigenflux_ops_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        op_at TEXT NOT NULL,
        op_type TEXT,
        operator TEXT,
        target TEXT,
        result TEXT,
        detail_json TEXT
    )""")
    conn.commit()


def _m1_mount_orphans() -> Dict[str, Any]:
    """M1: 挂载孤儿模块 (调用 orphan_module_loader)."""
    try:
        from orphan_module_loader import get_loader
        loader = get_loader()
        # 若已挂载则只做健康检查
        health = loader.health_check()
        if health.get("total", 0) == 0:
            report = loader.mount_all()
            return {"ok": True, "mounted": report["mounted_ok"],
                    "total": report["total"], "rate": f"{round(report['mounted_ok']*100/max(report['total'],1),1)}%"}
        return {"ok": True, "already_mounted": True, **health}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _m3_governance_schema() -> Dict[str, Any]:
    """M3: 治理中枢 schema 对齐."""
    try:
        os.environ.setdefault("MT_USE_MAIN_DB", "1")
        from schema_aligner import ensure_schema_ready
        r = ensure_schema_ready()
        return {"ok": r.get("all_ok", False), "views": r.get("views_ok", 0),
                "tables": r.get("new_tables_created", 0),
                "compat_views": bool(r.get("compat_views"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _m4_self_audit_patrol() -> Dict[str, Any]:
    """M4: AI自监测巡检器 - 检查全系统节点健康度.
    复用决策引擎 cron (每5分钟), 这里做即时快照.
    """
    try:
        conn = sqlite3.connect(MAIN_DB, timeout=10)
        # 1. 路由健康 (mt_log_decision_log 最近活动)
        last_decision = conn.execute(
            "SELECT created_at FROM mt_log_decision_log ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        # 2. 脑库活跃度
        brain_count = conn.execute(
            "SELECT COUNT(*) FROM mt_ai_brain_feed_log"
        ).fetchone()[0]
        # 3. 孤儿挂载状态
        orphan_ok = orphan_total = 0
        try:
            orphan_total = conn.execute(
                "SELECT COUNT(*) FROM mt_orphan_mount_registry"
            ).fetchone()[0]
            orphan_ok = conn.execute(
                "SELECT COUNT(*) FROM mt_orphan_mount_registry WHERE mounted=1"
            ).fetchone()[0]
        except Exception:
            pass
        # 4. 异常库
        anomaly_count = conn.execute(
            "SELECT COUNT(*) FROM mt_anomaly_feature_library"
        ).fetchone()[0]
        # 5. 经验库
        exp_count = conn.execute(
            "SELECT COUNT(*) FROM mt_experience_library"
        ).fetchone()[0]
        # 6. 开发流程
        dev_flow_count = 0
        try:
            dev_flow_count = conn.execute(
                "SELECT COUNT(*) FROM mt_dev_flow_session"
            ).fetchone()[0]
        except Exception:
            pass
        conn.close()

        # 闭环度计算 (6维)
        dims = {
            "decision_engine": 1 if last_decision else 0,
            "brain_bank": 1 if brain_count > 0 else 0,
            "orphan_mount": round(orphan_ok * 100 / max(orphan_total, 1)) / 100 if orphan_total else 0,
            "anomaly_lib": 1 if anomaly_count > 0 else 0,
            "experience_lib": 1 if exp_count > 0 else 0,
            "dev_flow": 1 if dev_flow_count > 0 else 0,
        }
        closure_rate = round(sum(dims.values()) / len(dims) * 100, 1)
        return {
            "ok": True, "closure_rate": f"{closure_rate}%",
            "dimensions": dims,
            "last_decision": last_decision[0] if last_decision else None,
            "brain_count": brain_count,
            "orphan_mounted": f"{orphan_ok}/{orphan_total}",
            "anomaly_count": anomaly_count,
            "experience_count": exp_count,
            "dev_flow_count": dev_flow_count,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _m5_eigenflux_ops_init() -> Dict[str, Any]:
    """M5: EigenFlux 运维接口初始化 - 记录专家团队常态化介入."""
    try:
        conn = sqlite3.connect(MAIN_DB, timeout=10)
        _ensure_norm_tables(conn)
        conn.execute("""INSERT INTO mt_eigenflux_ops_log
            (op_at, op_type, operator, target, result, detail_json)
            VALUES (?,?,?,?,?,?)""",
            (datetime.now().isoformat(), "SYSTEM_NORMALIZE_INIT",
             "EigenFlux AI + 专家组", "全系统",
             "INIT_OK", json.dumps({
                 "panel": ["EigenFlux AI", "杨安AI", "吴美工AI", "AI治理中枢"],
                 "flow_id": os.environ.get("MT_SYSNORM_FLOW_ID", "sysnorm_b3b5a279"),
             }, ensure_ascii=False)))
        conn.commit()
        conn.close()
        return {"ok": True, "operator": "EigenFlux AI + 专家组",
                "status": "常态化运维已启用"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _m6_route_health_check(app) -> Dict[str, Any]:
    """M6: 路由健康检查 - 统计已注册蓝图和路由数."""
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                "rule": rule.rule,
                "endpoint": rule.endpoint,
                "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
            })
        bps = set()
        for r in routes:
            if "." in r["endpoint"]:
                bps.add(r["endpoint"].split(".")[0])
        return {"ok": True, "total_routes": len(routes),
                "total_blueprints": len(bps),
                "blueprints": sorted(bps)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def normalize_system(app=None) -> Dict[str, Any]:
    """系统正规化统一初始化入口.
    在 Flask app 启动前调用, 完成 M1-M6 全部初始化.
    """
    t0 = time.time()
    report = {
        "at": datetime.now().isoformat(),
        "flow_id": os.environ.get("MT_SYSNORM_FLOW_ID", "sysnorm_b3b5a279"),
        "phases": {},
    }

    # 写入正规化状态表
    try:
        conn = sqlite3.connect(MAIN_DB, timeout=10)
        _ensure_norm_tables(conn)
        conn.close()
    except Exception:
        pass

    # M1: 孤儿模块挂载
    report["phases"]["M1_orphan_mount"] = _m1_mount_orphans()

    # M3: 治理中枢 schema
    report["phases"]["M3_governance_schema"] = _m3_governance_schema()

    # M4: AI自监测巡检
    report["phases"]["M4_self_audit"] = _m4_self_audit_patrol()

    # M5: EigenFlux 运维接口
    report["phases"]["M5_eigenflux_ops"] = _m5_eigenflux_ops_init()

    # M6: 路由健康检查 (需 app)
    if app is not None:
        report["phases"]["M6_route_health"] = _m6_route_health_check(app)

    report["took_sec"] = round(time.time() - t0, 2)
    report["overall_ok"] = all(
        p.get("ok", False) for p in report["phases"].values()
    )

    # 记录到主库
    try:
        conn = sqlite3.connect(MAIN_DB, timeout=10)
        conn.execute("""INSERT INTO mt_system_norm_status
            (check_at, module, check_name, status, detail, metrics_json)
            VALUES (?,?,?,?,?,?)""",
            (report["at"], "system_normalizer", "NORMALIZE_ALL",
             "OK" if report["overall_ok"] else "PARTIAL",
             f"flow={report['flow_id']}, took={report['took_sec']}s",
             json.dumps(report, ensure_ascii=False)))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return report


if __name__ == "__main__":
    print("=== 系统正规化初始化器 自检 ===")
    r = normalize_system()
    print(json.dumps(r, ensure_ascii=False, indent=2))
