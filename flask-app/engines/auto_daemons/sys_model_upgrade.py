#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成daemon: sys_model_upgrade
职责: 大模型自动升级引擎 — sync Ollama → eval 所有模型 → 升级/回滚
周期: 3600s (1小时)
"""
import os, sys, time, signal, sqlite3, json
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DB = os.path.join(_PROJECT_ROOT, "Database", "app.db")
if not os.path.exists(APP_DB):
    APP_DB = os.path.join(_PROJECT_ROOT, "flask-app", "app.db")
PID_FILE = os.path.join(_PROJECT_ROOT, "_runtime", "pids", "sys_model_upgrade.pid")
LOG_FILE = os.path.join(_PROJECT_ROOT, "_runtime", "logs", "sys_model_upgrade.log")

os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
with open(PID_FILE, "w") as f: f.write(str(os.getpid()))

_running = True
def _signal_handler(signum, frame):
    global _running; _running = False
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

def _db():
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def _log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def _heartbeat(status="RUNNING", extra=""):
    try:
        conn = _db()
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE mt_daemon_registry SET status=?, last_heartbeat=?, updated_at=?, total_runs=total_runs+1 WHERE daemon_name='sys_model_upgrade'",
            (status, now, now))
        conn.execute(
            "INSERT OR IGNORE INTO mt_daemon_registry (daemon_name, daemon_type, daemon_purpose, interval_seconds, status) VALUES ('sys_model_upgrade','model','大模型自动评测与升级',3600,'RUNNING')")
        conn.commit(); conn.close()
    except Exception as e:
        _log(f"heartbeat err: {e}")

def main_loop():
    _log("=== sys_model_upgrade START ===")
    ENGINE_DIR = os.path.join(_PROJECT_ROOT, "flask-app", "ai_engines")
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, "flask-app"))
    
    try:
        from ai_engines.model_upgrade_engine import model_upgrade_engine as eng
    except Exception as e:
        _log(f"engine import FAIL: {e}")
        return

    cycle = 0
    while _running:
        cycle += 1
        _log(f"--- cycle #{cycle} ---")
        _heartbeat("RUNNING", f"cycle={cycle}")

        try:
            # Step 1: sync Ollama → DB
            r = eng.sync_ollama()
            _log(f"sync: {r}")

            # Step 2: eval 所有模型（1 轮，daemon 背景跑不耗时）
            status = eng.get_status()
            for v in status.get('versions', []):
                tag = v['ollama_tag']
                _log(f"eval {tag} ...")
                try:
                    eng.eval_model(tag, rounds=1)
                except Exception as e:
                    _log(f"  eval FAIL: {e}")

            # Step 3: 自动激活最高分模型（如果差距 > 5 分）
            versions = eng.get_status()['versions']
            # 按 eval_score 降序
            versions.sort(key=lambda x: x.get('eval_score', 0), reverse=True)
            if len(versions) >= 2:
                top = versions[0]; second = versions[1]
                if top['eval_score'] > second['eval_score'] + 5 and not top.get('is_current'):
                    _log(f"upgrade: {top['ollama_tag']}(eval={top['eval_score']}) > {second['ollama_tag']}(eval={second['eval_score']})")
                    eng.activate(top['ollama_tag'])
                    _log(f"✅ activated → {top['ollama_tag']}")
                else:
                    _log(f"no_upgrade: diff={top['eval_score'] - second['eval_score']:.1f} < 5")

        except Exception as e:
            _log(f"cycle err: {e}")
            _heartbeat("ERROR", str(e)[:200])

        # 等 1 小时
        for _ in range(3600):
            if not _running: break
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_loop()
    finally:
        if os.path.exists(PID_FILE): os.remove(PID_FILE)
        _heartbeat("STOPPED")
        _log("=== sys_model_upgrade STOPPED ===")
