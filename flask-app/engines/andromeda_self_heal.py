#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仙女座自愈引擎 (Andromeda Self-Heal Engine)
===========================================
独立进程 — 不嵌入 Flask, 避免之前 ANDROMEDA-EVOL 在 Flask 内拉垮主进程的问题

职责:
  1. 每 30s 检查 Flask 健康 (PID 存活 + HTTP /index 200)
  2. 发现异常 → 匹配特征库 → 执行修复脚本 → 记录结果
  3. 健康心跳 → 写入 andromeda_health_heartbeat
  4. Flask 启动/退出追踪 → 写入 andromeda_flask_uptime
  5. 异常经验 → 写入/更新 andromeda_self_heal_log (frequency++, last_seen)

启动: python3 engines/andromeda_self_heal.py &
停止: kill -TERM <pid>

作者: Andromeda AI (仙女座)
版本: v1.0.0 (2026-09-20)
"""
import os, sys, time, json, signal, subprocess, sqlite3, re, urllib.request, urllib.error
from datetime import datetime

# ========== 常量 ==========
FLASK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(FLASK_DIR, 'database', 'app.db')
PID_FILE  = '/tmp/flask_pid_8888'
PORT      = 8888
HEALTHY   = 'http://localhost:%d/index' % PORT
INTERVAL  = 30          # 心跳间隔 (秒)
HTTP_TIMEOUT = 5
MAX_RESTARTS_PER_HOUR = 5   # 1 小时内最多重启次数 (避免无限 loop)

# ========== 优雅退出 ==========
_SHUTDOWN = False
def _graceful_exit(signum, frame):
    global _SHUTDOWN
    _SHUTDOWN = True
signal.signal(signal.SIGTERM, _graceful_exit)
signal.signal(signal.SIGINT, _graceful_exit)

# ========== DB 工具 (独立进程, 自己的连接) ==========
def _db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

def _log_anomaly(anomaly_type, severity, description, auto_fix_applied='', fix_method='', success=0, ai_analysis='', tags=None):
    """上报异常到特征库 — 匹配已有条目则 frequency++, 否则新建"""
    conn = _db()
    try:
        existing = conn.execute(
            "SELECT id, frequency FROM andromeda_self_heal_log WHERE anomaly_type=? AND resolved=0 ORDER BY frequency DESC LIMIT 1",
            (anomaly_type,)
        ).fetchone()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if existing:
            conn.execute("""
                UPDATE andromeda_self_heal_log 
                SET frequency=frequency+1, last_seen=?, description=COALESCE(?,description),
                    success=? WHERE id=?
            """, (now, description or None, success, existing['id']))
            row_id = existing['id']
        else:
            cur = conn.execute("""
                INSERT INTO andromeda_self_heal_log
                (timestamp, anomaly_type, severity, description, auto_fix_applied, fix_method,
                 success, ai_analysis, frequency, first_seen, last_seen, resolved, tags)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (now, anomaly_type, severity, description, auto_fix_applied, fix_method,
                  success, ai_analysis, 1, now, now, 0, json.dumps(tags or [], ensure_ascii=False)))
            row_id = cur.lastrowid
        conn.commit()
        print(f"[ANROMEDA] 📋 特征库 #{row_id} {anomaly_type} freq={conn.execute('SELECT frequency FROM andromeda_self_heal_log WHERE id=?',(row_id,)).fetchone()[0]} fix={'✅' if success else '❌'}")
    finally:
        conn.close()
    return row_id

def _log_heartbeat(flask_alive, flask_http_200, db_writable, anomalies=0):
    conn = _db()
    try:
        # DB 锁计数
        locked = 0
        try:
            locked = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='andromeda_self_heal_log'"
            ).fetchone()[0]
        except Exception:
            pass
        cpu = mem = 0.0
        try:
            # ps 获取 Flask CPU/MEM
            if flask_alive:
                pid = open(PID_FILE).read().strip() if os.path.exists(PID_FILE) else ''
                out = subprocess.getoutput(f"ps -p {pid} -o %cpu=,%mem=")
                parts = out.strip().split()
                cpu = float(parts[0]) if parts else 0
                mem = float(parts[1]) if len(parts) > 1 else 0
        except Exception:
            pass
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            INSERT INTO andromeda_health_heartbeat
            (timestamp, flask_alive, flask_http_200, db_writable, db_locked_count, cpu_percent, mem_percent, anomalies_found)
            VALUES (?,?,?,?,?,?,?,?)
        """, (now, flask_alive, flask_http_200, db_writable, 0, cpu, mem, anomalies))
        conn.commit()
    finally:
        conn.close()

def _log_uptime_event(pid, event, reason='', alive_seconds=0):
    """记录 Flask 启动/退出"""
    conn = _db()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if event == 'start':
            conn.execute("""
                INSERT INTO andromeda_flask_uptime
                (start_time, pid, exit_reason, auto_restarted)
                VALUES (?,?,?,?)
            """, (now, pid, reason, 1))
        elif event == 'exit':
            conn.execute("""
                UPDATE andromeda_flask_uptime
                SET end_time=?, exit_reason=?, alive_seconds=?
                WHERE pid=? AND end_time IS NULL
            """, (now, reason, alive_seconds, pid))
        conn.commit()
    finally:
        conn.close()

# ========== 健康检查 ==========
def check_flask_pid():
    """Flask PID 文件里的进程还活着?"""
    if not os.path.exists(PID_FILE):
        return False, None
    try:
        pid = int(open(PID_FILE).read().strip())
        os.kill(pid, 0)  # 不发信号, 只检查
        return True, pid
    except (ValueError, OSError):
        return False, None

def check_flask_http():
    """HTTP /index 200?"""
    try:
        req = urllib.request.Request(HEALTHY, headers={'Referer': 'http://localhost:8888/', 'User-Agent': 'Andromeda-SelfHeal/1.0'})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            return r.status == 200, r.status
    except urllib.error.HTTPError as e:
        return False, e.code
    except Exception as e:
        return False, str(e)

def check_port_listening():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex(('127.0.0.1', PORT))
    s.close()
    return result == 0

def check_db_writable():
    try:
        conn = _db()
        conn.execute("CREATE TABLE IF NOT EXISTS _ah_probe (x INTEGER)")
        conn.execute("INSERT INTO _ah_probe VALUES (1)")
        conn.execute("DROP TABLE _ah_probe")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# ========== 修复执行 ==========
def _run_fix_script(script, label='fix'):
    print(f"[ANROMEDA] 🔧 执行修复: {label}")
    try:
        result = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=30, cwd=FLASK_DIR)
        out = (result.stdout + result.stderr).strip()[:200]
        ok = result.returncode == 0
        print(f"  returncode={result.returncode} {'✅' if ok else '❌'} output={out[:100]}")
        return ok, out
    except subprocess.TimeoutExpired:
        print(f"  ❌ timeout")
        return False, 'timeout'
    except Exception as e:
        print(f"  ❌ {e}")
        return False, str(e)

def _kill_old_flasks():
    """杀所有 8888 上的进程"""
    kill_count = 0
    try:
        out = subprocess.getoutput(f"lsof -ti :{PORT} 2>/dev/null")
        for pid in out.split():
            if pid.strip():
                subprocess.getoutput(f"kill -9 {pid}")
                kill_count += 1
    except Exception:
        pass
    # 兜底
    subprocess.getoutput("pkill -9 -f 'python3 modular_start' 2>/dev/null")
    time.sleep(2)
    return kill_count

def _clean_port():
    """确保端口空"""
    _kill_old_flasks()
    for _ in range(5):
        if not check_port_listening():
            return True
        _kill_old_flasks()
        time.sleep(1)
    return not check_port_listening()

def _clear_pycache():
    subprocess.getoutput(f"find {FLASK_DIR} -name '__pycache__' -type d -exec rm -rf {{}} + 2>/dev/null")
    subprocess.getoutput("rm -f /tmp/flask_pid_8888")

def _start_flask():
    """启动 Flask, 返回 PID 或 None"""
    _clean_port()
    _clear_pycache()
    log_path = '/tmp/flask_auto_heal.log'
    # ANDROMEDA-EVOL / AUTOSYNC / OLLAMA 线程已在 modular_start.py 里被拦截
    cmd = f"cd {FLASK_DIR} && nohup python3 modular_start.py >> {log_path} 2>&1 & disown"
    subprocess.getoutput(cmd)
    # 写 PID 文件
    for _ in range(15):
        out = subprocess.getoutput(f"lsof -ti :{PORT} 2>/dev/null | head -1")
        if out.strip():
            open(PID_FILE, 'w').write(out.strip())
            return int(out.strip())
        time.sleep(1)
    return None

# ========== 自愈主逻辑 ==========
def attempt_recovery():
    """匹配特征库 → 执行修复"""
    conn = _db()
    try:
        # 1. Flask 死了
        alive, pid = check_flask_pid()
        http_ok, http_code = check_flask_http()
        port_ok = check_port_listening()
        db_ok = check_db_writable()

        print(f"[ANROMEDA] 📊 体检: pid={'✅'+str(pid) if alive else '❌'}, port={'✅' if port_ok else '❌'}, http={http_code}, db={'✅' if db_ok else '❌'}")

        anomalies = []
        if not port_ok and not alive:
            anomalies.append(('flask_dead', 'critical', f'PID文件无 + 端口{PORT}空'))
        elif alive and not http_ok:
            anomalies.append(('flask_stuck', 'critical', f'PID {pid} alive but HTTP {http_code}'))
        elif not alive and port_ok:
            anomalies.append(('zombie_port', 'warning', f'端口被无 PID 文件的进程占用'))
        if not db_ok:
            anomalies.append(('db_locked', 'warning', 'DB 写入测试失败 (被锁)'))

        for atype, severity, desc in anomalies:
            print(f"[ANROMEDA] 🔴 发现异常: {atype} ({severity}) — {desc[:60]}")

            # 查特征库找修复脚本
            seed = conn.execute("""
                SELECT * FROM andromeda_self_heal_log 
                WHERE anomaly_type=? AND resolved=0 ORDER BY frequency DESC LIMIT 1
            """, (atype,)).fetchone()

            fix_ok = False
            fix_out = ''
            fix_method = ''

            if seed and seed['fix_script']:
                fix_method = seed['fix_method'] or ''
                # 执行修复
                if atype in ('flask_dead', 'zombie_port'):
                    kill_n = _kill_old_flasks()
                    _clear_pycache()
                    new_pid = _start_flask()
                    fix_ok = new_pid is not None
                    fix_out = f"killed={kill_n} new_pid={new_pid}"
                    if fix_ok:
                        _log_uptime_event(new_pid, 'start', 'auto_restarted_by_andromeda')
                elif atype == 'flask_stuck':
                    _kill_old_flasks()
                    _clear_pycache()
                    new_pid = _start_flask()
                    fix_ok = new_pid is not None
                    fix_out = f"killed+restart new_pid={new_pid}"
                elif atype == 'db_locked':
                    subprocess.getoutput("pkill -9 -f ai_smart_mount 2>/dev/null")
                    subprocess.getoutput("pkill -9 -f 'python3.*engines' 2>/dev/null")
                    # Flask 也要重启因为它可能被 DB 锁堵死
                    _kill_old_flasks()
                    _clear_pycache()
                    new_pid = _start_flask()
                    fix_ok = new_pid is not None
                    fix_out = f"killed_daemons+restarted new_pid={new_pid}"
                else:
                    fix_ok, fix_out = _run_fix_script(seed['fix_script'] or 'echo noop', atype)
            else:
                # 兜底: 简单 kill+restart
                _kill_old_flasks()
                _clear_pycache()
                new_pid = _start_flask()
                fix_ok = new_pid is not None
                fix_out = f"fallback_restart new_pid={new_pid}"

            # 上报特征库
            _log_anomaly(
                anomaly_type=atype,
                severity=severity,
                description=desc,
                auto_fix_applied='restart_flask' if fix_ok else 'fix_failed',
                fix_method=fix_method or fix_out,
                success=1 if fix_ok else 0,
                ai_analysis='自动修复: kill旧进程 + 清cache + 重启Flask (modular_start.py)',
                tags=json.dumps([atype, 'self_heal'])
            )
    finally:
        conn.close()

# ========== 主循环 ==========
def main():
    print("=" * 60)
    print("🛰️ 仙女座自愈引擎 v1.0.0 启动")
    print(f"   DB:      {DB_PATH}")
    print(f"   PID:     {PID_FILE}")
    print(f"   Port:    {PORT}")
    print(f"   心跳:    {INTERVAL}s")
    print(f"   启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 初始检查 — Flask 活着就不动, 死了就拉
    alive, pid = check_flask_pid()
    http_ok, _ = check_flask_http()
    if alive and http_ok:
        print(f"[ANROMEDA] ✅ Flask PID={pid} 健康, 开始守护")
    else:
        print(f"[ANROMEDA] ⚠️ Flask 不健康 (pid={'✅' if alive else '❌'}, http={'✅' if http_ok else '❌'}), 执行首次恢复")
        attempt_recovery()

    last_anomaly_time = 0.0  # 上次异常时间 — 节流 300s 内同类型不重复上报
    while not _SHUTDOWN:
        time.sleep(INTERVAL)
        if _SHUTDOWN: break

        alive, pid = check_flask_pid()
        http_ok, http_code = check_flask_http()
        port_ok = check_port_listening()
        db_ok = check_db_writable()

        anomalies_count = (0 if alive else 1) + (0 if http_ok else 1) + (0 if port_ok else 1) + (0 if db_ok else 1)

        # 心跳上报
        try:
            _log_heartbeat(1 if alive else 0, 1 if http_ok else 0, 1 if db_ok else 0, anomalies_count)
        except Exception as e:
            pass  # 心跳写失败不中断

        if anomalies_count > 0:
            now_t = time.time()
            if now_t - last_anomaly_time > 60:  # 节流: 异常 60s 内只报一次
                print(f"[ANROMEDA] 🚨 检测到 {anomalies_count} 个异常 → 触发自愈")
                attempt_recovery()
                last_anomaly_time = now_t
        else:
            # 健康 — 每 5 个心跳打一行
            try:
                if int(time.time()) % (INTERVAL * 5) < INTERVAL:
                    print(f"[ANROMEDA] 💚 健康 PID={pid} HTTP=200 DB=OK")
            except Exception:
                pass

    print(f"\n[ANROMEDA] 👋 收到 SIGTERM, 退出")

if __name__ == '__main__':
    main()
