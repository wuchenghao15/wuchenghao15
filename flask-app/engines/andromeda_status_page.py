#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# andromeda_status_page.py — 仙女座后台状态页面 (独立 8889 端口)
#
# 只读 DB, 展示 (开发机本地监测):
#   - Daemon 状态 + 心跳
#   - system_notifications (实时)
#   - 演化日志
#   - 脑库总量 + 今日新增
#   - AI 员工活跃排行
#   - 图谱 / EigenFlux 活跃度
#   - Mac mini (HULK-MACMINI) 在线状态 + ping RTT + uptime + load
#
# mini 连接: 只读观测, 不参与双向同步
#   - ping 1s 超时检测在线
#   - SSH 3s 超时拉 uptime/load
#   - 上线/离线翻转时写一条 system_notifications (NEW badge 触发)
#
# 访问: http://localhost:8889/andromeda
# 自动刷新: 2.5s
# ─────────────────────────────────────────────────────────────
import sqlite3, json, time, os, sys, threading, subprocess, re

# 🆕 2026-09-20: DB 锁争用修复 — patch_sqlite3_connect (WAL + busy_timeout=60s)
try:
    import sys as _sys, os as _os
    _app_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _app_dir not in _sys.path:
        _sys.path.insert(0, _app_dir)
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception:
    pass
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, redirect

# ── mini 主机配置 (开发机本地, 只读观测) ──
MINI_HOST = "192.168.31.9"
MINI_NAME = "HULK-MACMINI"
MINI_USER = "wuchenghao"
MINI_SSH_TIMEOUT = 3
MINI_PING_TIMEOUT = 1

# 状态缓存 (只在变化时写通知)
_LAST_MINI_ONLINE = None

# mini 同步数据缓存 (30s, 避免每次 API 都 SSH)
_MINI_SYNC_CACHE = {"ts": 0, "data": None}
MINI_SYNC_CACHE_TTL = 30  # 秒

# mini DB 路径
MINI_DB_PATH = "/Users/wuchenghao/mtscos/flask-app/database/app.db"

# 对比的关键表 (按重要性排序)
SYNC_TABLES = [
    ("mt_andromeda_employee_registry", "🏛️ 员工注册中心"),
    ("ai_employees", "🧑‍💼 精选专家 (ai_employees)"),
    ("ai_brain_enhanced_knowledge", "🧠 脑库知识"),
    ("mt_daemon_registry", "⚙️ Daemon"),
    ("knowledge_graph_nodes", "🕸️ 图谱节点"),
    ("knowledge_graph_relations", "🔗 图谱关系"),
    ("mt_ai_self_evolution_log", "🧬 演化提案"),
    ("ai_learning_records", "📚 学习记录"),
    ("system_notifications", "🔔 通知"),
]

def _get_mini_sync():
    """SSH 拉 mini DB 关键表 count + 最近时间戳, 返回 list[dict]
    带 30s 缓存, mini 离线返回 all online=False
    """
    now = time.time()
    if _MINI_SYNC_CACHE["data"] and (now - _MINI_SYNC_CACHE["ts"]) < MINI_SYNC_CACHE_TTL:
        return _MINI_SYNC_CACHE["data"]
    
    # 先检查 mini 在线 (ping)
    try:
        ping = subprocess.run(
            ["ping", "-c", "1", "-W", str(MINI_PING_TIMEOUT), MINI_HOST],
            capture_output=True, text=True, timeout=MINI_PING_TIMEOUT + 2,
        )
        if ping.returncode != 0:
            # 离线 → 全部 offline
            result = {
                "online": False,
                "tables": [],
                "hostname": MINI_NAME,
                "db_path": MINI_DB_PATH,
                "checked_at": datetime.now().strftime("%H:%M:%S"),
            }
            _MINI_SYNC_CACHE["data"] = result
            _MINI_SYNC_CACHE["ts"] = now
            return result
    except Exception:
        pass
    
    # SSH 执行 Python 脚本拉数据 (stdin heredoc 方式, 避免引号嵌套问题)
    table_defs = ", ".join([f'("{t}", "{label}")' for t, label in SYNC_TABLES])
    py_script = f"""
import sqlite3, json, sys, os
DB = "{MINI_DB_PATH}"
tables_def = [{table_defs}]
result = []
try:
    c = sqlite3.connect(DB, timeout=5)
    for t, label in tables_def:
        try:
            cnt = c.execute(f"SELECT COUNT(*) FROM [{{t}}]").fetchone()[0]
            ts_col = None
            for col in [r[1] for r in c.execute(f"PRAGMA table_info([{{t}}])")]:
                if col in ("created_at","updated_at","last_heartbeat","heartbeat_at","generated_at","timestamp"):
                    ts_col = col; break
            ts = None
            if ts_col:
                try:
                    row = c.execute(f"SELECT MAX([{{ts_col}}]) FROM [{{t}}]").fetchone()
                    ts = row[0] if row and row[0] else None
                except: pass
            result.append({{"table": t, "label": label, "count": cnt, "last_ts": ts}})
        except Exception as e:
            result.append({{"table": t, "label": label, "count": None, "last_ts": None, "error": str(e)[:60]}})
    print(json.dumps({{"ok": True, "hostname": os.popen("hostname").read().strip(), "db_path": DB, "tables": result}}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({{"ok": False, "error": str(e)[:120]}}))
"""
    
    try:
        ssh = subprocess.run(
            ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
             "-o", "StrictHostKeyChecking=no",
             "-o", "BatchMode=yes",
             f"{MINI_USER}@{MINI_HOST}",
             "python3 -"],
            input=py_script, capture_output=True, text=True, timeout=MINI_SSH_TIMEOUT + 5,
        )
        if ssh.returncode == 0 and ssh.stdout.strip():
            data = json.loads(ssh.stdout.strip())
            # 合并开发机数据 → 形成对比
            c = db()
            compared = []
            for mini_row in data.get("tables", []):
                # 开发机 count
                local_cnt = None
                local_ts = None
                try:
                    local_cnt = c.execute(f"SELECT COUNT(*) FROM [{mini_row['table']}]").fetchone()[0]
                    ts_col = None
                    for col in [r[1] for r in c.execute(f"PRAGMA table_info([{mini_row['table']}])")]:
                        if col in ("created_at","updated_at","last_heartbeat","heartbeat_at","generated_at","timestamp"):
                            ts_col = col; break
                    if ts_col:
                        row = c.execute(f"SELECT MAX([{ts_col}]) FROM [{mini_row['table']}]").fetchone()
                        local_ts = row[0] if row and row[0] else None
                except Exception:
                    pass
                
                compared.append({
                    "table": mini_row["table"],
                    "label": mini_row["label"],
                    "local": local_cnt,
                    "local_last": _fmt_ts(local_ts),
                    "mini": mini_row["count"],
                    "mini_last": _fmt_ts(mini_row.get("last_ts")),
                    "mini_error": mini_row.get("error"),
                })
            c.close()
            
            result = {
                "online": True,
                "hostname": data.get("hostname", MINI_NAME),
                "db_path": MINI_DB_PATH,
                "tables": compared,
                "checked_at": datetime.now().strftime("%H:%M:%S"),
            }
        else:
            result = {"online": True, "ssh_ok": False, "tables": [], "hostname": MINI_NAME, "db_path": MINI_DB_PATH, "checked_at": datetime.now().strftime("%H:%M:%S")}
    except Exception as e:
        result = {"online": True, "ssh_ok": False, "error": str(e)[:100], "tables": [], "hostname": MINI_NAME, "db_path": MINI_DB_PATH, "checked_at": datetime.now().strftime("%H:%M:%S")}
    
    _MINI_SYNC_CACHE["data"] = result
    _MINI_SYNC_CACHE["ts"] = now
    return result

_ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
_FLASK_APP_DIR = os.path.dirname(_ENGINES_DIR)  # flask-app/
_DB_PATH = os.path.join(_FLASK_APP_DIR, "database", "app.db")

app = Flask(__name__)

def db():
    return sqlite3.connect(_DB_PATH, timeout=5)

def _fmt_ts(ts):
    """把各种 timestamp (Unix float / ISO str / None) 格式化成统一字符串"""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        try:
            # Unix 时间戳 → 本地时间
            return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
        except (OSError, OverflowError, ValueError):
            return str(ts)
    return str(ts)  # 已经是 ISO 字符串

# ─────────────────────────────────────────────────────────────
# Mac mini 连接检测 (只读观测, 不参与同步)
# ─────────────────────────────────────────────────────────────
def _check_mini():
    """检测 mini 在线状态 + SSH uptime/load, 返回 dict"""
    global _LAST_MINI_ONLINE
    result = {
        "host": MINI_HOST,
        "name": MINI_NAME,
        "online": False,
        "rtt_ms": None,
        "uptime": "—",
        "load": None,
        "users": None,
        "ssh_ok": False,
    }
    
    # 1. ping 检测
    try:
        ping = subprocess.run(
            ["ping", "-c", "1", "-W", str(MINI_PING_TIMEOUT), MINI_HOST],
            capture_output=True, text=True, timeout=MINI_PING_TIMEOUT + 2,
        )
        if ping.returncode == 0:
            result["online"] = True
            # macOS ping 输出: "round-trip min/avg/max/stddev = 4.293/4.293/4.293/nan ms"
            m = re.search(r"round-trip min/avg/max/stddev = [\d.]+/([\d.]+)/", ping.stdout)
            if m:
                result["rtt_ms"] = round(float(m.group(1)), 1)
    except Exception:
        pass
    
    # 2. SSH uptime/load
    if result["online"]:
        try:
            ssh = subprocess.run(
                ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
                 "-o", "StrictHostKeyChecking=no",
                 "-o", "BatchMode=yes",
                 f"{MINI_USER}@{MINI_HOST}",
                 "hostname; uptime"],
                capture_output=True, text=True, timeout=MINI_SSH_TIMEOUT + 2,
            )
            if ssh.returncode == 0:
                result["ssh_ok"] = True
                lines = ssh.stdout.strip().split("\n")
                # macOS uptime: "20:19  up 5 days, 16:50, 2 users, load averages: 9.97 6.38 3.76"
                for line in lines:
                    if "up " in line and "load" in line:
                        m_up = re.search(r"up\s+([\d:]+\s*[a-z]*(?:\s*[\d:]+)*)", line, re.IGNORECASE)
                        if m_up:
                            result["uptime"] = m_up.group(1).strip()
                        m_users = re.search(r"(\d+)\s+user", line)
                        if m_users:
                            result["users"] = int(m_users.group(1))
                        m_load = re.search(r"load averages?:\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
                        if m_load:
                            result["load"] = [float(m_load.group(i)) for i in (1, 2, 3)]
                        break
        except Exception:
            pass
    
    # 3. 状态变化 → 写通知 (只在翻转时)
    online_now = result["online"]
    if _LAST_MINI_ONLINE is not None and online_now != _LAST_MINI_ONLINE:
        try:
            nc = sqlite3.connect(_DB_PATH, timeout=3)
            if online_now:
                nc.execute(
                    "INSERT INTO system_notifications (title, content, level, status, created_at) VALUES (?,?,?,?,datetime('now','localtime'))",
                    (f"🟢 {MINI_NAME} 上线啦", f"IP={MINI_HOST} RTT={result['rtt_ms']}ms SSH={'OK' if result['ssh_ok'] else 'ping only'}", "success", "unread"))
            else:
                nc.execute(
                    "INSERT INTO system_notifications (title, content, level, status, created_at) VALUES (?,?,?,?,datetime('now','localtime'))",
                    (f"🔴 {MINI_NAME} 离线了", f"IP={MINI_HOST} ping 不通", "warning", "unread"))
            nc.commit()
            nc.close()
        except Exception:
            pass
    
    _LAST_MINI_ONLINE = online_now
    result["last_check"] = datetime.now().strftime("%H:%M:%S")
    return result

# ─────────────────────────────────────────────────────────────
# 数据 API
# ─────────────────────────────────────────────────────────────

@app.route('/api/data')
def get_data():
    """一次性返回所有状态数据 (前端 2.5s 轮询)"""
    c = db()
    
    # 1. Daemon 状态
    daemons = []
    for row in c.execute("""
        SELECT process_name, status, last_heartbeat, pid 
        FROM mt_daemon_registry 
        ORDER BY CASE status WHEN 'RUNNING' THEN 0 WHEN 'EVENT' THEN 1 WHEN 'READY' THEN 2 ELSE 3 END, last_heartbeat DESC
    """).fetchall():
        daemons.append({
            "name": row[0],
            "status": row[1],
            "hb": row[2] or "—",
            "pid": row[3],
        })
    
    # 2. 最近通知
    notifications = []
    for row in c.execute("""
        SELECT title, content, level, created_at 
        FROM system_notifications 
        ORDER BY rowid DESC LIMIT 20
    """).fetchall():
        notifications.append({
            "title": row[0], "content": row[1], 
            "level": row[2], "ts": row[3]
        })
    
    # 3. 演化日志
    evolutions = []
    for row in c.execute("""
        SELECT trigger_type, target_task, created_at 
        FROM mt_ai_self_evolution_log 
        ORDER BY rowid DESC LIMIT 15
    """).fetchall():
        evolutions.append({
            "type": row[0], "task": str(row[1])[:60], "ts": row[2]
        })
    
    # 4. 脑库统计
    brain_total = c.execute("SELECT COUNT(*) FROM ai_brain_enhanced_knowledge").fetchone()[0]
    brain_today = c.execute("""
        SELECT COUNT(*) FROM ai_brain_enhanced_knowledge 
        WHERE date(created_at, 'unixepoch') = date('now', 'localtime')
    """).fetchone()[0]
    brain_cats = []
    for row in c.execute("""
        SELECT category, COUNT(*) as cnt 
        FROM ai_brain_enhanced_knowledge 
        GROUP BY category ORDER BY cnt DESC LIMIT 10
    """).fetchall():
        brain_cats.append({"cat": row[0], "cnt": row[1]})
    
    # 5. 图谱
    nodes = c.execute("SELECT COUNT(*) FROM knowledge_graph_nodes").fetchone()[0]
    rels = c.execute("SELECT COUNT(*) FROM knowledge_graph_relations").fetchone()[0]
    
    # 6. AI 员工活跃 (精选专家 ai_employees, 总数 mt_andromeda_employee_registry)
    employee_total = c.execute(
        "SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE enabled = 1"
    ).fetchone()[0]

    # 注册表里还有多少活跃 (call_count > 0) 和 休眠 (call_count = 0)
    try:
        emp_active = c.execute(
            "SELECT COUNT(*) FROM mt_andromeda_employee_registry WHERE enabled=1 AND call_count > 0"
        ).fetchone()[0]
    except:
        emp_active = 0

    # 按 employee_type 聚合 TOP 10 类型 (最多的 AI 类型)
    registry_types = []
    try:
        for row in c.execute("""
            SELECT employee_type, COUNT(*) as cnt 
            FROM mt_andromeda_employee_registry 
            WHERE enabled = 1 
            GROUP BY employee_type 
            ORDER BY cnt DESC LIMIT 10
        """).fetchall():
            registry_types.append({"type": row[0] or "unknown", "count": row[1]})
    except:
        pass

    top_writers = []
    for row in c.execute("""
        SELECT name, skill_level, group_tag, description 
        FROM ai_employees 
        WHERE is_enabled = 1
        ORDER BY CASE WHEN typeof(skill_level)='real' THEN skill_level ELSE 0 END DESC, id ASC LIMIT 20
    """).fetchall():
        # skill_level 可能是数值也可能是字符串 (WRITER/POET/UI_MASTER 等)
        try:
            skill_val = float(row[1]) if row[1] not in (None, '') else 0.5
        except (ValueError, TypeError):
            skill_val = 0.5
        top_writers.append({
            "name": row[0], "skill": skill_val, 
            "skill_label": str(row[1]) if row[1] and not isinstance(row[1], (int,float)) else "",
            "group": row[2] or "", 
            "description": (row[3] or "")[:60],
        })
    
    # 7. EigenFlux 近 1h
    eigenflux_1h = c.execute("""
        SELECT COUNT(*) FROM eigenflux_comm_messages 
        WHERE created_at > datetime('now', '-1 hours', 'localtime')
    """).fetchone()[0]
    
    # 8. daemon config_json 里的 recent_events
    daemon_events = []
    for row in c.execute("""
        SELECT process_name, config_json FROM mt_daemon_registry 
        WHERE config_json IS NOT NULL AND config_json != ''
        ORDER BY last_heartbeat DESC LIMIT 3
    """).fetchall():
        try:
            cfg = json.loads(row[1])
            events = cfg.get("recent_events", [])[:5]
            daemon_events.append({"daemon": row[0], "events": events})
        except Exception:
            pass
    
    # 8. 演化趋势 (折线图: 最近 10 小时 × 每小时演化数)
    evo_trend = []
    for row in c.execute("""
        SELECT strftime('%H:00', created_at) as h, COUNT(*) as cnt
        FROM mt_ai_self_evolution_log
        WHERE created_at > datetime('now', '-10 hours', 'localtime')
        GROUP BY h ORDER BY h
    """).fetchall():
        evo_trend.append({"hour": row[0], "count": row[1]})
    
    # 9. 脑库增长趋势 (最近 7 天)
    brain_trend = []
    for row in c.execute("""
        SELECT date(created_at, 'unixepoch') as d, COUNT(*) as cnt
        FROM ai_brain_enhanced_knowledge
        WHERE created_at > strftime('%s', date('now', '-7 days', 'localtime'))
        GROUP BY d ORDER BY d
    """).fetchall():
        brain_trend.append({"date": row[0], "count": row[1]})
    
    # 10. EigenFlux 24h 消息趋势
    ef_trend = []
    for row in c.execute("""
        SELECT strftime('%H:00', created_at) as h, COUNT(*) as cnt
        FROM eigenflux_comm_messages
        WHERE created_at > datetime('now', '-24 hours', 'localtime')
        GROUP BY h ORDER BY h
    """).fetchall():
        ef_trend.append({"hour": row[0], "count": row[1]})
    
    # 11. 未读通知数 (用于提醒 badge)
    unread = c.execute("SELECT COUNT(*) FROM system_notifications WHERE status='unread'").fetchone()[0]
    
    c.close()
    
    # 12. Mac mini 连接检测 (单独调, 避免锁 DB 太久)
    mini = _check_mini()
    
    return jsonify({
        "daemons": daemons,
        "notifications": notifications,
        "evolutions": evolutions,
        "brain_total": brain_total,
        "brain_today": brain_today,
        "brain_cats": brain_cats,
        "brain_trend": brain_trend,
        "graph_nodes": nodes,
        "graph_rels": rels,
        "top_writers": top_writers,
        "employee_total": employee_total,
        "emp_active": emp_active,
        "registry_types": registry_types,
        "eigenflux_1h": eigenflux_1h,
        "ef_trend": ef_trend,
        "daemon_events": daemon_events,
        "evo_trend": evo_trend,
        "unread": unread,
        "mini": mini,
        "mini_sync": _get_mini_sync(),
        "generated_at": datetime.now().strftime("%H:%M:%S"),
    })

# ─────────────────────────────────────────────────────────────
# 手动刷新 mini_sync 缓存 (前端按钮调)
# ─────────────────────────────────────────────────────────────
@app.route('/api/sync/refresh', methods=['POST'])
def api_sync_refresh():
    """清缓存 + 重新拉 mini_sync"""
    _MINI_SYNC_CACHE["data"] = None
    _MINI_SYNC_CACHE["ts"] = 0
    _LAST_MINI_ONLINE = None  # 也让 mini 状态重新检测
    data = _get_mini_sync()
    return jsonify({"ok": True, "sync": data})

# ─────────────────────────────────────────────────────────────
# 手动双向同步 (开发机 ↔ mini, 两边取并集, 按主键 upsert)
# mini 离线返回 400, SSH/写入失败返回 500
# 策略: 先拉 mini 到开发机 (开发机拿 mini 的独有数据)
#       再推开发机到 mini (mini 拿开发机的独有数据)
#       最终两边都是并集, 幂等
# ─────────────────────────────────────────────────────────────
# 表定义: (表名, 主键列, 是否大表跳过)
MINI_SYNC_TABLES = [
    ("ai_employees", "id"),
    ("mt_daemon_registry", "process_name"),
    ("knowledge_graph_nodes", "id"),
    ("knowledge_graph_relations", "id"),
    ("mt_ai_self_evolution_log", "id"),
    ("ai_learning_records", "learn_id"),
    ("system_notifications", "id"),
    ("ai_brain_enhanced_knowledge", "knowledge_id:updated_at"),  # 脑库 133 万行, 按 updated_at 增量
]
MINI_DB_PATH_REMOTE = "/Users/wuchenghao/mtscos/flask-app/database/app.db"

@app.route('/api/sync/push', methods=['POST'])
def api_sync_push():
    """真正的双向同步: upsert, 两边取并集"""
    mini_info = _check_mini()
    if not mini_info["online"]:
        return jsonify({"ok": False, "error": "Mac mini 离线, 无法同步"}), 400
    
    results = []
    
    try:
        # ═══ Step 1: 开发机 ← mini (拉 mini 到开发机) ═══
        # 先查开发机每张表的最大 updated_at (给大表做增量用)
        c_local = db()
        local_max_ts = {}
        for tbl, pk in MINI_SYNC_TABLES:
            # 大表 (带 updated_at 后缀) 增量拉
            if ":" in pk:
                ts_col = pk.split(":")[1]
                try:
                    local_max_ts[tbl] = c_local.execute(
                        f"SELECT MAX([{ts_col}]) FROM [{tbl}]"
                    ).fetchone()[0]
                except Exception:
                    local_max_ts[tbl] = None
        c_local.close()
        
        pull_code = f"""# -*- coding: utf-8 -*-
import sqlite3, json

DB = {json.dumps(MINI_DB_PATH_REMOTE)}
TABLES = {json.dumps(MINI_SYNC_TABLES)}
LOCAL_MAX_TS = {json.dumps(local_max_ts)}
c = sqlite3.connect(DB, timeout=10)
c.execute('PRAGMA busy_timeout = 30000')
out = {{}}
for tbl, pk in TABLES:
    try:
        cols = [r[1] for r in c.execute(f'PRAGMA table_info({{tbl}})')]
        ts_max = LOCAL_MAX_TS.get(tbl)
        if ':' in pk and ts_max is not None:
            # 大表增量: 只拉 updated_at > 开发机 max 的行
            ts_col = pk.split(':')[1]
            rows = c.execute(f'SELECT * FROM [{{tbl}}] WHERE [{{ts_col}}] > {{ts_max}}').fetchall()
            out[tbl] = {{'cols': cols, 'rows': [[v if v is not None else None for v in r] for r in rows], 'incremental': True}}
        else:
            rows = c.execute(f'SELECT * FROM [{{tbl}}]').fetchall()
            out[tbl] = {{'cols': cols, 'rows': [[v if v is not None else None for v in r] for r in rows], 'incremental': False}}
    except Exception as e:
        out[tbl] = {{'error': str(e)[:100]}}
c.close()
print(json.dumps(out, ensure_ascii=False, default=str))
"""
        ssh_pull = subprocess.run(
            ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
             "-o", "BatchMode=yes",
             f"{MINI_USER}@{MINI_HOST}",
             "python3 -"],
            input=pull_code, capture_output=True, text=True, timeout=30,
        )
        if ssh_pull.returncode != 0:
            return jsonify({"ok": False, "error": f"SSH 拉取失败: {ssh_pull.stderr[:200]}"}), 500
        
        mini_data = json.loads(ssh_pull.stdout.strip())
        
        # 开发机 upsert mini 数据
        c = db()
        for tbl, pk in MINI_SYNC_TABLES:
            info = mini_data.get(tbl, {})
            if "error" in info:
                results.append(f"SKIP 拉 {tbl}: {info['error']}")
                continue
            try:
                cols = info["cols"]
                rows = info["rows"]
                col_list = ", ".join([f"[{col}]" for col in cols])
                # UPSERT: INSERT OR REPLACE (SQLite)
                ph = ",".join(["?"] * len(cols))
                c.executemany(
                    f"INSERT OR REPLACE INTO [{tbl}] ({col_list}) VALUES ({ph})",
                    rows
                )
                new_cnt = c.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                results.append(f"⬇️ 拉 {tbl}: {len(rows)} 行 → 开发机 now {new_cnt}")
            except Exception as e:
                results.append(f"ERR 拉 {tbl}: {str(e)[:60]}")
        c.commit()
        c.close()
        
        # ═══ Step 2: 开发机 → mini (推开发机到 mini) ═══
        # mini 端的 max_ts (通过 SSH 查) — 用于开发机增量推
        mini_max_ts = {}
        try:
            _mini_ts_check = subprocess.run(
                ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
                 "-o", "BatchMode=yes",
                 f"{MINI_USER}@{MINI_HOST}",
                 "python3 -"],
                input=f"""import sqlite3, json
DB = {json.dumps(MINI_DB_PATH_REMOTE)}
c = sqlite3.connect(DB, timeout=10)
out = {{}}
for tbl, pk in {json.dumps([(t, p) for t, p in MINI_SYNC_TABLES if ':' in p])}:
    ts_col = pk.split(':')[1]
    try:
        r = c.execute(f'SELECT MAX([{{ts_col}}]) FROM [{{tbl}}]').fetchone()
        out[tbl] = r[0] if r and r[0] else None
    except: pass
c.close()
print(json.dumps(out))
""",
                capture_output=True, text=True, timeout=10,
            )
            if _mini_ts_check.returncode == 0 and _mini_ts_check.stdout.strip():
                mini_max_ts = json.loads(_mini_ts_check.stdout.strip())
        except Exception:
            pass
        
        push_payload = {}
        c = db()
        for tbl, pk in MINI_SYNC_TABLES:
            try:
                cols = [r[1] for r in c.execute(f"PRAGMA table_info([{tbl}])")]
                is_incremental = ":" in pk and mini_max_ts.get(tbl) is not None
                if is_incremental:
                    # 增量: updated_at > mini.max 的行
                    ts_col = pk.split(":")[1]
                    pk_col = pk.split(":")[0]
                    rows = c.execute(
                        f"SELECT * FROM [{tbl}] WHERE [{ts_col}] > ?",
                        (mini_max_ts[tbl],)
                    ).fetchall()
                    # 双保险: knowledge_id 差集 — 额外推 dev 独有的行
                    # 这些行的 updated_at 可能比 mini_max 小, 但 knowledge_id mini 端完全没有
                    extra_rows = []
                    try:
                        # 查 dev 全部 pk
                        all_dev_pks = set(r[0] for r in c.execute(f"SELECT [{pk_col}] FROM [{tbl}]").fetchall())
                        # SSH mini 查 mini 全部 pk (只查 pk 列, 很快)
                        _mini_pk_check = subprocess.run(
                            ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
                             "-o", "BatchMode=yes",
                             f"{MINI_USER}@{MINI_HOST}",
                             "python3 -"],
                            input=f"import sqlite3; c=sqlite3.connect({json.dumps(MINI_DB_PATH_REMOTE)}); print('\\n'.join(str(r[0]) for r in c.execute(f'SELECT [{pk_col}] FROM [{tbl}]'))); c.close()",
                            capture_output=True, text=True, timeout=15,
                        )
                        if _mini_pk_check.returncode == 0 and _mini_pk_check.stdout.strip():
                            mini_pks = set(line.strip() for line in _mini_pk_check.stdout.strip().split("\n") if line.strip())
                            dev_only_pks = all_dev_pks - mini_pks
                            if dev_only_pks:
                                ph = ",".join(["?"] * len(dev_only_pks))
                                extra_rows = c.execute(
                                    f"SELECT * FROM [{tbl}] WHERE [{pk_col}] IN ({ph})",
                                    list(dev_only_pks)
                                ).fetchall()
                                results.append(f"⚠️ [{tbl}] 额外补推 {len(extra_rows)} 行 (knowledge_id mini 端不存在)")
                    except Exception as ex:
                        results.append(f"[{tbl}] knowledge_id 差集跳过: {str(ex)[:60]}")
                    
                    all_rows = list(rows) + [r for r in extra_rows if r not in rows]  # 去重
                    info = {"cols": cols, "rows": [[v if v is not None else None for v in row] for row in all_rows], "incremental": True, "pk_col": pk_col}
                else:
                    rows = c.execute(f"SELECT * FROM [{tbl}]").fetchall()
                    info = {"cols": cols, "rows": [[v if v is not None else None for v in row] for row in rows], "incremental": False}
                push_payload[tbl] = info
            except Exception as e:
                push_payload[tbl] = {"error": str(e)[:100]}
        c.close()
        
        local_json = "/tmp/mtscos_biway_sync.json"
        with open(local_json, "w", encoding="utf-8") as f:
            json.dump(push_payload, f, ensure_ascii=False, default=str)
        
        scp = subprocess.run(
            ["scp", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
             "-o", "BatchMode=yes",
             local_json, f"{MINI_USER}@{MINI_HOST}:/tmp/mtscos_biway_sync.json"],
            capture_output=True, timeout=15,
        )
        if scp.returncode != 0:
            return jsonify({"ok": False, "error": f"scp 失败: {scp.stderr.decode(errors='replace')[:120]}"}), 500
        
        push_code = f"""# -*- coding: utf-8 -*-
import sqlite3, json

DB = {json.dumps(MINI_DB_PATH_REMOTE)}
data = json.load(open('/tmp/mtscos_biway_sync.json'))
c = sqlite3.connect(DB, timeout=30)
c.execute('PRAGMA busy_timeout = 30000')  # 等锁最多 30s
for tbl, info in data.items():
    if 'error' in info:
        continue
    try:
        cols = info['cols']
        rows = info['rows']
        # 1. 先检查 mini 表缺哪些列, 补列
        existing_cols = [r[1] for r in c.execute(f'PRAGMA table_info([{{tbl}}])')]
        for col in cols:
            if col not in existing_cols:
                try:
                    c.execute(f'ALTER TABLE [{{tbl}}] ADD COLUMN [{{col}}]')
                    print(f'  ALTER {{tbl}} ADD COLUMN {{col}}')
                except Exception as e:
                    print(f'  ALTER {{tbl}} {{col}}: {{str(e)[:40]}}')
        c.commit()
        # 2. 重新读 mini 现有列, 确定交集 (避免列不匹配)
        existing_cols = [r[1] for r in c.execute(f'PRAGMA table_info([{{tbl}}])')]
        upsert_cols = [col for col in cols if col in existing_cols]
        if not upsert_cols:
            print(f'  SKIP {{tbl}}: 无匹配列')
            continue
        # 3. 用子集列 upsert
        col_list = ', '.join([f'[{{col}}]' for col in upsert_cols])
        col_idx = [cols.index(col) for col in upsert_cols]
        filtered_rows = [[row[i] for i in col_idx] for row in rows]
        ph = ','.join(['?'] * len(upsert_cols))
        c.executemany(
            f'INSERT OR REPLACE INTO [{{tbl}}] ({{col_list}}) VALUES ({{ph}})',
            filtered_rows
        )
        new_cnt = c.execute(f'SELECT COUNT(*) FROM [{{tbl}}]').fetchone()[0]
        print(f'  OK {{tbl}}: {{len(filtered_rows)}} 行 upsert, now {{new_cnt}}')
    except Exception as e:
        print(f'  ERR {{tbl}}: {{str(e)[:60]}}')
c.commit()
c.close()
print('OK 双向同步完成')
"""
        
        ssh_push = subprocess.run(
            ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
             "-o", "BatchMode=yes",
             f"{MINI_USER}@{MINI_HOST}",
             "python3 -"],
            input=push_code, capture_output=True, text=True, timeout=30,
        )
        if ssh_push.returncode != 0:
            return jsonify({"ok": False, "error": f"SSH 推送失败: {ssh_push.stderr[:200]}"}), 500
        
        # ── 追加: mini 端文件系统整理 (与开发机保持一致) ──
        file_clean_code = r"""
import os, glob, shutil, time

run_dir = os.path.expanduser("~/.mtscos/run")
os.makedirs(run_dir, exist_ok=True)
logs_dir = os.path.join(run_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)

cleaned = []

# 1. 清理 /tmp 里 andromeda_* 残留 (旧状态页日志/pid)
for pat in ["/tmp/andromeda_*.log", "/tmp/andromeda_v*.log", "/tmp/andromeda_*sync*.sh", "/tmp/mock_mini_*", "/tmp/check_mini*", "/tmp/andromeda_status_page.pid"]:
    for f in glob.glob(pat):
        try:
            sz = os.path.getsize(f)
            os.remove(f)
            cleaned.append("rm %s (%d bytes)" % (os.path.basename(f), sz))
        except Exception as e:
            cleaned.append("skip %s: %s" % (os.path.basename(f), e))

# 2. 清理 mini 端 flask-app/engines/ 里的 .bak / 过大 .log
engines_dir = os.path.expanduser("~/mtscos/flask-app/engines")
if os.path.isdir(engines_dir):
    archive_dir = os.path.join(engines_dir, "_runtime", "archive")
    os.makedirs(archive_dir, exist_ok=True)
    logs_d = os.path.join(engines_dir, "_runtime", "logs")
    os.makedirs(logs_d, exist_ok=True)
    
    for f in os.listdir(engines_dir):
        fp = os.path.join(engines_dir, f)
        if not os.path.isfile(fp):
            continue
        # 过时 DB 副本
        if f.endswith(".db") and f != "app.db":
            dst = os.path.join(archive_dir, f + ".obsolete_" + time.strftime("%Y%m%d"))
            os.rename(fp, dst)
            cleaned.append("mv engines/%s → archive/ (%d bytes)" % (f, os.path.getsize(dst)))
        # .bak_* 备份
        elif ".bak_" in f or f.endswith(".bak"):
            try:
                os.rename(fp, os.path.join(archive_dir, f))
                cleaned.append("mv engines/%s → archive/" % f)
            except Exception as e:
                cleaned.append("skip bak %s: %s" % (f, e))
        # 超过 5MB 的 .log → 截断/归档
        elif f.endswith(".log") and os.path.getsize(fp) > 5 * 1024 * 1024:
            dst = os.path.join(logs_d, f + ".truncated_" + time.strftime("%Y%m%d"))
            os.rename(fp, dst)
            cleaned.append("mv engines/%s → logs/ (%d bytes)" % (f, os.path.getsize(dst)))

print(json.dumps({"ok": True, "cleaned": cleaned}, ensure_ascii=False))
"""
        try:
            file_clean = subprocess.run(
                ["ssh", "-o", f"ConnectTimeout={MINI_SSH_TIMEOUT}",
                 "-o", "BatchMode=yes",
                 f"{MINI_USER}@{MINI_HOST}",
                 "python3 -"],
                input=file_clean_code, capture_output=True, text=True, timeout=15,
            )
            if file_clean.returncode == 0 and file_clean.stdout.strip():
                import json as _json
                try:
                    fc = _json.loads(file_clean.stdout.strip())
                    results.append("FILESYS mini 整理: %d 项" % len(fc.get("cleaned", [])))
                    for c in fc.get("cleaned", []):
                        results.append("  %s" % c)
                except Exception:
                    results.append("FILESYS mini: %s" % file_clean.stdout.strip()[:200])
            else:
                results.append("FILESYS mini 跳过 (离线/无权限)")
        except Exception as e:
            results.append("FILESYS mini 失败: %s" % str(e)[:80])
        
        # 清缓存
        _MINI_SYNC_CACHE["data"] = None
        _MINI_SYNC_CACHE["ts"] = 0
        
        return jsonify({"ok": True, "results": results, "mini_push": ssh_push.stdout.strip()})
    
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "SSH 超时"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)[:200]}), 500

# ─────────────────────────────────────────────────────────────
# AI 员工搜索 (分页, 支持按 name/type/source 搜)
# ─────────────────────────────────────────────────────────────
@app.route('/api/employees')
def api_employees():
    q = request.args.get('q', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    limit = min(100, max(1, int(request.args.get('limit', 20))))
    offset = (page - 1) * limit
    
    c = db()
    
    if q:
        like = f"%{q}%"
        where = "WHERE enabled=1 AND (name LIKE ? OR employee_type LIKE ? OR employee_source LIKE ? OR host_id LIKE ?)"
        params = [like, like, like, like]
    else:
        where = "WHERE enabled=1"
        params = []
    
    total = c.execute(
        f"SELECT COUNT(*) FROM mt_andromeda_employee_registry {where}", params
    ).fetchone()[0]
    
    rows = c.execute(f"""
        SELECT employee_id, name, employee_type, employee_source, level,
               call_count, enabled, registered_at, host_id
        FROM mt_andromeda_employee_registry
        {where}
        ORDER BY call_count DESC, level DESC, registered_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset]).fetchall()
    
    # 附加精选专家 ai_employees 信息 (如果 employee_source 匹配)
    enriched = []
    for r in rows:
        employee_id, name, etype, esource, level, calls, enabled, reg_at, host = r
        # 查 ai_employees 精选专家表有没有同名
        desc = ""
        try:
            d = c.execute("SELECT description, skill_level, group_tag FROM ai_employees WHERE name=?", (name,)).fetchone()
            if d: desc = d[0] or ""
        except: pass
        enriched.append({
            "employee_id": employee_id, "name": name, "employee_type": etype,
            "employee_source": esource, "level": level or 0, "call_count": calls or 0,
            "registered_at": reg_at, "host_id": host or "", "description": desc[:60],
        })
    
    # 类型聚合 (sidebar 显示)
    type_agg = []
    try:
        for r2 in c.execute("""
            SELECT employee_type, COUNT(*) as cnt
            FROM mt_andromeda_employee_registry
            WHERE enabled=1
            GROUP BY employee_type ORDER BY cnt DESC LIMIT 15
        """).fetchall():
            type_agg.append({"type": r2[0] or "unknown", "count": r2[1]})
    except: pass
    
    c.close()
    
    return jsonify({
        "ok": True, "total": total, "page": page, "limit": limit,
        "pages": (total + limit - 1) // limit, "rows": enriched,
        "types": type_agg, "q": q,
    })

# ─────────────────────────────────────────────────────────────
# HTML 状态页 (单文件, 纯原生 JS, 2.5s 自动刷新)
# ─────────────────────────────────────────────────────────────

STATUS_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 仙女座 AI · 后台状态监控</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0a0e1a; --card: #111827; --border: #1e293b;
    --text: #e2e8f0; --muted: #64748b; --accent: #3b82f6;
    --green: #22c55e; --red: #ef4444; --yellow: #eab308; --blue: #3b82f6;
    --purple: #8b5cf6;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg); color: var(--text); padding: 24px; font-size: 16px;
    background-image: radial-gradient(circle at 20% 20%, rgba(59,130,246,0.08), transparent 50%),
                      radial-gradient(circle at 80% 80%, rgba(139,92,246,0.08), transparent 50%);
    min-height: 100vh;
  }
  
  /* ===== Header ===== */
  .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
  h1 { font-size: 28px; font-weight: 700; }
  .subtitle { color: var(--muted); font-size: 15px; margin-top: 4px; }
  /* 连接状态指示器 */
  .conn { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; animation: pulseConn 2s infinite; }
  .conn-ok { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
  .conn-retry { background: #eab308; box-shadow: 0 0 6px #eab308; }
  .conn-offline { background: #ef4444; box-shadow: 0 0 6px #ef4444; animation: none; }
  @keyframes pulseConn { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
  .refresh-badge { font-size: 13px; color: var(--muted); font-family: monospace; }
  
  /* ===== KPI Row ===== */
  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .kpi {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 20px 22px; position: relative; overflow: hidden;
  }
  .kpi::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--kpi-color, var(--accent));
  }
  .kpi-label { font-size: 14px; color: var(--muted); font-weight: 500; }
  .kpi-value { font-size: 36px; font-weight: 800; margin-top: 6px; font-variant-numeric: tabular-nums;
    background: linear-gradient(90deg, var(--kpi-color, var(--accent)), #8b5cf6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .kpi-sub { font-size: 13px; color: var(--muted); margin-top: 4px; }
  .kpi.green { --kpi-color: var(--green); }
  .kpi.blue  { --kpi-color: var(--blue); }
  .kpi.purple{ --kpi-color: var(--purple); }
  .kpi.yellow{ --kpi-color: var(--yellow); }
  
  /* ===== Card grid ===== */
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; }
  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 22px;
  }
  .card-wide { grid-column: span 2; }
  .card h2 {
    font-size: 18px; font-weight: 600; margin-bottom: 16px; color: var(--accent);
    display: flex; align-items: center; gap: 10px;
  }
  
  /* ===== Charts ===== */
  .chart-box { height: 240px; position: relative; }
  
  /* ===== Daemon ===== */
  .daemon-row { display: flex; align-items: center; justify-content: space-between; padding: 9px 0; font-size: 15px; border-bottom: 1px solid rgba(255,255,255,0.04); }
  .daemon-row:last-child { border-bottom: none; }
  .daemon-left { display: flex; align-items: center; gap: 10px; }
  .pulse { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .pulse.green { background: var(--green); animation: pulse 2s infinite; }
  .pulse.yellow { background: var(--yellow); } .pulse.red { background: var(--red); } .pulse.blue { background: var(--blue); }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
  .daemon-name { font-family: 'SF Mono', monospace; font-size: 14px; }
  .status-badge { padding: 2px 10px; border-radius: 20px; font-size: 13px; font-weight: 600; }
  .status-badge.running { background: rgba(34,197,94,0.15); color: var(--green); }
  .status-badge.ready { background: rgba(234,179,8,0.15); color: var(--yellow); }
  .status-badge.offline { background: rgba(239,68,68,0.15); color: var(--red); }
  .status-badge.event { background: rgba(59,130,246,0.15); color: var(--blue); }
  
  /* ===== Notifications (with new badge) ===== */
  .section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
  .section-head h2 { margin-bottom: 0; }
  .new-badge {
    background: var(--red); color: #fff; padding: 2px 10px; border-radius: 20px;
    font-size: 13px; font-weight: 700; animation: blink 1.5s infinite;
  }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
  .notify-item { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
  .notify-item:last-child { border-bottom: none; }
  .notify-new { border-left: 3px solid var(--accent); padding-left: 12px; animation: slideIn 0.4s; }
  @keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: none; } }
  .notify-title { font-weight: 600; font-size: 15px; }
  .notify-content { font-size: 14px; color: var(--muted); margin-top: 3px; }
  .notify-ts { font-size: 13px; color: var(--muted); }
  .level-info { color: var(--blue); } .level-success { color: var(--green); }
  .level-warning { color: var(--yellow); } .level-error { color: var(--red); } .level-critical { color: var(--red); }
  
  /* ===== Collapsible ===== */
  details { border-top: 1px solid var(--border); margin-top: 14px; padding-top: 10px; }
  details > summary {
    cursor: pointer; font-size: 14px; color: var(--muted); padding: 6px 0;
    user-select: none; list-style: none; display: flex; align-items: center; gap: 6px;
  }
  details > summary::-webkit-details-marker { display: none; }
  details > summary::before { content: '▶'; transition: transform 0.2s; font-size: 11px; }
  details[open] > summary::before { transform: rotate(90deg); }
  .stat-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; color: var(--muted); }
  .stat-val { color: var(--text); font-weight: 600; }
  
  /* ===== Writers ===== */
  .writer-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04); gap: 10px; align-items: flex-start; }
  .writer-item:last-child { border-bottom: none; }
  .writer-name { font-weight: 600; }
  .writer-meta { color: var(--muted); font-size: 12px; white-space: nowrap; }
  .ai-info { flex: 1; min-width: 0; }
  .ai-desc { font-size: 12px; color: var(--muted); margin-top: 2px; line-height: 1.4; }
  .ai-skill-tag { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 8px; background: rgba(139,92,246,0.2); color: #a78bfa; margin-left: 6px; font-weight: 400; letter-spacing: 0.5px; }
  
  @media (max-width: 900px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
    .card-wide { grid-column: span 1; }
  }

  /* ── Mini Host Status Bar ── */
  .mini-bar {
    background: linear-gradient(135deg, #1e2a3a 0%, #1a2432 100%);
    border: 1px solid #2a3a4e;
    border-radius: 12px;
    padding: 14px 20px;
    font-size: 13px;
    height: 100%;
    box-sizing: border-box;
  }
  /* mini-bar 和 sync-panel 组成两列 */
  .top-bar-row {
    display: grid; grid-template-columns: minmax(340px, 0.9fr) 1.3fr;
    gap: 16px; margin-bottom: 20px;
  }
  @media (max-width: 900px) {
    .top-bar-row { grid-template-columns: 1fr; }
  }
  .mini-status {
    display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
  }
  .mini-dot {
    font-size: 16px; animation: pulse 1.5s ease-in-out infinite;
  }
  .mini-dot.online { color: #2ecc71; text-shadow: 0 0 8px #2ecc7180; }
  .mini-dot.offline { color: #e74c3c; text-shadow: 0 0 8px #e74c3c80; animation: none; }
  .mini-dot.checking { color: #f39c12; animation: none; }
  .mini-host { font-weight: 700; color: #ecf0f1; font-size: 14px; }
  .mini-ip { color: #7f8c8d; font-family: monospace; }
  .mini-ssh { color: #3498db; }
  .mini-ssh.fail { color: #e74c3c; }
  .mini-rtt { color: #f1c40f; }
  .mini-uptime { color: #9b59b6; }
  .mini-load { color: #1abc9c; font-family: monospace; }
  .mini-load.warn { color: #e67e22; }
  .mini-load.hot { color: #e74c3c; }
  .mini-users { color: #bdc3c7; }
  .mini-check { margin-left: auto; color: #7f8c8d; font-size: 11px; }

  /* ── Sync Comparison Panel ── */
  .sync-panel {
    background: linear-gradient(135deg, #16202a 0%, #121a24 100%);
    border: 1px solid #2a3a4e;
    border-radius: 12px;
    padding: 14px 20px;
    height: 100%;
    box-sizing: border-box;
  }
  .sync-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 12px; font-size: 13px;
  }
  .sync-title { font-weight: 700; color: #ecf0f1; font-size: 14px; }
  .sync-sub { color: #7f8c8d; font-size: 11px; }
  .sync-table {
    width: 100%; border-collapse: collapse; font-size: 13px;
  }
  .sync-table th {
    text-align: left; padding: 6px 10px; color: #7f8c8d; font-weight: 500;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
    border-bottom: 1px solid #2a3a4e;
  }
  .sync-table td {
    padding: 7px 10px; border-bottom: 1px solid rgba(42,58,78,0.5);
    vertical-align: middle;
  }
  .sync-table tr:last-child td { border-bottom: none; }
  .sync-label { color: #bdc3c7; }
  .sync-local { color: #3498db; font-family: monospace; text-align: right; }
  .sync-mini { color: #9b59b6; font-family: monospace; text-align: right; }
  .sync-diff { text-align: right; font-family: monospace; font-weight: 600; }
  .sync-diff.plus { color: #2ecc71; }    // 开发机多 → 绿色
  .sync-diff.minus { color: #e67e22; }   // mini 多 → 橙色
  .sync-diff.equal { color: #7f8c8d; }   // 相等 → 灰色
  .sync-diff.na { color: #4a5568; }      // 一方不存在
  .sync-last { color: #7f8c8d; font-size: 11px; text-align: right; font-family: monospace; }
  .sync-offline-hint {
    color: #7f8c8d; text-align: center; padding: 16px; font-size: 13px;
  }
  .sync-header-row {
    display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; gap: 10px;
    padding: 0 10px; font-size: 11px; color: #7f8c8d;
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;
  }
  .sync-row {
    display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; gap: 10px;
    padding: 6px 10px; align-items: center;
    border-bottom: 1px solid rgba(42,58,78,0.4);
  }
  .sync-row:last-child { border-bottom: none; }
  .sync-row > div:last-child { text-align: right; }
  .sync-row .v-local { text-align: right; color: #3498db; font-family: monospace; }
  .sync-row .v-mini { text-align: right; color: #9b59b6; font-family: monospace; }
  .sync-row .v-diff { text-align: right; font-family: monospace; font-weight: 600; }
  .v-diff.plus { color: #2ecc71; }
  .v-diff.minus { color: #e67e22; }
  .v-diff.equal { color: #7f8c8d; }
  .v-diff.na { color: #4a5568; }

  /* ── Sync Action Buttons ── */
  .sync-actions { display: flex; gap: 8px; }
  .btn-sync {
    font-size: 11px; padding: 4px 12px; border-radius: 6px;
    border: 1px solid #2a3a4e; cursor: pointer; font-weight: 600;
    transition: all 0.15s; font-family: inherit;
  }
  .btn-sync:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-sync.refresh {
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    color: #fff; border-color: #2563eb;
  }
  .btn-sync.refresh:hover:not(:disabled) { background: linear-gradient(135deg, #2563eb, #3b82f6); }
  .btn-sync.push {
    background: linear-gradient(135deg, #14532d, #16a34a);
    color: #fff; border-color: #16a34a;
  }
  .btn-sync.push:hover:not(:disabled) { background: linear-gradient(135deg, #16a34a, #22c55e); }
  .btn-sync.push:disabled {
    background: #374151; border-color: #4b5563; color: #9ca3af;
  }
  .sync-toast {
    font-size: 11px; padding: 3px 8px; border-radius: 4px;
    background: rgba(34,197,94,0.2); color: #22c55e;
  }
  .sync-toast.error { background: rgba(239,68,68,0.2); color: #ef4444; }
  .sync-toast.working { background: rgba(234,179,8,0.2); color: #eab308; }

  /* ===== 同步结果 Modal ===== */
  .sync-modal-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999; animation: fadeIn 0.2s ease;
  }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  .sync-modal {
    background: #0d1117; border: 1px solid #2a3a4e; border-radius: 10px;
    width: 720px; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;
    animation: slideUp 0.25s ease;
  }
  @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  .sync-modal-header {
    padding: 14px 18px; background: linear-gradient(90deg, #1e293b, #0d1117);
    border-bottom: 1px solid #2a3a4e; display: flex; justify-content: space-between;
    align-items: center; font-weight: 600; font-size: 15px; color: #22c55e;
  }
  .sync-modal-close {
    cursor: pointer; font-size: 20px; color: #64748b; line-height: 1;
    transition: color 0.15s;
  }
  .sync-modal-close:hover { color: #ef4444; }
  .sync-modal-body {
    padding: 14px 18px; overflow-y: auto; font-family: 'SF Mono', 'Menlo', monospace; font-size: 12px;
  }
  .modal-section { margin-bottom: 14px; }
  .modal-section:last-child { margin-bottom: 0; }
  .modal-section-title {
    color: #8b5cf6; font-weight: 600; font-size: 12px; margin-bottom: 8px;
    padding-bottom: 4px; border-bottom: 1px solid #2a3a4e;
  }
  .modal-row { padding: 3px 6px; border-radius: 3px; color: #94a3b8; white-space: pre-wrap; }
  .modal-pull { background: rgba(59,130,246,0.12); color: #60a5fa; }
  .modal-push { background: rgba(34,197,94,0.12); color: #4ade80; }
  .modal-filesys { background: rgba(139,92,246,0.12); color: #a78bfa; }
  .modal-error { background: rgba(239,68,68,0.15); color: #f87171; }
  .modal-info { color: #94a3b8; }
  .modal-stdout {
    background: #000; border-radius: 5px; padding: 10px 12px;
    color: #22c55e; font-size: 11px; max-height: 160px; overflow-y: auto;
    border: 1px solid #22c55e30;
  }
</style>
</head>
<body>

<!-- ===== Header ===== -->
<div class="header-bar">
  <div>
    <h1>🧬 仙女座 AI · 后台状态</h1>
    <div class="subtitle">
      <span id="conn-indicator" class="conn conn-ok">●</span>
      <span id="conn-label">已连接</span>
      <span style="color:#2a3a4e;">·</span>
      239 AI 员工 · 19 daemon · 冰山三层实时监控
    </div>
  </div>
  <div class="refresh-badge" id="ts">—</div>
</div>

<!-- ===== KPI Row (主次分明: 大数字最显眼) ===== -->
<div class="kpi-row">
  <div class="kpi blue"><div class="kpi-label">🧠 脑库总量</div><div class="kpi-value" id="kpi-brain">—</div><div class="kpi-sub" id="kpi-brain-sub">—</div></div>
  <div class="kpi green"><div class="kpi-label">⚙️ RUNNING Daemon</div><div class="kpi-value" id="kpi-daemon">—</div><div class="kpi-sub" id="kpi-daemon-sub">休眠 ? 个 · 守护自动拉起</div></div>
  <div class="kpi purple"><div class="kpi-label">🧬 今日演化触发</div><div class="kpi-value" id="kpi-evo">—</div><div class="kpi-sub">自动演化频率</div></div>
  <div class="kpi yellow"><div class="kpi-label">�️ AI 员工注册</div><div class="kpi-value" id="kpi-writer">—</div><div class="kpi-sub" id="kpi-writer-sub">33,525 enabled</div></div>
</div>

<!-- ===== Top Bar: Mini Status (左) + Sync Comparison (右) ===== -->
<div class="top-bar-row">

<!-- ===== Mini Host Status ===== -->
<div class="mini-bar" id="mini-bar">
  <div class="mini-status">
    <span class="mini-dot" id="mini-dot">●</span>
    <span class="mini-host" id="mini-host">HULK-MACMINI</span>
    <span class="mini-ip" id="mini-ip">192.168.31.9</span>
    <span class="mini-ssh" id="mini-ssh">SSH —</span>
    <span class="mini-rtt" id="mini-rtt">RTT —</span>
    <span class="mini-uptime" id="mini-uptime">up —</span>
    <span class="mini-load" id="mini-load">load —</span>
    <span class="mini-users" id="mini-users">users —</span>
    <span class="mini-check" id="mini-check">检查中</span>
  </div>
</div>

<!-- ===== 双向同步对比 (开发机 ↔ mini DB) ===== -->
<div class="sync-panel" id="sync-panel">
  <div class="sync-head">
    <span class="sync-title">🔄 双向同步对比</span>
    <span class="sync-sub" id="sync-sub">开发机 ↔ HULK-MACMINI · 只读对比 · 缓存 30s</span>
    <div class="sync-actions">
      <button class="btn-sync refresh" id="btn-sync-refresh" title="清缓存 + 重新拉 mini DB 数据">🔄 手动刷新</button>
      <button class="btn-sync push" id="btn-sync-push" title="把开发机关键表推送到 mini (DELETE+INSERT)">⬆️ 开发机→mini 手动同步</button>
    </div>
  </div>
  <div class="sync-table" id="sync-body">
    <!-- JS 渲染 -->
  </div>
</div>

</div><!-- /top-bar-row -->

<!-- ===== Charts Row ===== -->
<div class="grid">
  <!-- 饼图: 脑库类目 -->
  <div class="card card-wide">
    <div class="section-head">
      <h2>🥧 脑库类目分布 (TOP 10)</h2>
    </div>
    <div class="chart-box"><canvas id="brainPie"></canvas></div>
  </div>
  
  <!-- 折线图: 演化 + EigenFlux -->
  <div class="card card-wide">
    <div class="section-head">
      <h2>📈 演化 / EigenFlux 活跃趋势</h2>
    </div>
    <div class="chart-box"><canvas id="trendLine"></canvas></div>
  </div>
</div>

<div class="grid" style="margin-top:20px;">
  <!-- 通知 (主, 带新消息 badge) -->
  <div class="card card-wide">
    <div class="section-head">
      <h2>🔔 最近通知</h2>
      <span class="new-badge" id="unread-badge" style="display:none;">0 NEW</span>
    </div>
    <div id="notifications">加载中...</div>
  </div>
  
  <!-- Daemon (主) -->
  <div class="card card-wide">
    <h2>⚙️ Daemon 运行状态</h2>
    <div id="daemons">加载中...</div>
  </div>
  
  <!-- AI 员工搜索 (完整版 + 33,525 人) -->
  <div class="card" style="grid-column: span 2;">
    <div class="section-head" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
      <h2>�️ AI 员工注册中心 <span id="emp-total-tag" style="color:#8b5cf6;font-size:13px;"></span></h2>
      <div style="display:flex;gap:8px;align-items:center;">
        <input type="text" id="emp-search" placeholder="🔍 搜索 name / type / source..." 
               style="background:#0d1117;border:1px solid #2a3a4e;border-radius:6px;padding:6px 12px;color:#e2e8f0;font-size:13px;width:240px;outline:none;" />
        <button id="emp-search-btn" class="btn-sync refresh" style="padding:4px 14px;">搜索</button>
        <select id="emp-limit" style="background:#0d1117;border:1px solid #2a3a4e;border-radius:6px;padding:5px;color:#e2e8f0;font-size:12px;">
          <option value="20">20/页</option>
          <option value="50">50/页</option>
          <option value="100">100/页</option>
        </select>
      </div>
    </div>
    <div id="emp-filters" style="margin-bottom:12px;display:flex;flex-wrap:wrap;gap:6px;"></div>
    <div id="emp-list">加载中...</div>
    <div id="emp-pager" style="margin-top:12px;display:flex;justify-content:center;gap:8px;align-items:center;"></div>
  </div>
  
  <div class="card">
    <h2>🧬 演化日志</h2>
    <div id="evolutions">加载中...</div>
  </div>
  
  <!-- 折叠: 图谱 + EigenFlux + daemon events -->
  <div class="card">
    <h2>� 其他指标</h2>
    <details open>
      <summary>🗂️ 图谱统计</summary>
      <div class="stat-row"><span>节点</span><span class="stat-val" id="graph-nodes">—</span></div>
      <div class="stat-row"><span>关系</span><span class="stat-val" id="graph-rels">—</span></div>
    </details>
    <details>
      <summary>💬 EigenFlux 活跃度</summary>
      <div class="stat-row"><span>近 1h 消息</span><span class="stat-val" id="ef-1h">—</span></div>
      <div class="stat-row"><span>今日演化触发</span><span class="stat-val" id="evo-trigger-count">—</span></div>
    </details>
    <details>
      <summary>📋 Daemon 附加事件</summary>
      <div id="daemon-events"></div>
    </details>
  </div>
</div>

<script>
function fmtNum(n) { if (!n) return '0'; return Number(n).toLocaleString(); }

let brainPieChart = null, trendChart = null;
let seenNotifIds = new Set();  // 追踪哪些通知已显示过
let _connFailCount = 0;        // 连续失败计数

// ===== 连接状态指示器 =====
function setConnState(state, msg) {
    const ind = document.getElementById('conn-indicator');
    const lab = document.getElementById('conn-label');
    if (!ind) return;
    ind.className = 'conn conn-' + state;
    if (msg) lab.textContent = msg;
    else if (state === 'ok') lab.textContent = '已连接';
    else if (state === 'retry') lab.textContent = '重连中...';
    else if (state === 'offline') lab.textContent = '离线 (守护会自动拉起)';
}

// ===== 带重试的 fetch (静默, 不刷屏 console) =====
async function fetchWithRetry(url, opts, maxRetries = 2) {
    let lastErr = null;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const ctrl = new AbortController();
            const timer = setTimeout(() => ctrl.abort(), 3000);
            const r = await fetch(url, {...opts, signal: ctrl.signal});
            clearTimeout(timer);
            _connFailCount = 0;
            setConnState('ok');
            return r;
        } catch (e) {
            lastErr = e;
            if (attempt < maxRetries) {
                setConnState('retry', `重连中 (${attempt+1}/${maxRetries})...`);
                await new Promise(res => setTimeout(res, 400 + attempt * 300));
            }
        }
    }
    _connFailCount++;
    if (_connFailCount >= 3) setConnState('offline');
    // 只在第 1 次和第 3/6/9... 次失败时 log, 不刷屏
    if (_connFailCount === 1 || _connFailCount % 3 === 0) {
        console.warn('[refresh] 后端暂不可达 (已重试 ' + maxRetries + ' 次, 连续失败 ' + _connFailCount + ' 次), 守护会自动拉起');
    }
    return null;
}

// ===== 双向同步对比渲染 =====
function renderSync(sync) {
    const body = document.getElementById('sync-body');
    const sub = document.getElementById('sync-sub');
    if (!sync) { body.innerHTML = '<div class="sync-offline-hint">等待数据...</div>'; return; }
    
    sub.textContent = sync.online 
        ? `开发机 ↔ ${sync.hostname || 'HULK-MACMINI'} · DB=${sync.db_path || '—'} · 检查 ${sync.checked_at || '—'}`
        : `${sync.hostname || 'HULK-MACMINI'} 离线 · 无法对比`;
    
    if (!sync.online || !sync.tables || sync.tables.length === 0) {
        body.innerHTML = `<div class="sync-offline-hint">🔴 ${sync.hostname || 'Mac mini'} 离线, 暂无可比数据</div>`;
        return;
    }
    
    const rows = sync.tables.map(t => {
        const local = t.local, mini = t.mini;
        let diffText = '—', diffClass = 'na';
        if (local != null && mini != null) {
            const d = local - mini;
            const pct = mini > 0 ? Math.round(Math.abs(d) / mini * 100) : 0;
            if (d === 0) { diffText = '≡ 一致'; diffClass = 'equal'; }
            else if (d > 0) { diffText = `+${d.toLocaleString()} (+${pct}%)`; diffClass = 'plus'; }
            else { diffText = `${d.toLocaleString()} (${pct}%)`; diffClass = 'minus'; }
        } else if (local == null && mini != null) {
            diffText = '开发机无'; diffClass = 'na';
        } else if (local != null && mini == null) {
            diffText = 'mini 无'; diffClass = 'na';
        }
        
        const localStr = local != null ? local.toLocaleString() : '—';
        const miniStr = mini != null ? mini.toLocaleString() : (t.mini_error ? '❌ 表不存在' : '—');
        
        // 判断同步建议
        let hint = '';
        if (diffClass === 'plus' && mini != null) hint = '← mini 落后, 考虑推同步';
        else if (diffClass === 'minus') hint = '→ 开发机落后, mini 数据新';
        
        return `<div class="sync-row" title="${t.table}${hint ? ' | ' + hint : ''}">
            <div class="sync-label">${t.label}</div>
            <div class="v-local">${localStr}</div>
            <div class="v-mini">${miniStr}</div>
            <div class="v-diff ${diffClass}">${diffText}</div>
        </div>`;
    }).join('');
    
    body.innerHTML = `
        <div class="sync-header-row">
            <div>数据表</div><div>🖥️ 开发机</div><div>🔮 ${sync.hostname}</div><div>Δ 差异</div>
        </div>
        ${rows}
    `;
}

async function refresh() {
  const r = await fetchWithRetry('/api/data?t=' + Date.now());
  if (!r) return;  // 后端离线, fetchWithRetry 已处理状态 + 重试
  if (!r.ok) { setConnState('retry'); return; }
  try {
    const d = await r.json();
    if (!d.generated_at) return;
    document.getElementById('ts').textContent = '更新 ' + d.generated_at + ' · 2.5s';
    
    // ===== 辅助: 安全设置 DOM (元素不存在就静默跳过) =====
    const safeSet = (id, updater) => {
      const el = document.getElementById(id);
      if (!el) return;  // 可能在切换布局时被移除了
      try { updater(el); } catch (e) { console.warn('safeSet ' + id + ':', e); }
    };
    
    // ===== KPI =====
    const runCount = d.daemons.filter(x => x.status.includes('RUNNING')).length;
    safeSet('kpi-brain', el => el.textContent = fmtNum(d.brain_total));
    safeSet('kpi-brain-sub', el => el.textContent = '今日 +' + fmtNum(d.brain_today));
    safeSet('kpi-daemon', el => el.textContent = runCount + '/' + d.daemons.length);
    safeSet('kpi-daemon-sub', el => {
        stopped = d.daemons.length - runCount
        el.textContent = `${stopped} 个休眠 · 守护自动拉起`;
    });
    safeSet('kpi-evo', el => el.textContent = d.evolutions.length);
    safeSet('kpi-writer', el => el.textContent = d.employee_total.toLocaleString());
    safeSet('kpi-writer-sub', el => {
        if (d.emp_active > 0) {
            el.textContent = d.emp_active.toLocaleString() + ' 活跃 / ' + (d.employee_total - d.emp_active).toLocaleString() + ' 休眠';
        } else {
            el.textContent = d.employee_total.toLocaleString() + ' enabled (待激活)';
        }
    });

    // ===== Mini Host Status =====
    const m = d.mini || {};
    safeSet('mini-dot', el => { el.className = 'mini-dot ' + (m.online ? 'online' : 'offline'); });
    safeSet('mini-host', el => el.textContent = m.name || 'HULK-MACMINI');
    safeSet('mini-ip', el => el.textContent = m.host || '—');
    safeSet('mini-ssh', el => {
        el.textContent = 'SSH ' + (m.ssh_ok ? '✅ OK' : (m.online ? '❌ FAIL' : '—'));
        el.className = 'mini-ssh' + (m.ssh_ok ? '' : (m.online ? ' fail' : ''));
    });
    safeSet('mini-rtt', el => el.textContent = m.online && m.rtt_ms != null ? `RTT ${m.rtt_ms}ms` : 'RTT —');
    safeSet('mini-uptime', el => el.textContent = m.online && m.uptime ? 'up ' + m.uptime : 'up —');
    safeSet('mini-load', el => {
        if (m.online && m.load) {
            const [l1, l5, l15] = m.load;
            el.textContent = `load ${l1} / ${l5} / ${l15}`;
            el.className = 'mini-load' + (l1 > 8 ? ' hot' : l1 > 4 ? ' warn' : '');
        } else { el.textContent = 'load —'; el.className = 'mini-load'; }
    });
    safeSet('mini-users', el => el.textContent = m.online && m.users != null ? `👤 ${m.users}` : 'users —');
    safeSet('mini-check', el => el.textContent = '检查 ' + (m.last_check || '—'));

    // ===== Sync Comparison =====
    renderSync(d.mini_sync);

    // ===== Charts =====
    if (d.brain_cats.length > 0) {
      const colors = ['#3b82f6','#8b5cf6','#22c55e','#eab308','#ef4444','#ec4899','#06b6d4','#f97316','#6366f1','#14b8a6'];
      const labels = d.brain_cats.map(c => c.cat.substring(0,14));
      const data = d.brain_cats.map(c => c.cnt);
      if (brainPieChart) { brainPieChart.data.labels = labels; brainPieChart.data.datasets[0].data = data; brainPieChart.update('none'); }
      else {
        safeSet('brainPie', el => {
            brainPieChart = new Chart(el, {
              type: 'doughnut',
              data: { labels, datasets: [{ data, backgroundColor: colors.slice(0, data.length), borderWidth: 0, hoverOffset: 8 }] },
              options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#64748b', font: { size: 12 }, boxWidth: 12, padding: 10 } } } }
            });
        });
      }
    }
    
    // 演化 + EigenFlux 折线图
    const allHours = Array.from({length:24}, (_,i) => String(i).padStart(2,'0') + ':00');
    const efMap = {}, evoMap = {};
    d.ef_trend.forEach(x => efMap[x.hour] = x.count);
    d.evo_trend.forEach(x => evoMap[x.hour] = x.count);
    if (trendChart) {
      trendChart.data.datasets[0].data = allHours.map(h => efMap[h] || 0);
      trendChart.data.datasets[1].data = allHours.map(h => evoMap[h] || 0);
      trendChart.update('none');
    } else {
      safeSet('trendLine', el => {
          trendChart = new Chart(el, {
            type: 'line',
            data: {
              labels: allHours,
              datasets: [
                { label: 'EigenFlux 消息 (24h)', data: allHours.map(h => efMap[h] || 0), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.4, pointRadius: 2 },
                { label: '演化触发 (10h)', data: allHours.map(h => evoMap[h] || 0), borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)', fill: true, tension: 0.4, pointRadius: 2 },
              ]
            },
            options: {
              responsive: true, maintainAspectRatio: false,
              interaction: { mode: 'index', intersect: false },
              plugins: { legend: { labels: { color: '#64748b', font: { size: 12 } } } },
              scales: {
                x: { ticks: { color: '#64748b', maxTicksLimit: 12 }, grid: { color: 'rgba(255,255,255,0.04)' } },
                y: { ticks: { color: '#64748b', precision: 0 }, grid: { color: 'rgba(255,255,255,0.04)' } }
              }
            }
          });
      });
    }
    
    // ===== Notifications (with NEW slide-in) =====
    const notifIds = d.notifications.map(n => n.ts + n.title);
    const newIds = notifIds.filter(id => !seenNotifIds.has(id));
    notifIds.forEach(id => seenNotifIds.add(id));
    const newCount = newIds.length;
    
    safeSet('unread-badge', el => {
        if (newCount > 0) { el.style.display = 'inline-block'; el.textContent = newCount + ' NEW'; }
        else { el.style.display = 'none'; }
    });
    
    safeSet('notifications', el => {
        el.innerHTML = d.notifications.length === 0 ? 
          '<div style="color:var(--muted);font-size:14px;">暂无通知</div>' :
          d.notifications.map((n, i) => {
            const isNew = i < newCount;
            return `<div class="notify-item ${isNew ? 'notify-new' : ''}">
              <div class="notify-title level-${n.level}">${n.title}${isNew ? ' <span style="color:#ef4444;font-size:12px;margin-left:6px;">● NEW</span>' : ''}</div>
              <div class="notify-content">${n.content}</div>
              <span class="notify-ts">${n.ts}</span>
            </div>`;
          }).join('');
    });
    
    // ===== Daemons =====
    safeSet('daemons', el => {
        el.innerHTML = d.daemons.map(dm => {
            const cls = dm.status.includes('RUNNING') ? 'running' : dm.status.includes('READY') ? 'ready' : dm.status.includes('EVENT') ? 'event' : 'offline';
            const dotCls = dm.status.includes('RUNNING') ? 'green' : dm.status.includes('READY') ? 'yellow' : 'red';
            return `<div class="daemon-row">
                <div class="daemon-left"><span class="pulse ${dotCls}"></span><span class="daemon-name">${dm.name}</span></div>
                <div><span class="status-badge ${cls}">${dm.status}</span> <span style="color:var(--muted);font-size:13px;margin-left:8px;">${dm.hb}</span></div>
            </div>`;
        }).join('');
    });
    
    // ===== Evolutions =====
    safeSet('evolutions', el => {
        el.innerHTML = d.evolutions.length === 0 ? 
          '<div style="color:var(--muted);font-size:14px;">暂无演化</div>' :
          d.evolutions.slice(0, 10).map(e => `
            <div class="stat-row"><span>🧬 ${e.type}</span><span class="stat-val">${e.ts}</span></div>`).join('');
    });
    
    // ===== Secondary =====
    safeSet('graph-nodes', el => el.textContent = fmtNum(d.graph_nodes));
    safeSet('graph-rels', el => el.textContent = fmtNum(d.graph_rels));
    safeSet('ef-1h', el => el.textContent = fmtNum(d.eigenflux_1h));
    safeSet('evo-trigger-count', el => el.textContent = d.evolutions.length);
    safeSet('daemon-events', el => {
        el.innerHTML = d.daemon_events.length === 0 ? 
          '<div style="color:var(--muted);font-size:13px;">暂无</div>' :
          d.daemon_events.map(de => `<div style="margin-bottom:8px;"><div style="font-size:13px;font-weight:600;color:var(--accent);">${de.daemon}</div>
            ${de.events.map(e => `<div style="font-size:13px;padding:2px 0;"><span class="level-${e.level}">${e.title}</span></div>`).join('')}
          </div>`).join('');
    });
    
  } catch (e) {
    // JSON 解析/DOM 异常 — 属于代码 bug, 只 warn 一次避免刷屏
    if (!refresh._warned) { console.warn('[refresh] 数据处理异常:', e); refresh._warned = true; }
  }
}

// ===== 同步面板按钮事件 =====
function showSyncToast(msg, type='working') {
    let toast = document.getElementById('sync-toast');
    if (!toast) {
        toast = document.createElement('span');
        toast.className = 'sync-toast';
        toast.id = 'sync-toast';
        document.querySelector('.sync-actions').prepend(toast);
    }
    toast.className = 'sync-toast ' + type;
    toast.textContent = msg;
    if (type === 'success') setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

document.getElementById('btn-sync-refresh').addEventListener('click', async () => {
    const btn = document.getElementById('btn-sync-refresh');
    btn.disabled = true;
    btn.textContent = '刷新中...';
    showSyncToast('正在重新拉取 mini 数据...', 'working');
    try {
        const r = await fetch('/api/sync/refresh', {method: 'POST'});
        const j = await r.json();
        if (j.ok) {
            renderSync(j.sync);
            showSyncToast('✅ 已刷新', 'success');
        } else {
            showSyncToast('❌ 失败: ' + (j.error || ''), 'error');
        }
    } catch(e) {
        showSyncToast('❌ 网络错误', 'error');
    }
    btn.disabled = false;
    btn.textContent = '🔄 手动刷新';
});

document.getElementById('btn-sync-push').addEventListener('click', async () => {
    const btn = document.getElementById('btn-sync-push');
    btn.disabled = true;
    btn.textContent = '同步中 (DB 双向 upsert + 文件整理)...';
    showSyncToast('正在推送到 mini, 通常 15-30s...', 'working');
    try {
        const r = await fetch('/api/sync/push', {method: 'POST'});
        const j = await r.json();
        btn.disabled = false;
        btn.textContent = '⬆️ 开发机→mini 手动同步';
        if (j.ok) {
            showSyncModal(j);
            refresh();
        } else {
            showSyncToast('❌ ' + (j.error || '未知错误'), 'error');
        }
    } catch(e) {
        btn.disabled = false;
        btn.textContent = '⬆️ 开发机→mini 手动同步';
        showSyncToast('❌ 网络错误: ' + e.message, 'error');
    }
});

// 同步结果 Modal — 展示真实明细
function showSyncModal(j) {
    // 构造 results 表 (拉取 + 推送)
    const rows = (j.results || []).map(line => {
        let cls = 'info';
        if (line.startsWith('⬇️')) cls = 'pull';
        else if (line.startsWith('⬆️') || line.startsWith('OK')) cls = 'push';
        else if (line.startsWith('FILESYS')) cls = 'filesys';
        else if (line.startsWith('  ERR')) cls = 'error';
        return `<div class="modal-row modal-${cls}">${escapeHtml(line)}</div>`;
    }).join('');
    
    const pushDetail = (j.mini_push || '').trim();
    
    const modal = document.createElement('div');
    modal.className = 'sync-modal-backdrop';
    modal.innerHTML = `
        <div class="sync-modal">
            <div class="sync-modal-header">
                <span>✅ 同步完成</span>
                <span class="sync-modal-close" onclick="this.closest('.sync-modal-backdrop').remove()">×</span>
            </div>
            <div class="sync-modal-body">
                <div class="modal-section">
                    <div class="modal-section-title">📋 同步详情 (${(j.results||[]).length} 项)</div>
                    ${rows || '<div class="modal-row modal-info">无详细输出</div>'}
                </div>
                ${pushDetail ? `
                <div class="modal-section">
                    <div class="modal-section-title">🖥️ mini 端实际执行 (stdout)</div>
                    <pre class="modal-stdout">${escapeHtml(pushDetail)}</pre>
                </div>` : ''}
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    // 背景点击关闭
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
}

function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// mini 离线时禁用 push 按钮
function updateSyncButtons(miniOnline) {
    document.getElementById('btn-sync-push').disabled = !miniOnline;
    if (!miniOnline) {
        document.getElementById('btn-sync-push').title = 'Mac mini 离线, 无法同步';
    } else {
        document.getElementById('btn-sync-push').title = '把开发机关键表推送到 mini';
    }
}

// 每次 refresh 后更新按钮状态
const _origRenderSync = renderSync;
renderSync = function(sync) {
    _origRenderSync(sync);
    updateSyncButtons(sync && sync.online);
};

// ===== AI 员工搜索面板 =====
let empPage = 1;
let empQ = '';
let empTypeFilter = '';

async function loadEmployees() {
    const listEl = document.getElementById('emp-list');
    const pagerEl = document.getElementById('emp-pager');
    const filtersEl = document.getElementById('emp-filters');
    const totalTag = document.getElementById('emp-total-tag');
    const limit = parseInt(document.getElementById('emp-limit').value);
    
    listEl.innerHTML = '<div style="color:#7f8c8d;text-align:center;padding:20px;">加载中...</div>';
    
    const params = new URLSearchParams({ q: empQ + (empTypeFilter ? ' ' + empTypeFilter.replace(/.*:/, '') : ''), page: empPage, limit });
    try {
        const r = await fetch('/api/employees?' + params);
        const j = await r.json();
        
        totalTag.textContent = `(${j.total.toLocaleString()} 人, ${j.pages} 页)`;
        
        // 类型筛选 chips
        if (j.types && j.types.length > 0 && !empQ && empPage === 1) {
            filtersEl.innerHTML = '<span style="color:#7f8c8d;font-size:12px;margin-right:6px;">按类型筛选:</span>' +
                j.types.map(t => {
                    const pct = (t.count / j.total * 100).toFixed(1);
                    const active = empTypeFilter === t.type;
                    return `<button class="btn-sync" onclick="empTypeFilter='${t.type === empTypeFilter ? '' : t.type}';empPage=1;loadEmployees();" 
                        style="padding:3px 10px;font-size:11px;background:${active ? '#8b5cf6' : '#1e293b'};color:${active ? '#fff' : '#94a3b8'};border:1px solid ${active ? '#8b5cf6' : '#2a3a4e'};">
                        ${t.type} ${t.count.toLocaleString()} <span style="opacity:.6">(${pct}%)</span>
                    </button>`;
                }).join('');
        } else if (empTypeFilter) {
            filtersEl.innerHTML = `<button class="btn-sync" onclick="empTypeFilter='';empPage=1;loadEmployees();" 
                style="padding:3px 10px;font-size:11px;background:#8b5cf6;color:#fff;border:1px solid #8b5cf6;">🔴 清除类型筛选</button>`;
        } else {
            filtersEl.innerHTML = '';
        }
        
        // 列表
        if (j.rows.length === 0) {
            listEl.innerHTML = '<div style="color:#7f8c8d;text-align:center;padding:30px;">🔍 没找到匹配的 AI 员工</div>';
            pagerEl.innerHTML = '';
            return;
        }
        
        listEl.innerHTML = j.rows.map(e => `
            <div class="emp-card" style="background:#0d1117;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;margin-bottom:8px;display:flex;gap:14px;align-items:center;transition:border-color .15s;"
                onmouseover="this.style.borderColor='#8b5cf640'" onmouseout="this.style.borderColor='#1e293b'">
                <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff;flex-shrink:0;">
                    ${(e.name || '?')[0].toUpperCase()}
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:14px;color:#e2e8f0;">
                        ${e.name}
                        ${e.description ? `<span style="color:#7f8c8d;font-weight:400;font-size:12px;margin-left:8px;">${e.description}</span>` : ''}
                    </div>
                    <div style="font-size:12px;color:#64748b;margin-top:3px;display:flex;gap:12px;flex-wrap:wrap;">
                        <span style="color:#8b5cf6;">#${e.employee_id}</span>
                        <span>📦 ${e.employee_type}</span>
                        <span>🏷️ ${e.employee_source}</span>
                        <span>⭐ level ${e.level}</span>
                        <span>📞 调用 ${e.call_count}</span>
                        ${e.registered_at ? `<span>📅 ${e.registered_at}</span>` : ''}
                        ${e.host_id && e.host_id !== 'dev' ? `<span style="color:#f97316;">🖥️ ${e.host_id}</span>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        // 分页
        if (j.pages > 1) {
            let pagesHtml = '';
            const maxShow = 7;
            let start = Math.max(1, j.page - Math.floor(maxShow/2));
            let end = Math.min(j.pages, start + maxShow - 1);
            start = Math.max(1, end - maxShow + 1);
            
            if (start > 1) pagesHtml += `<button class="btn-sync" style="padding:2px 8px;font-size:11px;" onclick="empPage=1;loadEmployees();">«</button>`;
            for (let p = start; p <= end; p++) {
                pagesHtml += `<button class="btn-sync" style="padding:2px 10px;font-size:11px;${p===j.page?'background:#8b5cf6;color:#fff;border-color:#8b5cf6;':''}" 
                    onclick="empPage=${p};loadEmployees();">${p}</button>`;
            }
            if (end < j.pages) pagesHtml += `<button class="btn-sync" style="padding:2px 8px;font-size:11px;" onclick="empPage=${j.pages};loadEmployees();">»</button>`;
            
            pagerEl.innerHTML = `
                <span style="color:#7f8c8d;font-size:12px;">${j.total.toLocaleString()} 条 · ${j.page}/${j.pages} 页</span>
                ${pagesHtml}
                <button class="btn-sync" style="padding:2px 10px;font-size:11px;" ${j.page<=1?'disabled':''} onclick="empPage=Math.max(1,empPage-1);loadEmployees();">← 上一页</button>
                <button class="btn-sync" style="padding:2px 10px;font-size:11px;" ${j.page>=j.pages?'disabled':''} onclick="empPage=Math.min(${j.pages},empPage+1);loadEmployees();">下一页 →</button>
            `;
        } else {
            pagerEl.innerHTML = `<span style="color:#7f8c8d;font-size:12px;">共 ${j.total.toLocaleString()} 条</span>`;
        }
        
    } catch(e) {
        listEl.innerHTML = `<div style="color:#ef4444;text-align:center;padding:20px;">加载失败: ${e.message}</div>`;
    }
}

// 搜索事件
document.getElementById('emp-search-btn').addEventListener('click', () => {
    empQ = document.getElementById('emp-search').value.trim();
    empPage = 1;
    empTypeFilter = '';
    loadEmployees();
});
document.getElementById('emp-search').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        empQ = e.target.value.trim();
        empPage = 1;
        empTypeFilter = '';
        loadEmployees();
    }
});
document.getElementById('emp-limit').addEventListener('change', () => {
    empPage = 1;
    loadEmployees();
});

// 页面加载时拉一次 (类型聚合)
loadEmployees();

refresh();
setInterval(refresh, 2500);
</script>
</body>
</html>"""

@app.route('/andromeda')
def status_page():
    return render_template_string(STATUS_PAGE)

@app.route('/')
def root():
    return redirect('/andromeda')

def run(host='127.0.0.1', port=8889):
    print(f"🧬 仙女座后台状态页 (仅本地): http://localhost:{port}/andromeda")
    print(f"   数据源: {_DB_PATH}")
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    run()
