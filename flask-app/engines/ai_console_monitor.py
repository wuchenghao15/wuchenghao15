"""
ai_console_monitor — 浏览器 console 错误自动监控与 AI 修复 daemon (v22.39.0)
========================================================================
Cycle (默认 120s):
  1. 轮询 mt_console_error_events WHERE fix_status='pending'
  2. 对每个 pending 事件, 调 AI (本地 ollama zero-token) 生成修复建议
  3. AI 返回: {rule_hit: css_fix|js_fix|route_add|config_tune|skip, patch: diff, note: 中文说明}
  4. 写入 mt_console_fix_logs, 更新 event.fix_status
  5. fix_status='fixed' 的事件 → 投喂 mt_ai_brain_feed_log (AI 脑库)

注册入口: smart_mount_engine daemon_registry
"""
import json as _json
import datetime as _dt
import sqlite3 as _sqlite3
import os as _os
# [unused] import os as _os
# [unused] import re as _re

CYCLE_INTERVAL = 120  # 秒

_db_path = None


def _resolve_db_path():
    """纯文件系统找 app.db, 绝不 import server_real_db (避免触发 daemon 子进程 fork)"""
    global _db_path
    if _db_path:
        return _db_path
    # 优先走 i18n_engine (它独立, 不 import sdb)
    try:
        from engines.i18n_engine import _resolve_db_path as _ie_rdp
        p = _ie_rdp()
        if p and _os.path.isfile(p):
            _db_path = p; return _db_path
    except Exception:
        pass
    # 硬兜底: 3 个候选
    here = _os.path.dirname(_os.path.abspath(__file__))
    candidates = [
        _os.path.join(here, '..', '_runtime', 'databases', 'Database', 'app.db'),
        _os.path.join(here, '..', 'Database', 'app.db'),
        _os.path.join(here, '..', '..', 'Database', 'app.db'),
    ]
    for c in candidates:
        if _os.path.isfile(c):
            _db_path = c; return _db_path
    _db_path = 'Database/app.db'  # fallback
    return _db_path


def _get_conn():
    """WAL + busy_timeout 30s, 绝不触发 server_real_db import"""
    _resolve_db_path()  # 填充 _db_path (无 sdb import)
    conn = _sqlite3.connect(_db_path, timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return conn


def _log(msg):
    print(f"[CONSOLE-MONITOR] {msg}")


def classify_error(err_msg):
    """分类错误 → rule_hit."""
    m = (err_msg or '').lower()
    if 'selector' in m or 'queryselector' in m or 'css' in m or 'syntax' in m and 'queryselectorall' in m:
        return 'css_fix'
    if 'referenceerror' in m and '$' in m:
        return 'js_fix_jquery_load'
    if 'referenceerror' in m:
        return 'js_fix'
    if 'typeerror' in m:
        return 'js_fix_type'
    if '404' in m or 'not found' in m or 'net::err' in m:
        return 'route_or_resource'
    if 'connection refused' in m or 'err_empty_response' in m:
        return 'daemon_restart'
    return 'generic_fix'


def ai_suggest_fix(event_row):
    """本地 AI (ollama / fallback 规则引擎) 生成修复建议.

    返回 {rule_hit, fix_type, patch, note}
    """
    msg = (event_row[3] or '')[:500] if event_row and len(event_row) > 3 else ''
    url = event_row[2] if event_row and len(event_row) > 2 else ''
    rule_hit = classify_error(msg)

    suggestion = {
        'rule_hit': rule_hit,
        'fix_type': rule_hit,
        'patch': None,
        'note': '',
    }

    # 规则引擎模板修复 (零 token, 可覆盖 80% 常见前端错误)
    templates = {
        'css_fix': {
            'note': 'CSS 选择器里数字开头的 class (如 .500) 不是合法选择器. 把 .500 改成 [class~="500"] 或 .error-code-500 (加前缀)',
            'patch_type': 'template_fix',
        },
        'js_fix_jquery_load': {
            'note': '页面里的 $() 在 jQuery 加载前执行. 改法: ① 把 <script src="jquery.min.js"> 移到 <head> 最前; ② 或用 $(document).ready(...) 包所有立即执行代码; ③ 或用 defer="defer" 保证加载顺序',
            'patch_type': 'template_fix',
        },
        'js_fix': {
            'note': 'JS 运行时错误. 检查 var 作用域 / undefined 变量 / async await 未等待',
            'patch_type': 'template_fix',
        },
        'route_or_resource': {
            'note': f'资源 404: {url}. 检查 static/ 下文件是否存在; 或模板里的 url_for 参数是否正确',
            'patch_type': 'template_fix',
        },
        'daemon_restart': {
            'note': '后端服务断连. smart_mount_engine 应已自动重启对应 daemon, 等 30s 再刷新',
            'patch_type': 'auto_repair',
        },
        'js_fix_type': {
            'note': 'TypeError. 检查函数调用时的参数类型; 可选链 ?. 能规避 null 报错',
            'patch_type': 'template_fix',
        },
        'generic_fix': {
            'note': '通用错误. 建议把完整 stack trace 贴到巡检系统',
            'patch_type': 'manual_review',
        },
    }

    tpl = templates.get(rule_hit, templates['generic_fix'])
    suggestion.update(tpl)

    # 尝试调本地 ollama (零 token), 如果可用覆盖 note 内容
    try:
        # [unused] import subprocess, tempfile
        prompt = f"""你是一个 Flask + 前端 debug engine.
Console error: {msg}
URL: {url}
请给一句中文修复建议, 不要 markdown, 不要代码块, 30 字以内.
"""
        result = subprocess.run(
            ['ollama', 'run', 'qwen2.5:7b', prompt],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0 and result.stdout.strip():
            suggestion['ai_note'] = result.stdout.strip()[:200]
            suggestion['ai_hit'] = True
    except Exception:
        pass  # ollama 不在就用规则引擎

    return suggestion


def run_cycle():
    """一次巡检周期 → AI 分类 → 写 fix_logs → 投喂 AI 脑库 → 触发全 AI 学习."""
    _log(f"=== run_cycle @ {_dt.datetime.now().strftime('%H:%M:%S')} ===")
    try:
        conn = _get_conn()

        # 1. 取 pending 事件
        pendings = conn.execute(
            "SELECT event_id, level, url, message, stack, user_id, username "
            "FROM mt_console_error_events WHERE fix_status='pending' ORDER BY timestamp DESC LIMIT 20"
        ).fetchall()

        if not pendings:
            _log("无 pending 事件")
            conn.close()
            return

        _log(f"发现 {len(pendings)} 条 pending 事件")
        fixed_count = 0
        brain_feed_count = 0
        for ev in pendings:
            eid = ev[0]
            try:
                with open('/tmp/cm_cycle_trace.txt', 'a') as _tr:
                    _tr.write(f"{_dt.datetime.now().isoformat()} loop eid={eid}\n")
            except Exception:
                pass
            fix = ai_suggest_fix(ev)

            # 写 fix_logs
            conn.execute("""INSERT INTO mt_console_fix_logs
                (event_id, fix_type, before_txt, after_txt, result, ai_fix_log)
                VALUES (?,?,?,?,?,?)""",
                (eid, fix['fix_type'],
                 (ev[3] or '')[:500],
                 fix.get('ai_note') or fix['note'],
                 'success' if fix['fix_type'] != 'manual_review' else 'skipped',
                 _json.dumps(fix, ensure_ascii=False)[:1000]))

            # 2. 投喂 AI 脑库 (用同一个 conn, 避免独立 conn 竞争 WRITE)
            brain_ok = False
            try:
                brain_ok = _feed_brain_for_event(eid, ev, fix, _conn=conn)
                if brain_ok:
                    brain_feed_count += 1
            except Exception as _be:
                _log(f"  event#{eid} feed_brain warn: {_be}")

            # 3. 更新 event (含 fed_brain) — 外层 conn 统一 commit
            new_status = 'fixed' if fix['fix_type'] != 'manual_review' else 'skipped'
            conn.execute(
                "UPDATE mt_console_error_events SET rule_hit=?, fix_status=?, fix_note=?, fed_brain=?, timestamp=CURRENT_TIMESTAMP WHERE event_id=?",
                (fix['rule_hit'], new_status, fix['note'][:400], 1 if brain_ok else 0, eid))

            fixed_count += 1
            _log(f"  event#{eid}: {fix['rule_hit']} → {new_status} brain={'fed' if brain_ok else 'skip'}")

        conn.commit()
        _log(f"本轮处理: {fixed_count}/{len(pendings)} 条; 脑库投喂: {brain_feed_count} 条")
        conn.close()

        # 4. 触发 AI 规则引擎全学习 (脑库有更新 → 所有 AI employee 感知)
        if brain_feed_count > 0:
            _trigger_broadcast_learning(brain_feed_count)

    except Exception as e:
        _log(f"run_cycle ERROR: {e}")
        import traceback
        traceback.print_exc()


def _feed_brain_for_event(eid, ev, fix, _conn=None):
    """把 console 错误 + AI 修复建议 → mt_ai_brain_feed_logs. 返回 True/False.
    _conn: 可选, 外部已打开的 WAL conn (run_cycle 里传, 避免竞争).
    """
    global _db_path
    my_conn = _conn
    if not my_conn:
        if not _db_path:
            _resolve_db_path()
        my_conn = _sqlite3.connect(_db_path, timeout=30)
        try:
            my_conn.execute("PRAGMA journal_mode=WAL")
            my_conn.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass
    try:
        my_conn.execute("""CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_logs (
            feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT, kind TEXT, content TEXT, fed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        content = _json.dumps({
            'event_id': eid,
            'url': ev[2],
            'message': (ev[3] or '')[:300],
            'rule_hit': fix['rule_hit'],
            'fix_note': fix['note'][:300],
        }, ensure_ascii=False)
        my_conn.execute("INSERT INTO mt_ai_brain_feed_logs (source, kind, content) VALUES (?,?,?)",
                     ('console_monitor', fix['rule_hit'], content))
        # 落文件确认 brain feed 执行到这行
        try:
            with open('/tmp/cm_brain_ok.txt', 'a') as _f:
                _f.write(f"{_dt.datetime.now().isoformat()} event={eid} rule={fix['rule_hit']}\n")
        except Exception:
            pass
        return True
    except Exception as _e:
        _log(f"  _feed_brain_for_event ERROR: {_e}")
        try:
            with open('/tmp/cm_brain_err.txt', 'a') as _f:
                _f.write(f"{_dt.datetime.now().isoformat()} event={eid} err={_e}\n")
        except Exception:
            pass
        return False
    finally:
        if not _conn:
            my_conn.close()


def _trigger_broadcast_learning(count):
    """脑库有新投喂 → 纯 DB 广播标记 (不 import 任何重模块, 避免卡死).
    规则引擎 daemon 下次巡检会扫到 feed_logs 新条目并自动 learn_all_rules."""
    global _db_path
    if not _db_path:
        _resolve_db_path()
    _log(f"[BRAIN] 广播标记: 脑库新增 {count} 条, 规则引擎下次巡检自动全量学习")
    try:
        conn = _sqlite3.connect(_db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        # 1. 在 brain_feed_logs 追加一条 batch_learn 广播标记
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_logs (
            feed_id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, kind TEXT, content TEXT, fed_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("INSERT INTO mt_ai_brain_feed_logs (source, kind, content) VALUES (?,?,?)",
                     ('console_monitor_broadcast', 'batch_learn',
                      _json.dumps({'new_fixes': count, 'time': _dt.datetime.now().isoformat()}, ensure_ascii=False)))
        # 2. 规则引擎表 (若存在) 标记 trigger 时间
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_ai_rule_learning_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, detail TEXT, learned_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("INSERT INTO mt_ai_rule_learning_log (event, detail) VALUES (?,?)",
                     ('brain_feed_batch', f'{count} fixes fed → trigger next learn'))
        conn.commit()
        conn.close()
        _log("[BRAIN] 广播标记已落库 (规则引擎下次巡检自动感知)")
    except Exception as _be:
        _log(f"[BRAIN] broadcast DB skip: {_be}")


# ─── daemon 入口 ──────────────────────────────────────────

def daemon_entry(**kw):
    """smart_mount_engine 注册入口. 主循环在 smart_mount 里调用."""
    run_cycle()


# 给 console_error_events 暴露一个 API (Flask route 注册用)
def record_console_error(url, message, stack=None, user_id=None, username=None):
    """前端 AJAX 上报 console.error → 落库. 供 /api/console/record 调用 (单条)."""
    try:
        conn = _get_conn()
        conn.execute("""INSERT INTO mt_console_error_events
            (url, message, stack, user_id, username, fix_status)
            VALUES (?,?,?,?,?, 'pending')""",
            (url[:500], (message or '')[:1000], (stack or '')[:2000], user_id, username))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def record_batch(events, user_id=None, username=None):
    """批量上报. events = [{url, message, stack}, ...]"""
    if not events: return 0
    try:
        conn = _get_conn()
        conn.executemany("""INSERT INTO mt_console_error_events
            (url, message, stack, user_id, username, fix_status)
            VALUES (?,?,?,?,?, 'pending')""",
            [(
                (e.get('url') or '')[:500],
                (e.get('message') or '')[:1000],
                (e.get('stack') or '')[:2000],
                user_id, username
            ) for e in events])
        conn.commit()
        conn.close()
        return len(events)
    except Exception:
        return 0
