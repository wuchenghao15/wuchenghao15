#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI规则自动学习与严格执行引擎 (Rule Learning & Enforcement Engine)
================================================================
flow_id: flow_rule_auto_learn_enforce_20260819_001
§14 STEP_7_EXECUTE 下场实施

核心能力:
  1. 自动学习: 解析.trae/rules/9篇规则 → 提取RULE_META+硬约束 → 投喂AI脑库
  2. 严格执行: 完整性扫描 + 违规检测 + 告警投喂(EigenFlux+脑库+SA)
  3. 绕过检测: 检查bypass_allowed=False的规则是否有绕过尝试
  4. 不可绕开: §14 IRON_RULE bypass_allowed=False, 含超级管理员

复用现有基础设施:
  - rules_engine.parse_all_rules()  解析9篇规则RULE_META
  - rules_engine.run_integrity_scan() 完整性自检
  - rules_engine.alert_violation()  违规告警投喂
  - rules_engine.RuleDB  规则治理表DAO
  - rules_engine.init_tables()  建表

CLI守护模式:
  python3 ai_rule_learning_engine.py start    启动守护进程
  python3 ai_rule_learning_engine.py stop     停止
  python3 ai_rule_learning_engine.py status   查看状态
  python3 ai_rule_learning_engine.py learn    仅学习规则
  python3 ai_rule_learning_engine.py enforce  仅执行检查
  python3 ai_rule_learning_engine.py once     执行一次完整循环

遵循硬约束:
  - §14 IRON_RULE: bypass_allowed=False, 不可绕开
  - 数据库唯一数据源(app.db)
  - 全链路追溯ID
"""
import json
import os
import signal
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
# ---- 路径 & 依赖 ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # flask-app/
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
ENGINES_DIR = os.path.join(ROOT, "engines")
APP_DB = os.path.join(AI_ENGINES_DIR, "app.db")
# 🔧 仙女座 v5.0 fix: 统一指向 Database/app.db 主库 (与 smart_mount_engine 同库)
_MAIN_DB = os.path.join(ROOT, "..", "Database", "app.db")
if os.path.exists(_MAIN_DB):
    APP_DB = _MAIN_DB
RULES_DIR = os.path.join(ROOT, "..", ".trae", "rules")
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
PID_FILE = os.path.join(PID_DIR, "ai_rule_learning_engine.pid")
LOG_FILE = os.path.join(LOG_DIR, "ai_rule_learning_engine.log")

for _d in [LOG_DIR, PID_DIR]:
    os.makedirs(_d, exist_ok=True)

# 导入rules_engine
sys.path.insert(0, AI_ENGINES_DIR)
try:
    from rules_engine import (
        parse_all_rules, validate_rule_meta,
        run_integrity_scan, alert_violation,
        RuleDB, init_tables,
        RULE_REGISTRY,
    )
    from rules_engine.rule_meta import RuleMeta
except ImportError:
    # 兼容直接运行
    sys.path.insert(0, os.path.join(AI_ENGINES_DIR, "rules_engine"))
    # [unused] from rule_meta import parse_all_rules, validate_rule_meta, RuleMeta
    from rule_integrity_scanner import run_integrity_scan
    from rule_violation_alert import alert_violation
    from rule_db import RuleDB, init_tables
    RULE_REGISTRY = {
        "MT_IRON_RULE_12STEPS": "§14强制开发12步骤独立约束规则.md",
        "MT_RULE_DEV": "开发规则.md",
        "MT_RULE_DESIGN": "设计规范.md",
        "MT_RULE_PERM": "用户权限.md",
        "MT_RULE_AI_OPS": "AI系统操作规范.md",
        "MT_RULE_SYS_OPS": "系统操作规范.md",
        "MT_RULE_PARAM": "系统参数数据规范与操作规范.md",
        "MT_RULE_SRC_MOD": "源码修改准则参考与思路方案.md",
        "MT_RULE_QBANK": "题库管理规范与准则.md",
    }

_LOCK = threading.Lock()
ENFORCE_INTERVAL = 300  # 执行间隔: 5分钟
LEARN_INTERVAL = 3600   # 学习间隔: 1小时(规则文件不常变)


# ============================================================
# 1. 建表 (幂等)
# ============================================================
def ensure_rule_learning_tables() -> Dict[str, bool]:
    """创建规则学习相关表"""
    results = {}
    # 先确保rules_engine基础表存在
    try:
        init_tables()
    except Exception:
        pass

    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()

        # 规则学习记录表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_rule_learning_log (
            learn_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id          TEXT NOT NULL,
            rule_name        TEXT,
            rule_level       TEXT,
            rule_version     TEXT,
            violation_code   TEXT,
            intercept_layers TEXT,
            bypass_allowed   INTEGER DEFAULT 0,
            hard_constraints TEXT,
            learned_at       TEXT NOT NULL,
            brain_fed        INTEGER DEFAULT 0,
            UNIQUE(rule_id, rule_version)
        )""")
        results["mt_ai_rule_learning_log"] = True

        # 规则执行巡检记录表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_rule_enforcement_log (
            enforce_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_status      TEXT NOT NULL,
            rules_scanned    INTEGER DEFAULT 0,
            rules_passed     INTEGER DEFAULT 0,
            rules_failed     INTEGER DEFAULT 0,
            weak_words_total INTEGER DEFAULT 0,
            violations_found INTEGER DEFAULT 0,
            alerts_fed       INTEGER DEFAULT 0,
            bypass_attempts  INTEGER DEFAULT 0,
            details_json     TEXT,
            enforced_at      TEXT NOT NULL,
            CHECK(scan_status IN ('PASS','FAIL'))
        )""")
        results["mt_ai_rule_enforcement_log"] = True

        # AI脑库投喂日志表 (若不存在)
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (
            feed_uid    TEXT PRIMARY KEY,
            source      TEXT NOT NULL,
            content     TEXT,
            tags_json   TEXT,
            value_score REAL DEFAULT 0.5,
            status      TEXT DEFAULT 'PENDING',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )""")
        results["mt_ai_brain_feed_log"] = True

        conn.commit()
        conn.close()
    return results


# ============================================================
# 2. 自动学习: 解析9篇规则 → 投喂AI脑库
# ============================================================
def _extract_hard_constraints(file_path: str) -> List[str]:
    """从规则文件中提取硬约束条款"""
    constraints = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取包含"必须"/"禁止"/"不可"/"强制"的行
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            keywords = ["必须", "禁止", "不可", "强制", "不得", "严禁", "铁律", "bypass_allowed=False"]
            if any(kw in stripped for kw in keywords):
                constraints.append(stripped[:200])
    except Exception:
        pass
    return constraints


def _feed_rule_to_brain(conn: sqlite3.Connection, meta: RuleMeta,
                         constraints: List[str]) -> bool:
    """将规则知识投喂到AI脑库 (mt_ai_brain_feed_log)
    现有表schema: feed_id(auto), flow_id, feed_kind, feed_content, triggered_at"""
    now = datetime.now().isoformat()

    # 构建知识内容
    knowledge = json.dumps({
        "rule_id": meta.rule_id,
        "rule_name": meta.rule_name,
        "rule_level": meta.rule_level,
        "rule_version": meta.rule_version,
        "violation_code": meta.violation_code,
        "intercept_layers": meta.intercept_layers,
        "bypass_allowed": meta.bypass_allowed,
        "hard_constraints": constraints[:20],
        "constraint_count": len(constraints),
    }, ensure_ascii=False)

    try:
        conn.execute(
            """INSERT INTO mt_ai_brain_feed_log
            (flow_id, feed_kind, feed_content, triggered_at)
            VALUES (?,?,?,?)""",
            ("rule_learning_%s" % meta.rule_id,
             "RULE_LEARNING",
             knowledge[:2000],
             now),
        )
        return True
    except sqlite3.Error:
        return False


def learn_all_rules() -> Dict:
    """学习所有9篇规则: 解析RULE_META → 提取硬约束 → 投喂脑库 → 记录"""
    results = {"learned": 0, "skipped": 0, "brain_fed": 0, "details": []}

    # 解析规则目录
    rules_dir = os.path.abspath(RULES_DIR)
    if not os.path.isdir(rules_dir):
        _log(f"[LEARN] rules目录不存在: {rules_dir}")
        return results

    metas = parse_all_rules(rules_dir)
    if not metas:
        _log("[LEARN] 未解析到任何规则")
        return results

    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        for meta in metas:
            # 检查是否已学习过(同rule_id+version)
            existing = c.execute(
                "SELECT learn_id FROM mt_ai_rule_learning_log WHERE rule_id=? AND rule_version=?",
                (meta.rule_id, meta.rule_version)).fetchone()
            if existing:
                results["skipped"] += 1
                continue

            # 提取硬约束
            rule_file = RULE_REGISTRY.get(meta.rule_id, "")
            if rule_file:
                file_path = os.path.join(rules_dir, rule_file)
                constraints = _extract_hard_constraints(file_path)
            else:
                constraints = []

            # 投喂脑库
            brain_fed = _feed_rule_to_brain(conn, meta, constraints)

            # 记录学习
            now = datetime.now().isoformat()
            c.execute("""INSERT OR IGNORE INTO mt_ai_rule_learning_log
                (rule_id, rule_name, rule_level, rule_version,
                 violation_code, intercept_layers, bypass_allowed,
                 hard_constraints, learned_at, brain_fed)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (meta.rule_id, meta.rule_name, meta.rule_level, meta.rule_version,
                 meta.violation_code, ",".join(meta.intercept_layers),
                 1 if meta.bypass_allowed else 0,
                 json.dumps(constraints[:20], ensure_ascii=False),
                 now, 1 if brain_fed else 0))

            results["learned"] += 1
            if brain_fed:
                results["brain_fed"] += 1

            results["details"].append({
                "rule_id": meta.rule_id,
                "rule_name": meta.rule_name,
                "rule_level": meta.rule_level,
                "rule_version": meta.rule_version,
                "violation_code": meta.violation_code,
                "bypass_allowed": meta.bypass_allowed,
                "constraints_count": len(constraints),
                "brain_fed": brain_fed,
            })

        conn.commit()
        conn.close()

    _log(f"[LEARN] learned={results['learned']} skipped={results['skipped']} "
         f"brain_fed={results['brain_fed']}")
    return results


# ============================================================
# 3. 严格执行: 完整性扫描 + 违规检测 + 告警投喂
# ============================================================
def enforce_rules() -> Dict:
    """执行规则严格检查:
    1. 运行完整性扫描 (run_integrity_scan)
    2. 检查bypass_attempts
    3. 对违规项触发告警投喂 (alert_violation)
    """
    results = {
        "scan_status": "PASS", "rules_scanned": 0, "rules_passed": 0,
        "rules_failed": 0, "weak_words_total": 0, "violations_found": 0,
        "alerts_fed": 0, "bypass_attempts": 0, "details": [],
    }

    rules_dir = os.path.abspath(RULES_DIR)

    # 1. 运行完整性扫描
    try:
        # run_integrity_scan 返回 0=PASS, 1=FAIL
        scan_result = run_integrity_scan(rules_dir=rules_dir, output_json=False, strict=True)
        results["scan_status"] = "PASS" if scan_result == 0 else "FAIL"
    except Exception as e:
        _log(f"[ENFORCE] integrity_scan error: {e}")
        results["scan_status"] = "FAIL"
        scan_result = 1

    # 2. 检查bypass_attempts (查询mt_rule_violation_alert中未处理的绕过尝试)
    try:
        with _LOCK:
            conn = sqlite3.connect(APP_DB, timeout=30)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # 统计规则学习记录
            learned = c.execute(
                "SELECT COUNT(*) FROM mt_ai_rule_learning_log").fetchone()[0]
            bypass_rules = c.execute(
                "SELECT COUNT(*) FROM mt_ai_rule_learning_log WHERE bypass_allowed=1").fetchone()[0]

            # 查询未投喂的违规告警
            try:
                unfed = c.execute(
                    "SELECT COUNT(*) FROM mt_rule_violation_alert WHERE fed=0").fetchone()[0]
            except sqlite3.OperationalError:
                unfed = 0

            # 查询最近的违规记录
            try:
                recent_violations = c.execute("""
                    SELECT rule_id, violation_code, violation_detail, triggered_by, created_at
                    FROM mt_rule_violation_alert
                    ORDER BY created_at DESC LIMIT 10
                """).fetchall()
            except sqlite3.OperationalError:
                recent_violations = []

            conn.close()

        results["rules_scanned"] = learned
        results["bypass_attempts"] = bypass_rules
        results["violations_found"] = unfed

        # 3. 对未投喂的违规触发告警投喂
        if unfed > 0:
            try:
                rule_db = RuleDB()
                with _LOCK:
                    conn = sqlite3.connect(APP_DB, timeout=30)
                    conn.row_factory = sqlite3.Row
                    unfed_alerts = conn.execute(
                        "SELECT alert_id, rule_id, violation_code, violation_detail, triggered_by "
                        "FROM mt_rule_violation_alert WHERE fed=0 LIMIT 5").fetchall()
                    conn.close()

                for alert in unfed_alerts:
                    try:
                        # alert_violation会重新投喂EigenFlux+脑库+SA
                        alert_id = alert_violation(
                            rule_db,
                            rule_id=alert["rule_id"],
                            violation_code=alert["violation_code"],
                            violation_detail=alert["violation_detail"],
                            triggered_by=alert["triggered_by"] or "rule_enforcement_daemon",
                        )
                        if alert_id:
                            results["alerts_fed"] += 1
                            _log(f"[ENFORCE] alert re-fed: alert_id={alert_id} rule={alert['rule_id']}")
                    except Exception as e:
                        _log(f"[ENFORCE] alert feed failed: {e}")
            except Exception as e:
                _log(f"[ENFORCE] RuleDB init failed: {e}")

        # 4. 检查bypass_allowed=False的规则是否有绕过尝试
        if bypass_rules > 0:
            _log(f"[ENFORCE] WARNING: {bypass_rules} rules have bypass_allowed flag")
            results["bypass_attempts"] = bypass_rules

    except Exception as e:
        _log(f"[ENFORCE] DB check error: {e}")

    # 5. 落库执行记录
    now = datetime.now().isoformat()
    try:
        with _LOCK:
            conn = sqlite3.connect(APP_DB, timeout=30)
            c = conn.cursor()
            c.execute("""INSERT INTO mt_ai_rule_enforcement_log
                (scan_status, rules_scanned, rules_passed, rules_failed,
                 weak_words_total, violations_found, alerts_fed,
                 bypass_attempts, details_json, enforced_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (results["scan_status"], results["rules_scanned"],
                 results["rules_passed"], results["rules_failed"],
                 results["weak_words_total"], results["violations_found"],
                 results["alerts_fed"], results["bypass_attempts"],
                 json.dumps(results["details"], ensure_ascii=False)[:2000], now))
            conn.commit()
            conn.close()
    except Exception as e:
        _log(f"[ENFORCE] log insert error: {e}")

    _log(f"[ENFORCE] status={results['scan_status']} "
         f"scanned={results['rules_scanned']} "
         f"violations={results['violations_found']} "
         f"alerts_fed={results['alerts_fed']} "
         f"bypass={results['bypass_attempts']}")

    # ── MT_RULE_VERSION §3.2: 仙女座 ↔ 规则引擎 自动版本 bump 桥接 ──
    # 每 300s 由 sys_rule_enforcer 调用, 扫描 6 个事件表判定是否触发版本 bump
    try:
        from ai_engines.rules_engine.rule_version import apply_auto_bumps
        _bumps = apply_auto_bumps()
        if _bumps:
            _log(f"[ENFORCE] 自动版本 bump 触发: {', '.join(_bumps)}")
            results["auto_bumps"] = _bumps
    except Exception as _bex:  # noqa: BLE001
        _log(f"[ENFORCE] auto_bump 跳过 (非阻断): {_bex}")

    # ── MT_RULE_VERSION §3.2 + §4: 规则分块 ingest 自动补全 ──
    # 每 300s 检查 rule_knowledge 覆盖度, 缺了自动补
    try:
        from ai_engines.rules_engine.rule_andromeda_bridge import (
            rule_knowledge_health_check,
            ingest_rules_to_knowledge,
        )
        _hc = rule_knowledge_health_check()
        results["rule_knowledge_covered"] = _hc["covered"]
        results["rule_knowledge_missing"] = _hc["missing"]
        if _hc["missing"]:
            _ing = ingest_rules_to_knowledge(force=False)
            _log(f"[ENFORCE] rule_knowledge 补全: ingested={_ing['ingested']} "
                 f"skipped={_ing['skipped']} missing={_hc['missing']}")
    except Exception as _hx:  # noqa: BLE001
        _log(f"[ENFORCE] rule_knowledge 检查跳过 (非阻断): {_hx}")

    return results


# ============================================================
# 4. CLI守护模式
# ============================================================
class RuleLearningDaemon:
    """守护进程: 定期学习规则 + 执行检查"""

    @staticmethod
    def read_pid() -> Optional[int]:
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            return None

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def start():
        """启动守护进程"""
        existing = RuleLearningDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING  pid={existing}")
            return

        ensure_rule_learning_tables()

        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def _term(signum, frame):
            _log("[DAEMON] SIGTERM received, shutting down...")
            RuleLearningDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)

        _log(f"[DAEMON] START pid={os.getpid()} enforce_interval={ENFORCE_INTERVAL}s")

        # 首次启动: 立即学习+执行
        _log("[DAEMON] 首次学习规则...")
        learn_all_rules()
        _log("[DAEMON] 首次执行检查...")
        enforce_rules()

        # 主循环
        cycle = 0
        last_learn_time = time.time()

        while True:
            cycle += 1
            try:
                now = time.time()

                # 每1小时重新学习规则
                if now - last_learn_time >= LEARN_INTERVAL:
                    _log(f"[DAEMON] cycle={cycle} re-learning rules...")
                    learn_all_rules()
                    last_learn_time = now

                # 每5分钟执行检查
                _log(f"[DAEMON] cycle={cycle} enforcing rules...")
                enforce_rules()

            except Exception as e:
                _log(f"[DAEMON] cycle={cycle} ERROR: {e}")

            time.sleep(ENFORCE_INTERVAL)

    @staticmethod
    def stop():
        pid = RuleLearningDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED (no PID)")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        except OSError:
            pass
        RuleLearningDaemon.clear_pid()
        print("[STATUS] STOPPED")

    @staticmethod
    def status() -> Dict:
        ensure_rule_learning_tables()
        pid = RuleLearningDaemon.read_pid()
        state = "RUNNING" if pid else "STOPPED"

        with _LOCK:
            conn = sqlite3.connect(APP_DB, timeout=30)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # 学习统计
            learned = c.execute(
                "SELECT COUNT(*) FROM mt_ai_rule_learning_log").fetchone()[0]
            brain_fed = c.execute(
                "SELECT COUNT(*) FROM mt_ai_rule_learning_log WHERE brain_fed=1").fetchone()[0]

            # 执行统计
            enforce_count = c.execute(
                "SELECT COUNT(*) FROM mt_ai_rule_enforcement_log").fetchone()[0]
            last_enforce = c.execute("""
                SELECT * FROM mt_ai_rule_enforcement_log
                ORDER BY enforced_at DESC LIMIT 1
            """).fetchone()

            # 违规统计
            try:
                total_violations = c.execute(
                    "SELECT COUNT(*) FROM mt_rule_violation_alert").fetchone()[0]
            except sqlite3.OperationalError:
                total_violations = 0
            try:
                unfed_violations = c.execute(
                    "SELECT COUNT(*) FROM mt_rule_violation_alert WHERE fed=0").fetchone()[0]
            except sqlite3.OperationalError:
                unfed_violations = 0

            # 9篇规则学习详情
            rules = c.execute("""
                SELECT rule_id, rule_name, rule_level, rule_version,
                       violation_code, bypass_allowed, brain_fed, learned_at
                FROM mt_ai_rule_learning_log
                ORDER BY learned_at DESC
            """).fetchall()

            conn.close()

        return {
            "daemon_pid": pid,
            "daemon_state": state,
            "rules_learned": learned,
            "brain_fed": brain_fed,
            "enforce_count": enforce_count,
            "last_enforce": dict(last_enforce) if last_enforce else None,
            "total_violations": total_violations,
            "unfed_violations": unfed_violations,
            "rules": [dict(r) for r in rules],
        }


# ============================================================
# 日志
# ============================================================
def _log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


# ============================================================
# CLI入口
# ============================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "start":
        RuleLearningDaemon.start()

    elif cmd == "stop":
        RuleLearningDaemon.stop()

    elif cmd == "status":
        s = RuleLearningDaemon.status()
        print(f"{'='*60}")
        print(f"  Rule Learning & Enforcement Engine")
        print(f"{'='*60}")
        print(f"  Daemon PID:        {s['daemon_pid'] or '-'}")
        print(f"  Daemon State:      {s['daemon_state']}")
        print(f"  Rules Learned:     {s['rules_learned']}/9")
        print(f"  Brain Fed:         {s['brain_fed']}")
        print(f"  Enforce Count:      {s['enforce_count']}")
        print(f"  Total Violations:   {s['total_violations']}")
        print(f"  Unfed Violations:   {s['unfed_violations']}")
        if s["last_enforce"]:
            le = s["last_enforce"]
            print(f"  Last Scan Status:   {le['scan_status']}")
            print(f"  Last Enforce Time:  {le['enforced_at']}")
        print(f"{'='*60}")
        if s["rules"]:
            print(f"  {'Rule ID':<25} {'Level':<10} {'Ver':<10} {'Bypass':<8} {'Fed':<5}")
            print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*8} {'-'*5}")
            for r in s["rules"]:
                print(f"  {r['rule_id'][:25]:<25} {r['rule_level'] or '-':<10} "
                      f"{r['rule_version'] or '-':<10} "
                      f"{'NO' if r['bypass_allowed'] else 'YES':<8} "
                      f"{'Y' if r['brain_fed'] else 'N':<5}")

    elif cmd == "learn":
        ensure_rule_learning_tables()
        r = learn_all_rules()
        print(f"{'='*60}")
        print(f"  Rule Learning Result")
        print(f"{'='*60}")
        print(f"  Learned:   {r['learned']}")
        print(f"  Skipped:   {r['skipped']}")
        print(f"  Brain Fed: {r['brain_fed']}")
        for d in r["details"]:
            bypass = "NO" if d["bypass_allowed"] else "YES"
            print(f"  [{d['rule_level'] or '?':<10}] {d['rule_id']:<25} "
                  f"v{d['rule_version']} bypass={bypass} "
                  f"constraints={d['constraints_count']} fed={'Y' if d['brain_fed'] else 'N'}")

    elif cmd == "enforce":
        ensure_rule_learning_tables()
        r = enforce_rules()
        print(f"{'='*60}")
        print(f"  Rule Enforcement Result")
        print(f"{'='*60}")
        print(f"  Scan Status:      {r['scan_status']}")
        print(f"  Rules Scanned:    {r['rules_scanned']}")
        print(f"  Violations Found: {r['violations_found']}")
        print(f"  Alerts Fed:       {r['alerts_fed']}")
        print(f"  Bypass Attempts:  {r['bypass_attempts']}")

    elif cmd == "once":
        ensure_rule_learning_tables()
        print("=== 1. Learning rules ===")
        learn_all_rules()
        print("=== 2. Enforcing rules ===")
        enforce_rules()
        print("=== Done ===")

    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
