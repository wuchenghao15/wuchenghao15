#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策引擎 cron runner v2.2.0: 2 分钟 deadline + 主库兼容写入 + JSON 报告 + 自动归档清理.
用法: _cron_engine_runner.py <REPORT_FILE_OUTPUT>
依赖补充: 标准库全内置无需额外安装, 所有内部模块保持原有导入兼容.
"""
import json, os, signal, sys, time, shutil
from datetime import datetime

__version__ = "2.2.0"
report_file = sys.argv[1]
script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(script_dir)
for _p in (script_dir, _project_root):
    if _p not in sys.path: sys.path.insert(0, _p)

# 统一归档目录配置，所有引擎生成文件默认归档到该目录
ARCHIVE_DIR = os.environ.get("MT_UNIFIED_ARCHIVE_DIR", os.path.join(_project_root, "_runtime", "engine_archive"))
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.environ["MT_ENGINE_GENERATE_ROOT"] = ARCHIVE_DIR

os.environ.setdefault("MT_USE_MAIN_DB", "1")
# import 兼容层: 把 ai_engines.* 同步到顶层 sys.modules
import importlib as _gp_imp
for _name in ("schema_aligner","ai_governance_db","log_action_decision_engine","pcap_anomaly_parser","ai_engine_common"):
    _m = sys.modules.get("ai_engines."+_name)
    if _m is None:
        try: _m = _gp_imp.import_module("ai_engines."+_name)
        except Exception:
            try: _m = _gp_imp.import_module(_name)
            except Exception: _m = None
    if _m is not None: sys.modules.setdefault(_name, _m)

# 2 分钟软 deadline: SIGALRM 触发
DEADLINE_SEC = int(os.environ.get("MT_GOV_DEADLINE_SEC", "120"))


class DeadlineHit(Exception):
    pass


def _on_alarm(*a):
    raise DeadlineHit(f"deadline {DEADLINE_SEC}s")

try:
    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(DEADLINE_SEC)
except (ValueError, OSError):
    pass

t0 = time.time()
out = {
    "started_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "version": __version__
}

try:
    import schema_aligner as _al
    import log_action_decision_engine as _lde
    import ai_governance_db as _db

    # 限制扫描范围: 避免 os.walk 卡在 OneDrive 全量扫描
    if not os.environ.get("MT_GOV_SCAN_ROOT"):
        os.environ["MT_GOV_SCAN_ROOT"] = os.path.join(_project_root, "_runtime", "logs")
    # 首次运行确保主库 schema 就绪 (VIEW + repaired 列 + 5 新表 + 列迁移)
    _al.ensure_schema_ready()

    # 切写主库: monkey-patch ai_governance_db 的 8 个 insert + lde 的 2 个 insert
    _db.insert_brain_feed = _al.brain_insert
    _db.insert_anomaly = _al.anomaly_insert
    _db.mark_anomaly_repaired = _al.anomaly_mark_repaired
    _db.insert_experience = _al.experience_insert

    def _repair(*_, **kw): return _al.repair_insert(
        kw.get("anomaly_id"), kw.get("strategy", ""), kw.get("target", ""),
        kw.get("before_hash"), kw.get("after_hash"), bool(kw.get("success")), kw.get("detail", ""))

    def _upgrade(*_, **kw): return _al.upgrade_insert(
        kw.get("target", ""), kw.get("from_version"), kw.get("to_version"),
        kw.get("status", ""), kw.get("rollback_to"), kw.get("detail", ""))

    def _skill(*_, **kw): return _al.skill_insert(
        kw.get("skill_name", ""), kw.get("scenario", ""),
        kw.get("score", 0), bool(kw.get("passed")), kw.get("detail", ""))

    _db.insert_repair_log = _repair
    _db.insert_upgrade_log = _upgrade
    _db.insert_skill_sim = _skill
    _db.insert_decision_log = lambda *_, **kw: _al.decision_insert(**kw)
    _db.insert_action_log   = lambda *_, **kw: _al.action_insert(**kw)

    def _decision(*_, **kw): return _al.decision_insert(**kw)

    def _action(*_, **kw): return _al.action_insert(**kw)

    _lde.insert_decision = _decision
    _lde.insert_action = _action

    out["align"] = _al.align_main_db()
    eng = _lde.LogActionDecisionEngine(max_signals=200, max_actions=100)
    out["decision"] = eng.run_once()
    out["main_db_stats"] = _al.main_stats()
    out["status"] = "ok"
except DeadlineHit as e:
    out["status"] = "deadline"
    out["error"] = str(e)
except Exception as e:
    out["status"] = "error"
    out["error"] = f"{type(e).__name__}: {e}"
    import traceback as _tb
    out["traceback"] = _tb.format_exc()[:1200]
finally:
    try:
        signal.alarm(0)
    except (ValueError, OSError):
        pass

out["scan_root"] = os.environ.get("MT_GOV_SCAN_ROOT", "")
out["duration_sec_real"] = round(time.time() - t0, 2)
out["finished_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
out["unified_archive_dir"] = ARCHIVE_DIR

os.makedirs(os.path.dirname(report_file), exist_ok=True)
with open(report_file, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# 归档本次运行报告到统一归档目录
archive_report_name = f"engine_run_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.json"
shutil.copy2(report_file, os.path.join(ARCHIVE_DIR, archive_report_name))

# 自动扫描并归档所有生成的快文件/包文件到指定目录
report_parent_dir = os.path.dirname(os.path.abspath(report_file))
if os.path.exists(report_parent_dir):
    for fname in os.listdir(report_parent_dir):
        if fname.lower().endswith((".fast", ".pack", ".pkt", ".tmp", ".dat", ".pkg")):
            src_full = os.path.join(report_parent_dir, fname)
            dst_full = os.path.join(ARCHIVE_DIR, f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}_{fname}")
            shutil.move(src_full, dst_full)

# 新增功能：记录日志到文件
with open(os.path.join(ARCHIVE_DIR, "engine_run_log.txt"), "a", encoding="utf-8") as log_file:
    log_file.write(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - v{__version__} - Report saved: {report_file}\n")

# 自动清理归档目录下超过30天的旧文件，避免磁盘占用过高
_archive_cutoff = time.time() - 30 * 86400
for _arch_f in os.listdir(ARCHIVE_DIR):
    _fpath = os.path.join(ARCHIVE_DIR, _arch_f)
    if os.path.isfile(_fpath) and os.path.getmtime(_fpath) < _archive_cutoff:
        try: os.remove(_fpath)
        except: pass

sys.exit(0 if out["status"] == "ok" else 2)
