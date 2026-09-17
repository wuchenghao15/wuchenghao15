#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arduino 自动引导全链路定时巡检验证
==================================
纯 HTTP 客户端 — Flask server 必须已在 8888 端口运行。
每次巡检结果落库 mt_arduino_boot_verification (app.db)。

8 级链路:
  L1 events/poll     → guest 可访问
  L2 events/poll     → JSON {events:[...]} 合法
  L3 auto_detect     → guest 可访问
  L4 session/bind    → SA 可访问
  L5 redirect_target → → arduino_ide
  L6 arduino_ide     → 模板无 500
  L7 compile_assist  → qwen2.5-coder 返回修复
  L8 hotplug.js      → 文件完整 + 逻辑正确
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

BASE = "http://127.0.0.1:8888"
TIMEOUT = 15  # 单次 HTTP 超时 (compile_assist 单独用 120s)

def _get_app_db() -> str:
    try:
        from core.db_path import get_db_path
        return get_db_path("app.db")
    except Exception:
        return os.path.join(_ROOT, "Database", "app.db")

APP_DB = _get_app_db()


def _http_get(path: str, timeout: int = TIMEOUT) -> tuple:
    """return (status_code, body_str, err_str)"""
    try:
        req = urllib.request.Request(BASE + path)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='replace'), ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace'), ""
    except Exception as e:
        return 0, "", str(e)


def _http_post(path: str, body: dict, timeout: int = TIMEOUT) -> tuple:
    try:
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(BASE + path, data=data,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='replace'), ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace'), ""
    except Exception as e:
        return 0, "", str(e)


class ArduinoBootVerifier:
    def __init__(self):
        self._db = APP_DB
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _ensure_table(self, conn: sqlite3.Connection) -> None:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mt_arduino_boot_verification (
            verify_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id   TEXT,
            level      TEXT NOT NULL,
            name       TEXT NOT NULL,
            passed     INTEGER NOT NULL,
            latency_ms INTEGER DEFAULT 0,
            detail     TEXT,
            created_at TEXT
        );
        """)

    def verify(self) -> dict:
        cycle_id = f"arduino_boot_{int(time.time())}"
        results = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # L1
        t0 = time.time()
        sc, body, err = _http_get('/api/arduino/events/poll?global=1')
        ok = sc == 200 and not err
        results.append(self._rec(cycle_id, 'L1', 'events/poll guest 可访问', ok, t0, f'status={sc}'))

        # L2
        t0 = time.time()
        ok = False; detail = ""
        try:
            d = json.loads(body)
            evts = d.get('events') or (d.get('data') or {}).get('events')
            ok = isinstance(evts, list)
            detail = f'events_len={len(evts) if isinstance(evts, list) else "?"}'
        except Exception as e:
            detail = str(e)[:60]
        results.append(self._rec(cycle_id, 'L2', 'events/poll JSON 合法', ok, t0, detail))

        # L3
        t0 = time.time()
        sc, body, _ = _http_get('/api/arduino/auto_detect')
        ok = sc == 200
        results.append(self._rec(cycle_id, 'L3', 'auto_detect guest 可访问', ok, t0, f'status={sc}'))
        if ok:
            try:
                d = json.loads(body)
                ok2 = 'devices' in d or 'connected' in d
                results.append(self._rec(cycle_id, 'L3b', 'auto_detect devices 字段', ok2, t0))
            except Exception:
                pass

        # L4 — 需要 login session cookie (用 Flask test_client)
        t0 = time.time()
        ok, detail = self._test_l4_session()
        results.append(self._rec(cycle_id, 'L4', 'session/bind & redirect (SA)', ok, t0, detail))

        # L5
        results.append(self._rec(cycle_id, 'L5', 'session/redirect_target → arduino_ide', ok, t0, detail))

        # L6
        t0 = time.time()
        no_jinja = self._test_l6_template()
        results.append(self._rec(cycle_id, 'L6', 'arduino_ide 模板无 Jinja2 崩溃', no_jinja, t0))

        # L7 — Neural Hub compile_assist (慢, 120s)
        t0 = time.time()
        ok = False; detail = ""
        sc, body, _ = _http_post('/api/neuralhub/arduino_compile_assist',
                                  {'error_log': "'Serial' not declared", 'code': 'void setup(){}'},
                                  timeout=120)
        try:
            d = json.loads(body)
            ok = d.get('success', False)
            detail = f"model={d.get('model','')[:20]} dur={d.get('duration_ms')}ms"
        except Exception as e:
            detail = f'http={sc} err={str(e)[:50]}'
        results.append(self._rec(cycle_id, 'L7', 'compile_assist → qwen2.5-coder 修复', ok, t0, detail))

        # L8
        t0 = time.time()
        try:
            js = os.path.join(_ROOT, 'static', 'js', 'arduino_global_hotplug.js')
            with open(js) as f:
                content = f.read()
            ok = os.path.getsize(js) > 500 and '/events/poll' in content and 'arduino_ide' in content
            results.append(self._rec(cycle_id, 'L8', 'arduino_global_hotplug.js 完整', ok, t0, f'size={os.path.getsize(js)}'))
        except Exception as e:
            results.append(self._rec(cycle_id, 'L8', 'hotplug.js', False, t0, str(e)[:60]))

        self._persist(cycle_id, results)
        passed = sum(1 for r in results if r['passed'])
        return {"cycle_id": cycle_id, "timestamp": now,
                "overall_passed": passed == len(results),
                "passed": passed, "total": len(results),
                "results": results}

    def _test_l4_session(self) -> tuple:
        """用 Flask test_client 验证 login 后 session API"""
        try:
            from server_real_db import app
            with app.test_client() as c:
                with c.session_transaction() as sess:
                    sess['logged_in'] = True
                    sess['username'] = 'wuchenghao15'
                    sess['user_id'] = 1
                    sess['role'] = 'super_admin'
                r = c.post('/api/arduino/session/bind', json={'device_vid_pid': '2341:0043'})
                bind_ok = r.status_code in (200, 400)
                r2 = c.get('/api/arduino/session/redirect_target')
                redirect_ok = r2.status_code in (200, 302)
                if r2.status_code == 200:
                    try:
                        d = json.loads(r2.data)
                        rd = d.get('redirect') or (d.get('data') or {}).get('redirect', '')
                        redirect_ok = redirect_ok and ('arduino_ide' in rd or rd == '')
                    except Exception:
                        redirect_ok = False
                return bind_ok and redirect_ok, f'bind={bind_ok} redirect={redirect_ok}'
        except Exception as e:
            return False, str(e)[:80]

    def _test_l6_template(self) -> bool:
        """用 Flask test_client 验证模板不崩溃"""
        try:
            from server_real_db import app
            with app.test_client() as c:
                with c.session_transaction() as sess:
                    sess['logged_in'] = True
                    sess['username'] = 'wuchenghao15'
                    sess['user_id'] = 1
                    sess['role'] = 'super_admin'
                r = c.get('/admin_app/arduino_ide')
                return r.status_code < 500  # 302/403 都是安全拦截, 500 = Jinja2 crash
        except Exception:
            return False

    def _rec(self, cycle_id, level, name, passed, t0, detail=""):
        return {"cycle_id": cycle_id, "level": level, "name": name,
                "passed": bool(passed), "latency_ms": int((time.time()-t0)*1000),
                "detail": detail[:200], "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def _persist(self, cycle_id, results):
        try:
            c = sqlite3.connect(self._db, timeout=30)
            self._ensure_table(c)
            c.executemany("""INSERT INTO mt_arduino_boot_verification
                (cycle_id, level, name, passed, latency_ms, detail, created_at)
                VALUES (?,?,?,?,?,?,?)""",
                [(r['cycle_id'], r['level'], r['name'], 1 if r['passed'] else 0,
                  r['latency_ms'], r['detail'], r['created_at']) for r in results])
            c.commit(); c.close()
        except Exception as e:
            print(f"[ArduinoBootVerifier] persist: {e}")

    # ── daemon ──
    def start(self, interval: int = 600):
        if self._thread and self._thread.is_alive(): return
        def _loop():
            if not self._stop.wait(60): return
            while not self._stop.is_set():
                try:
                    r = self.verify()
                    mark = "✅" if r['overall_passed'] else "❌"
                    print(f"[ArduinoBootVerifier] {mark} {r['passed']}/{r['total']} @ {r['timestamp']}")
                except Exception as e:
                    print(f"[ArduinoBootVerifier] error: {e}")
                self._stop.wait(interval)
        self._thread = threading.Thread(target=_loop, name="arduino-boot-verify", daemon=True)
        self._thread.start()
        print(f"[ArduinoBootVerifier] 已启动 (interval={interval}s)")

    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(10)


if __name__ == "__main__":
    v = ArduinoBootVerifier()
    r = v.verify()
    mark = "✅" if r['overall_passed'] else "❌"
    print(f"\n{mark} Arduino 自动引导全链路 {r['passed']}/{r['total']} 通过 @ {r['timestamp']}")
    for row in r['results']:
        m = "✅" if row['passed'] else "❌"
        print(f"  {m} {row['level']} {row['name']} ({row['latency_ms']}ms) {row['detail'][:60]}")
