#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
治理中枢管理面板 Blueprint (sys_admin_app 挂载友好)
- 路由前缀: /admin_app/governance
- 权限装饰器: admin_emp_guard (骨架, 真实项目中从 sys_admin_auth_routes 导入)
- 双模式: HTML 页面 + JSON API (?fmt=json)
- 数据源: OneDrive 主库 (schema_aligner 兼容口径 + 3 VIEW)
功能:
  GET  /admin_app/governance/dashboard          面板首页(8表统计 + 最近决策 + 最近动作)
  GET  /admin_app/governance/decisions          决策历史列表 (分页)
  GET  /admin_app/governance/decision/<id>      单条决策 + 关联动作
  GET  /admin_app/governance/actions            动作历史列表
  GET  /admin_app/governance/action/<id>        单条动作
  GET  /admin_app/governance/brain              脑库投喂 (兼容视图)
  GET  /admin_app/governance/schema_status      schema 对齐报告
  POST /admin_app/governance/run_decision_now   立即触发决策引擎 (需管理员审批)
"""
from __future__ import annotations

import functools
from app.middlewares.system_container import system_container
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional
class _GP_DictObj(dict):
    """dict 子类: 同时支持 d['k'] / d.get(...) / d.items() / d.k 点访问。"""
    __slots__ = ()
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e
    def __setattr__(self, name, value):
        self[name] = value
    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError as e:
            raise AttributeError(name) from e

def _gp_wrap(obj):
    if isinstance(obj, _GP_DictObj):
        # 递归一次内部
        for k,v in obj.items():
            obj[k] = _gp_wrap(v)
        return obj
    if isinstance(obj, dict):
        return _GP_DictObj({k: _gp_wrap(v) for k,v in obj.items()})
    if isinstance(obj, list):
        return [_gp_wrap(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_gp_wrap(x) for x in obj)
    return obj

def _gp_wrap_template_data(data: dict):
    out = dict(data)
    for k,v in list(out.items()):
        if k.startswith('_'):
            continue
        if isinstance(v,(dict,list,tuple)):
            out[k] = _gp_wrap(v)
    return out


from flask import (Blueprint, abort, flash, g, jsonify, redirect,
                   render_template, request, url_for)
from app.middlewares.system_container import system_container

# 把项目根 / cron 目录加到 path (允许蓝图独立运行 flask --app 模式)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HERE = os.path.dirname(os.path.abspath(__file__));_PROJECT = os.path.dirname(_HERE);_AI = os.path.join(_PROJECT, "ai_engines")
for _p in (_PROJECT, _AI):
    if _p not in sys.path: sys.path.insert(0, _p)
if not os.environ.get("MT_USE_MAIN_DB"): os.environ["MT_USE_MAIN_DB"] = "1"
_MAIN_DB_DEFAULT = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/ai_engines/app.db'
if _MAIN_DB_DEFAULT and not os.environ.get("MT_MAIN_DB_PATH"): os.environ["MT_MAIN_DB_PATH"] = _MAIN_DB_DEFAULT


try:
    import schema_aligner as _al
except Exception:
    from ai_engines import schema_aligner as _al
try:
    import ai_governance_db as _db_local
except Exception:
    from ai_engines import ai_governance_db as _db_local

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
governance_panel_bp = Blueprint(
    "governance_panel", __name__,
    template_folder=os.path.join(_PROJECT_ROOT, "templates", "governance"),
    static_folder=None,
    url_prefix="/admin_app/governance",
)
bp = governance_panel_bp  # 别名，向后兼容

SCRIPT_DIR = _PROJECT_ROOT
CRON_SH = os.path.join(SCRIPT_DIR, "run_log_decision_cron.sh")

# ============== 权限装饰器: 真实项目从 sys_admin_auth_routes 导入, 否则降级 ==============
try:
    # 尝试从主项目 sys_admin_auth_routes 导入管理员装饰器
    _import_ok = False
    for _p in [
        os.path.expanduser("~/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/ai_engines"),
    ]:
        if os.path.isdir(_p):
            sys.path.insert(0, _p)
    from sys_admin_auth_routes import admin_emp_guard as _real_guard  # type: ignore
    _import_ok = True
except Exception:
    _import_ok = False


def admin_emp_guard(role_min: str = "AI_ADMIN"):
    """
    管理员装饰器.
    - 若主项目 sys_admin_auth_routes 可用 → 复用其 admin_emp_guard (走员工登录/角色铁律).
    - 否则 (蓝图独立模式) → 走 MT_GOV_DEV_TOKEN 环境变量比对 (仅供本地开发预览).
    """
    def wrapper(fn):
        if _import_ok:
            # 主项目模式: 复用已有 admin_emp_guard (审批记录自动写 mt_ai_intervene_audit)
            return _real_guard(fn)
        # 独立开发模式: dev token (Bearer 或 ?token=)
        @functools.wraps(fn)
        def wrapped(*a, **kw):
            expected = os.environ.get("MT_GOV_DEV_TOKEN")
            if not expected:
                # 未配置令牌: 开发模式无保护, 仅提示 flash
                g.gov_mode = "dev_unprotected"
                return fn(*a, **kw)
            got = (request.headers.get("Authorization", "")
                   .replace("Bearer ", "").strip()) or request.args.get("token", "").strip()
            if got != expected:
                abort(403, description="治理面板需要 MT_GOV_DEV_TOKEN 令牌")
            g.gov_mode = "dev_token"
            return fn(*a, **kw)
        return wrapped
    return wrapper


# ============== 工具: 主库/本地库二择 查询 ==============
def _db_mode() -> str:
    """返回 'main'(OneDrive主库) 或 'local'(本地独立库)."""
    if os.environ.get("MT_USE_MAIN_DB") == "1":
        return "main"
    # 默认优先主库, 若失败回退本地
    try:
        if os.path.exists(_al.MAIN_DB):
            return "main"
    except Exception:
        pass
    return "local"


def _qc(sql: str, params=(), limit: Optional[int] = None):
    """安全查询: SQL 中不允许拼接用户输入进入关键字段(由白名单表和参数绑定保证)."""
    mode = _db_mode()
    try:
        if mode == "main":
            conn = _al.main_conn()
        else:
            conn = _db_local.get_conn()
        try:
            cur = conn.execute(sql, params)
            rows = cur.fetchall() if limit is None else cur.fetchmany(limit)
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as e:
        return [{"_error": str(e)}]


def _stats() -> Dict[str, Any]:
    if _db_mode() == "main":
        try:
            return _al.main_stats()
        except Exception as e:
            return {"error": str(e)}
    return _db_local.stats()


# ============== 渲染辅助: HTML / JSON 自动切换 ==============
_schema_ready_flag = {"done": False}
def _respond(html_tpl: str, **data):
    if not _schema_ready_flag["done"] and _db_mode() == "main":
        try:
            _al.ensure_schema_ready()
            _schema_ready_flag["done"] = True
        except Exception:
            pass
    # 基础变量统一注入
    if "_db_mode" not in data:
        data["_db_mode"] = _db_mode()
    if "_now" not in data:
        data["_now"] = datetime.now().isoformat(timespec="seconds")
    if "_nav" not in data:
        # 导航项: (endpoint 后缀, 显示名)
        data["_nav"] = [
            ("dashboard", "仪表板"),
            ("decisions_list", "决策历史"),
            ("actions_list", "动作历史"),
            ("brain_list", "脑库投喂"),
            ("schema_status", "Schema 对齐"),
        ]
    # base.html 使用的 endpoint 前缀拼法是 governance_panel.<suffix>
    data["_nav_items"] = [
        ("governance_panel." + ep, label)
        for ep, label in data["_nav"]
    ]
    if request.args.get("fmt") == "json":
        return jsonify(data)
    tpl_data = _gp_wrap_template_data(data)
    return render_template(html_tpl, **tpl_data)


# ============== 路由 ==============

# --- 根路径 /admin_app/governance/ → redirect 到 /dashboard ---
@bp.route("/", methods=["GET"])
def governance_root_redirect():
    """治理中枢根路径 → 统一 redirect 到 dashboard"""
    return redirect("/admin_app/governance/dashboard")

@system_container(require_auth='login')
@bp.route("/dashboard")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def dashboard():
    stats = _stats()
    # 最近决策 20 条
    decisions = _qc(
        "SELECT * FROM mt_ai_decision_log ORDER BY decided_at DESC LIMIT ?", (20,))
    # 最近动作 20 条 (成功/失败)
    actions = _qc(
        "SELECT * FROM mt_ai_action_log ORDER BY executed_at DESC LIMIT ?", (20,))
    # 最近脑库 10 条
    brain_src = ("v_governance_mt_ai_brain_feed_log"
                 if _db_mode() == "main" else "mt_ai_brain_feed_log")
    brains = _qc(f"SELECT * FROM {brain_src} ORDER BY created_at DESC LIMIT ?", (10,))
    # 动作分布 (最近 24h)
    act_dist = _qc(
        "SELECT action, SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) AS ok_count,"
        " COUNT(*) AS total FROM mt_ai_action_log "
        "WHERE executed_at >= datetime('now','-1 day') GROUP BY action ORDER BY total DESC"
    )
    # 决策信号分布 (最近 24h)
    sig_dist = _qc(
        "SELECT signal, COUNT(*) AS n FROM mt_ai_decision_log "
        "WHERE decided_at >= datetime('now','-1 day') GROUP BY signal ORDER BY n DESC"
    )
    for r in act_dist:
        total = max(int(r.get("total") or 0), 1)
        ok = int(r.get("ok_count") or 0)
        r["pct_ok"] = int(round(ok * 100 / total))
        r["pct_bad"] = 100 - r["pct_ok"]
    return _respond(
        "dashboard.html",
        stats=stats, decisions=decisions, actions=actions, brains=brains,
        act_dist=act_dist, sig_dist=sig_dist,
    )


@bp.route("/decisions")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def decisions_list():
    page = max(1, int(request.args.get("page", "1")))
    size = min(200, max(5, int(request.args.get("size", "50"))))
    offset = (page - 1) * size
    where_sql, params = _build_filter_sql(
        request.args, allow_fields={"signal", "action", "severity", "consensus_pass"},
        bool_fields={"consensus_pass"},
    )
    total = _qc(f"SELECT COUNT(*) AS c FROM mt_ai_decision_log {where_sql}", params)[0].get("c", 0)
    rows = _qc(
        f"SELECT * FROM mt_ai_decision_log {where_sql}"
        f" ORDER BY decided_at DESC LIMIT ? OFFSET ?",
        tuple(list(params) + [size, offset]),
    )
    return _respond(
        "decisions.html",
        rows=rows, page=page, size=size, total=total,
        pages=((total + size - 1) // size) if size > 0 else 1,
        filters=request.args.to_dict(),
    )


@bp.route("/decision/<decision_id>")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def decision_detail(decision_id):
    decs = _qc("SELECT * FROM mt_ai_decision_log WHERE decision_id=?", (decision_id,))
    if not decs:
        abort(404)
    acts = _qc(
        "SELECT * FROM mt_ai_action_log WHERE decision_id=? ORDER BY executed_at ASC",
        (decision_id,),
    )
    return _respond("decision_detail.html", decision=decs[0], actions=acts)


@bp.route("/actions")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def actions_list():
    page = max(1, int(request.args.get("page", "1")))
    size = min(200, max(5, int(request.args.get("size", "50"))))
    offset = (page - 1) * size
    where_sql, params = _build_filter_sql(
        request.args, allow_fields={"action", "success"},
        bool_fields={"success"},
    )
    total = _qc(f"SELECT COUNT(*) AS c FROM mt_ai_action_log {where_sql}", params)[0].get("c", 0)
    rows = _qc(
        f"SELECT * FROM mt_ai_action_log {where_sql}"
        f" ORDER BY executed_at DESC LIMIT ? OFFSET ?",
        tuple(list(params) + [size, offset]),
    )
    return _respond(
        "actions.html",
        rows=rows, page=page, size=size, total=total,
        pages=((total + size - 1) // size) if size > 0 else 1,
        filters=request.args.to_dict(),
    )


@bp.route("/action/<action_id>")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def action_detail(action_id):
    acts = _qc("SELECT * FROM mt_ai_action_log WHERE action_id=?", (action_id,))
    if not acts:
        abort(404)
    dec_id = acts[0].get("decision_id")
    dec = _qc("SELECT * FROM mt_ai_decision_log WHERE decision_id=?", (dec_id,)) if dec_id else []
    return _respond("action_detail.html", action=acts[0], decision=dec[0] if dec else None)


@bp.route("/brain")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def brain_list():
    page = max(1, int(request.args.get("page", "1")))
    size = min(200, max(5, int(request.args.get("size", "50"))))
    offset = (page - 1) * size
    tbl = "v_governance_mt_ai_brain_feed_log" if _db_mode() == "main" else "mt_ai_brain_feed_log"
    where_sql, params = _build_filter_sql(
        request.args, allow_fields={"category", "source", "flow_id"},
    )
    total = _qc(f"SELECT COUNT(*) AS c FROM {tbl} {where_sql}", params)[0].get("c", 0)
    rows = _qc(
        f"SELECT * FROM {tbl} {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(list(params) + [size, offset]),
    )
    return _respond(
        "brain.html",
        rows=rows, page=page, size=size, total=total,
        pages=((total + size - 1) // size) if size > 0 else 1,
        filters=request.args.to_dict(), table=tbl,
    )


@bp.route("/schema_status")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def schema_status():
    report = {"align": {}, "stats": {}, "views_ok":0, "repaired_column_added":0,
              "new_tables_created":0, "views":[], "new_tables":[], "all_ok":False}
    if _db_mode() == "main":
        try:
            rep = _al.ensure_schema_ready()
            report["align"] = rep
            report["stats"] = _al.main_stats()
            for k in ("views_ok","repaired_column_added","new_tables_created","views",
                       "new_tables","all_ok","new_tables_status","target_db","at"):
                if k in rep: report[k] = rep[k]
        except Exception as e:
            report["error"] = str(e)
    else:
        report["error"] = "当前使用本地库(local),未接入OneDrive主库."
        report["stats"] = _db_local.stats()
    return _respond("schema_status.html", **report)


# 立即触发决策引擎 (需审批)
_trigger_lock = threading.Lock()


@bp.route("/run_decision_now", methods=["POST"])
@system_container(require_auth='login')
@admin_emp_guard("SUPER_ADMIN")  # 立即触发要求更高权限
def run_decision_now():
    with _trigger_lock:
        if not os.path.exists(CRON_SH):
            abort(404, description=f"未找到 cron 脚本: {CRON_SH}")
        try:
            result = subprocess.run(
                ["bash", CRON_SH], capture_output=True, text=True, timeout=120,
                cwd=SCRIPT_DIR,
                env={**os.environ, "MT_GOV_DEADLINE_SEC": "115"},  # 长一点
            )
        except subprocess.TimeoutExpired:
            return jsonify({"status": "timeout", "note": "引擎仍在后台运行, 请稍后查看最新报告"}), 202
    # 返回最新报告链接
    report_dir = os.path.join(SCRIPT_DIR, "_runtime", "cron_reports")
    latest = ""
    try:
        fs = sorted(os.listdir(report_dir), reverse=True)
        latest = next((f for f in fs if f.startswith("report_") and f.endswith(".json")), "")
    except Exception:
        pass
    return jsonify({
        "status": "submitted" if result.returncode == 0 else "non_zero",
        "exit_code": result.returncode,
        "stderr_tail": result.stderr[-300:],
        "latest_report": latest,
        "dashboard_link": url_for("governance_panel.dashboard"),
    })


# ============== 辅助函数 ==============
def _build_filter_sql(args, allow_fields, bool_fields=()):
    """从 ?field=value&field2=value2 构造 WHERE + 绑定参数 (白名单字段防注入)."""
    conds, params = [], []
    for k in sorted(args.keys()):
        if k not in allow_fields:
            continue
        v = args.get(k, "").strip()
        if not v:
            continue
        if k in bool_fields:
            try:
                iv = 1 if v.lower() in {"1", "true", "yes"} else 0
            except Exception:
                iv = 0
            conds.append(f"{k}=?")
            params.append(iv)
        elif "*" in v or "%" in v:
            conds.append(f"{k} LIKE ?")
            params.append(v.replace("*", "%"))
        else:
            conds.append(f"{k}=?")
            params.append(v)
    where_sql = ("WHERE " + " AND ".join(conds)) if conds else ""
    return where_sql, params




# ============== 系统正规化 (M3) ==============
@bp.route("/system_normalization")
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def system_normalization():
    """系统正规化指挥部: 闭环度+孤儿挂载+EigenFlux运维+12步流程"""
    report = {"norm": {}, "orphans": {}, "audit": {}, "eigenflux": {}, "flow": {}, "routes": {}}
    try:
        from system_normalizer import normalize_system, _m4_self_audit_patrol, _m6_route_health_check
        # 即时快照 (不重复挂载)
        report["audit"] = _m4_self_audit_patrol()
        # 孤儿挂载状态
        try:
            from orphan_module_loader import get_loader
            report["orphans"] = get_loader().health_check()
        except Exception as e:
            report["orphans"] = {"error": str(e)}
        # EigenFlux 运维记录
        import sqlite3 as _sq
        _c = _sq.connect(_al.MAIN_DB if hasattr(_al,'MAIN_DB') else _MAIN_DB_DEFAULT, timeout=10)
        try:
            rows = _c.execute("SELECT op_at, op_type, operator, result FROM mt_eigenflux_ops_log ORDER BY op_at DESC LIMIT 10").fetchall()
            report["eigenflux"] = {"recent_ops": [{"at": r[0], "type": r[1], "op": r[2], "result": r[3]} for r in rows]}
        except Exception:
            report["eigenflux"] = {"recent_ops": []}
        # 当前12步流程
        try:
            fr = _c.execute("SELECT flow_id, proposal_title, current_step, final_status, created_at FROM mt_dev_flow_session WHERE flow_id LIKE 'sysnorm_%' ORDER BY created_at DESC LIMIT 1").fetchone()
            if fr:
                report["flow"] = {"flow_id": fr[0], "title": fr[1], "step": fr[2], "status": fr[3], "created": fr[4]}
        except Exception:
            pass
        _c.close()
    except Exception as e:
        report["error"] = str(e)
    return _respond("system_normalization.html", **report)


@bp.route("/system_normalization/remount_orphans", methods=["POST"])
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def remount_orphans():
    """重新挂载孤儿模块 (管理员触发)."""
    try:
        from orphan_module_loader import mount_all_orphans
        r = mount_all_orphans()
        return jsonify({"ok": True, "mounted": r["mounted_ok"], "total": r["total"],
                        "rate": f"{round(r['mounted_ok']*100/max(r['total'],1),1)}%"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route("/system_normalization/eigenflux_consult", methods=["POST"])
@system_container(require_auth='login')
@admin_emp_guard("AI_ADMIN")
def eigenflux_consult():
    """EigenFlux 专家团队会议 (记录到主库)."""
    import sqlite3 as _sq
    from datetime import datetime as _dt
    try:
        topic = request.json.get("topic", "") if request.json else ""
        _c = _sq.connect(_al.MAIN_DB if hasattr(_al,'MAIN_DB') else _MAIN_DB_DEFAULT, timeout=10)
        _c.execute("""INSERT INTO mt_eigenflux_ops_log
            (op_at, op_type, operator, target, result, detail_json)
            VALUES (?,?,?,?,?,?)""",
            (_dt.now().isoformat(), "EXPERT_CONSULT",
             "EigenFlux AI + 杨安AI + 吴美工AI + AI治理中枢",
             topic or "系统正规化运维", "CONSULTED",
             '{"consensus":"进行中","panel":4}'))
        _c.commit()
        _c.close()
        return jsonify({"ok": True, "msg": "EigenFlux专家团队会议已记录"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ============== 蓝图独立运行 (本地预览) ==============
def _build_standalone_app():
    from flask import Flask
    app = Flask(__name__,
                template_folder=os.path.join(SCRIPT_DIR, "templates"),
                static_folder=None)
    app.secret_key = os.environ.get("MT_GOV_SECRET", "dev-secret-change-me")
    app.register_blueprint(bp)

    @app.route("/")
    @system_container(require_auth='login')
    def root():
        return redirect(url_for("governance_panel.dashboard"))

    return app


if __name__ == "__main__":
    app = _build_standalone_app()
    port = int(os.environ.get("MT_GOV_PORT", "5005"))
    print(f"治理面板独立启动: http://127.0.0.1:{port}/admin_app/governance/dashboard  (db_mode={_db_mode()})")
    app.run(host="127.0.0.1", port=port, debug=False)
