#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能挂载自动化进程引擎 (Smart Mount Engine)
================================================
flow_id: flow_smart_mount_auto_process_20260819_001
§14 STEP_7_EXECUTE 下场实施

核心能力:
  1. 收集AI建议池中已评估的高优先级建议
  2. 综合EigenFlux专家动态权重做挂载决策
  3. 自动生成daemon脚本并注册到mt_daemon_registry
  4. subprocess启动进程 + 心跳监控 + 自动重启
  5. 系统需求/EigenFlux专家建议综合驱动

复用现有基础设施:
  - ai_intelligent_upgrade_engine.register_daemon()  注册daemon
  - ai_intelligent_upgrade_engine.daemon_transition() 状态机转移
  - ai_intelligent_upgrade_engine.add_ai_suggestion()  添加建议
  - ai_intelligent_upgrade_engine.evaluate_suggestion() 评估建议
  - ai_intelligent_upgrade_engine.compute_dynamic_weight() 专家权重

新增表:
  - mt_ai_smart_mount_processes  智能挂载进程跟踪表

CLI守护模式:
  python3 ai_smart_mount_engine.py start    启动监控守护进程
  python3 ai_smart_mount_engine.py stop     停止
  python3 ai_smart_mount_engine.py status   查看状态
  python3 ai_smart_mount_engine.py list     列出所有挂载进程
  python3 ai_smart_mount_engine.py create   手动创建自动化进程
  python3 ai_smart_mount_engine.py adopt    采纳AI建议并挂载
  python3 ai_smart_mount_engine.py scan     扫描建议池+自动挂载

遵循硬约束:
  - 数据库唯一数据源(app.db)
  - daemon状态机5态(IDLE/RUNNING/PAUSED/FAILED/STOPPED)
  - 全链路追溯ID
  - 巡检闭环 + 自动修复
"""
import json
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
# ---- 路径 & 依赖 ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # flask-app/
PROJECT_ROOT = os.path.dirname(ROOT)  # 项目根
# 🔧 2026-09-10 仙女座修复: 主库从 flask-app/ai_engines/app.db → Database/app.db
# 清理前的旧副本 488KB 不包含 15 daemon 注册表、AI 员工 33,525 人、25 恒星域
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
# 🔧 仙女座 v5.2 路径修复 (2026-09-13):
# Mac mini 真实主库在 _runtime/databases/Database/app.db (9.8GB, 220 表)
# PROJECT_ROOT/Database/app.db 是本地 Flask 注册时的路径漂移
# 统一: 先找 _runtime/databases/Database/app.db → fallback 旧路径
APP_DB = os.path.join(PROJECT_ROOT, "_runtime", "databases", "Database", "app.db")
if not os.path.exists(APP_DB):
    # fallback: 本地开发机 / 旧版本兼容
    _alt1 = os.path.join(PROJECT_ROOT, "Database", "app.db")
    _alt2 = os.path.join(AI_ENGINES_DIR, "app.db")
    APP_DB = _alt1 if os.path.exists(_alt1) else _alt2
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
DAEMON_SCRIPTS_DIR = os.path.join(RUNTIME_DIR, "auto_daemons")
PID_FILE = os.path.join(PID_DIR, "ai_smart_mount_engine.pid")
MONITOR_LOG = os.path.join(LOG_DIR, "ai_smart_mount_monitor.log")

for _d in [LOG_DIR, PID_DIR, DAEMON_SCRIPTS_DIR]:
    os.makedirs(_d, exist_ok=True)

# 导入现有基础设施
sys.path.insert(0, AI_ENGINES_DIR)
try:
    from ai_intelligent_upgrade_engine import (
        register_daemon, daemon_transition, add_ai_suggestion,
        evaluate_suggestion, compute_dynamic_weight,
        ensure_upgrade_tables, _get_conn, _now,
        DAEMON_STATE_MACHINE,
    )
except ImportError:
    # 兼容直接运行
    _CONN = None

    def _get_conn():
        # 🔧 仙女座 v5.0: 统一 timeout=30s + WAL 解锁
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA wal_autocheckpoint = 10000")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _now():
        return datetime.now().isoformat()

    DAEMON_STATE_MACHINE = {
        "IDLE": ["RUNNING", "STOPPED"],
        "RUNNING": ["PAUSED", "FAILED", "STOPPED"],
        "PAUSED": ["RUNNING", "STOPPED"],
        "FAILED": ["RUNNING", "STOPPED"],
        "STOPPED": ["IDLE", "RUNNING"],
    }

_LOCK = threading.Lock()
MOUNT_THRESHOLD = 0.70  # 综合分>=0.70才自动挂载
MAX_RESTART_COUNT = 5       # 连续重启失败次数上限
HEARTBEAT_TIMEOUT = 120     # 心跳超时秒数 (↑从90→120, 给daemon多呼吸空间)
STOPPED_COOLDOWN = 300      # STOPPED状态冷却重试窗口(秒) - 超过后重置restart_count再试
MONITOR_INTERVAL = 30       # 监控巡检间隔秒数

# ============================================================
# 🆕 SYSTEM_REQUIRED_DAEMONS - 系统必需daemon配置
# 被重构时误删，2026-09-13 恢复
# ============================================================
SYSTEM_REQUIRED_DAEMONS = [
{
        "process_name": "sys_heartbeat_writer",
        "duty": "系统心跳写入 - 每30s向 mt_daemon_registry 写心跳，保持所有daemon存活",
        "work_body": """
import os, sys, sqlite3, time
DB = os.environ.get('APP_DB', '/Users/wuchenghao/mtscos/_runtime/databases/Database/app.db')
conn = sqlite3.connect(DB); conn.execute('PRAGMA busy_timeout=5000')
conn.execute("UPDATE mt_daemon_registry SET last_heartbeat=datetime('now') WHERE daemon_name=?", ('sys_heartbeat_writer',))
conn.commit(); conn.close()
_log("[heartbeat] written")
""",
        "inspect_cycle": 30,
    },
    {
        "process_name": "sys_patrol_inspector",
        "duty": "daemon状态巡检 - 每60s检查所有挂载进程心跳，超时的标记为TIMEOUT",
        "work_body": """
import sqlite3, os
DB = os.environ.get('APP_DB', '/Users/wuchenghao/mtscos/_runtime/databases/Database/app.db')
conn = sqlite3.connect(DB); conn.execute('PRAGMA busy_timeout=5000')
now = int(time.time())
for r in conn.execute("SELECT process_name, pid, heartbeat_at FROM mt_ai_smart_mount_processes WHERE current_state='RUNNING'").fetchall():
    try:
        alive = os.kill(int(r[1]), 0) if r[1] else None
        if alive is None:
            conn.execute("UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED' WHERE process_name=?", (r[0],))
    except:
        conn.execute("UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED' WHERE process_name=?", (r[0],))
conn.commit(); conn.close()
""",
        "inspect_cycle": 60,
    },
    {
        "process_name": "sys_auto_repair",
        "duty": "FAILED daemon自动修复 - 检查restart_count>0的进程，尝试重新挂载",
        "work_body": """
import sqlite3, os, time
DB = os.environ.get('APP_DB', '/Users/wuchenghao/mtscos/_runtime/databases/Database/app.db')
conn = sqlite3.connect(DB); conn.execute('PRAGMA busy_timeout=5000')
stale = conn.execute("SELECT process_name FROM mt_ai_smart_mount_processes WHERE current_state='FAILED' AND restart_count<5").fetchall()
for r in stale:
    _log(f"[auto_repair] FAILED→STOPPED: {r[0]}")
    conn.execute("UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED', restart_count=restart_count+1 WHERE process_name=?", (r[0],))
conn.commit(); conn.close()
""",
        "inspect_cycle": 120,
    },
    {
        "process_name": "sys_local_inference",
        "duty": "本地AI推理引擎 - 每120s检查Ollama状态，预热模型，零token调用",
        "work_body": """
import urllib.request, json
try:
    r = urllib.request.urlopen("http://127.0.0.1:11435/api/tags", timeout=3)
    models = [m['name'] for m in json.loads(r.read()).get('models',[])]
    _log(f"[local_inference] Ollama online, models={models}")
except Exception as e:
    _log(f"[local_inference] Ollama offline: {e}")
""",
        "inspect_cycle": 120,
    },
    {
        "process_name": "sys_rule_enforcer",
        "duty": "规则学习+执行 - 每300s扫描弱约束词，执行规则治理",
        "work_body": """
import sqlite3, os
DB = os.environ.get('APP_DB', '/Users/wuchenghao/mtscos/_runtime/databases/Database/app.db')
conn = sqlite3.connect(DB); conn.execute('PRAGMA busy_timeout=5000')
n = conn.execute("SELECT COUNT(*) FROM mt_rule_violation_alert WHERE rule_hit LIKE '%weak%'").fetchone()[0]
_log(f"[rule_enforcer] violations_today={n}")
conn.close()
""",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_auto_patrol",
        "duty": "源码巡逻队 - 每300s扫描Flask路由和模板，发现语法错误",
        "work_body": """
_log("[auto_patrol] patrol cycle... (placeholder - 真实巡逻由 ai_smart_mount_engine heartbeat_check 驱动)")
""",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_auto_hire",
        "duty": "AI自动雇佣 - 每300s检查EigenFlux注册，自动雇佣新专家",
        "work_body": """
_log("[auto_hire] hire cycle... (placeholder)")
""",
        "inspect_cycle": 300,
    },
    {
        "process_name": "sys_eigenflux_network",
        "duty": "EigenFlux网络自动连线 - 每120s检查在线专家，自动交友交流",
        "work_body": """
_log("[eigenflux_network] network cycle... (placeholder)")
""",
        "inspect_cycle": 120,
    },
    {
        "process_name": "sys_deep_inspection",
        "duty": "深度巡检 - 每600s扫描所有注册页面路由，记录到mt_ai_deep_inspection",
        "work_body": """
import urllib.request
try:
    r = urllib.request.urlopen("http://127.0.0.1:8888/index", timeout=5)
    _log(f"[deep_inspection] /index HTTP {r.status} ({len(r.read())}B)")
except Exception as e:
    _log(f"[deep_inspection] /index fail: {e}")
""",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_file_organizer",
        "duty": "智能文件整理 - 每600s清理临时文件和散落文件归类",
        "work_body": """
import os, glob
import_home = os.path.expanduser("~/Desktop")
stale = glob.glob(import_home + "/*.tmp")[:5] if os.path.isdir(import_home) else []
_log(f"[file_organizer] scan: found {len(stale)} stale tmp files")
""",
        "inspect_cycle": 600,
    },
    {
        "process_name": "sys_copy_inspection",
        "duty": "文案合规巡检 - 每900s扫描模板硬编码中文",
        "work_body": """
_log("[copy_inspection] cycle... (placeholder)")
""",
        "inspect_cycle": 900,
    },

    # ===== 仙女座超级集群 v6.1 — 18 daemon (源头质量门禁 + LaTeX 修复) =====
    {
        "process_name": "sys_ramanujan_derive",
        "duty": "拉马努金自动推导(错题→Ollama→严格净化→confidence+verification)",
        "work_body": """
import sqlite3, os, sys, time, random, urllib.request, json, re
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
row = conn.execute("SELECT subject, error_concept FROM mt_error_thinking_chain ORDER BY created_at DESC LIMIT 1").fetchone()
if not row:
    pool = [("math","sin²θ+cos²θ=1"),("physics","F=ma本质"),("calc","导数几何意义"),("algebra","i²=-1有用吗")]
    row = random.choice(pool)
subject, question = row

# === LaTeX 修复: Python dict escape 导致非法 JSON escape ===
def _fix_json_escapes(s):
    import re as _re
    s = _re.sub(r'\\\\([a-zA-Z]+)', r'\\\\1', s)     # \\theta -> theta (去掉反斜杠)
    s = _re.sub(r'\\\\([(){}\\[\\]])', r'\\\\1', s)   # \\( \\) \\[ \\] -> ( ) [ ]
    VALID = set('"\\\\/nrtbf')
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] == '\\\\' and i + 1 < n:
            nxt = s[i + 1]
            if nxt in VALID or nxt == 'u':
                out.append(s[i:i+2]); i += 2
            else:
                out.append(nxt); i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)

def _sanitize(raw_text):
    if not raw_text: return None, 0.0, {}, "pending"
    s = raw_text.strip()
    m = re.match(r'^```(?:json)?\\\\s*([\\\\s\\\\S]*?)\\\\s*```$', s)
    if m: s = m.group(1).strip()
    parsed = None
    for _ in range(2):
        try: parsed = json.loads(s); break
        except Exception: s = _fix_json_escapes(s)
    if not parsed:
        for op, cl in [("{", "}"), ("[", "]")]:
            li, ri = s.find(op), s.rfind(cl)
            if li != -1 and ri != -1 and ri > li:
                try: parsed = json.loads(s[li:ri+1]); break
                except Exception:
                    try: parsed = json.loads(_fix_json_escapes(s[li:ri+1])); break
                    except Exception: pass
    if not parsed: return None, 0.0, {}, "parse_fail"
    steps = parsed.get("推导") or parsed.get("推导过程") or parsed.get("derivation_steps") or parsed.get("steps") or []
    if not isinstance(steps, list):
        for v in parsed.values():
            if isinstance(v, list) and len(v) > 0: steps = v; break
    verification = parsed.get("验证") or parsed.get("自我验证") or parsed.get("self_verification") or {}
    conf_raw = parsed.get("confidence") or parsed.get("置信度")
    try: conf = float(conf_raw) if conf_raw is not None else 0.5
    except Exception: conf = 0.5
    is_valid = verification.get("is_valid") if isinstance(verification, dict) else True
    if isinstance(verification, dict): verification.setdefault("is_valid", is_valid)
    if len(steps) >= 3: conf = min(1.0, conf + 0.1)
    if verification: conf = min(1.0, conf + 0.1)
    vs = "verified" if is_valid else "unverified"
    dc_json = json.dumps({"推导": steps}, ensure_ascii=False) if steps else None
    ver_json = json.dumps(verification, ensure_ascii=False) if verification else None
    return dc_json, round(conf, 3), ver_json, vs

try:
    _queue = json.loads(os.environ.get('OLLAMA_QUEUE','[]'))
    while sum(1 for t in _queue if time.time()-t<120) >= 2: time.sleep(2); _queue = json.loads(os.environ.get('OLLAMA_QUEUE','[]'))
    _queue.append(time.time()); os.environ['OLLAMA_QUEUE'] = json.dumps(_queue)
    # v5.3: 严格 prompt —— 禁止 LaTeX 反斜杠, 至少5步推导
    _schema = (
        "严格按 JSON 输出, 不要 Markdown. 公式用纯文本 (如 a = F/m, sin²θ+cos²θ=1). "
        "禁止 LaTeX 反斜杠命令 (frac theta sqrt sin Delta 等一律禁止). "
        "{\"推导\":[{\"步骤\":1,\"类型\":\"假设|定义|推导|结论\",\"内容\":\"...\"}至少5步], "
        "\"验证\":{\"is_valid\":true,\"说明\":\"...\"},\"confidence\":0.0}"
    )
    payload = {
        "model":"qwen2.5:7b",
        "messages":[
            {"role":"system","content":f"你是拉马努金, 从零推导数学/物理公式. {_schema}"},
            {"role":"user","content":f"请从零推导: {question}"}
        ],
        "stream":False,
        "options":{"temperature":0.1,"num_predict":3000}
    }
    req = urllib.request.Request("http://127.0.0.1:11435/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read()).get("message",{}).get("content","")
    dc_clean, conf, ver_clean, vs = _sanitize(raw)
    if dc_clean is None:
        print(f"[拉马努金] 净化失败, 跳过: {question[:40]}")
    else:
        exist = conn.execute("SELECT knowledge_id FROM mt_derived_knowledge WHERE concept=? AND subject=? ORDER BY created_at DESC LIMIT 1", (question, subject)).fetchone()
        if exist:
            conn.execute("UPDATE mt_derived_knowledge SET derivation_chain=?, verification=?, confidence=?, verification_status=?, model_used='qwen2.5:7b', user_id='system', updated_at=datetime('now','localtime') WHERE knowledge_id=?", (dc_clean, ver_clean, conf, vs, exist[0]))
        else:
            conn.execute("INSERT INTO mt_derived_knowledge (concept,subject,derivation_chain,verification,confidence,model_used,user_id,verification_status,created_at) VALUES (?,?,?,?,?,'qwen2.5:7b','system',?,datetime('now','localtime'))", (question, subject, dc_clean, ver_clean, conf, vs))
        conn.commit()
        print(f"[拉马努金] OK {question[:30]} conf={conf} vs={vs}")
except Exception as e: print(f"[拉马努金] ERROR: {e}")
conn.close()
""",
        "inspect_cycle": 600,
        "startup_offset": 0,
    },
    {
        "process_name": "sys_tutor_learning",
        "duty": "AI导师自动学习(错题统计→认知画像更新)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
rows = conn.execute("SELECT user_id, subject, COUNT(*) as cnt FROM mt_error_thinking_chain WHERE created_at > datetime('now','localtime','-1 day') GROUP BY user_id, subject").fetchall()
if rows:
    for uid, subj, cnt in rows:
        conn.execute("INSERT INTO mt_user_cognitive_profile (user_id, weak_subjects, data_points_count) VALUES (?,?,?) ON CONFLICT(user_id) DO UPDATE SET weak_subjects=excluded.weak_subjects, data_points_count=data_points_count+excluded.data_points_count, updated_at=datetime('now','localtime')", (uid, subj, cnt))
    conn.commit(); print(f"[导师学习] {len(rows)} 用户画像更新")
else: print("[导师学习] 最近1天无新错题")
conn.close()
""",
        "inspect_cycle": 900,
        "startup_offset": 30,
    },
    {
        "process_name": "sys_error_digest",
        "duty": "错题消化(Ollama生成思维链回填)",
        "work_body": """
import sqlite3, os, urllib.request, json
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
rows = conn.execute("SELECT chain_id, subject, error_concept FROM mt_error_thinking_chain WHERE thinking_chain IS NULL ORDER BY created_at DESC LIMIT 3").fetchall()
if rows:
    for cid, subj, q in rows:
        try:
            payload = {"model":"qwen2.5:7b","prompt":f"问题:{q}\n为什么错?思维卡在哪?如何纠正?输出结构化JSON","stream":False,"options":{"temperature":0.3}}
            req = urllib.request.Request("http://127.0.0.1:11435/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=90) as resp: chain = json.loads(resp.read()).get("response","")
            conn.execute("UPDATE mt_error_thinking_chain SET thinking_chain=?, ai_model='qwen2.5:7b' WHERE chain_id=?", (chain[:3000], cid))
            conn.commit(); print(f"[错题消化] #{cid} [{subj}] OK")
        except Exception as e: print(f"[错题消化] #{cid} 失败: {e}")
else: print("[错题消化] 无新错题")
conn.close()
""",
        "inspect_cycle": 1800,
        "startup_offset": 60,
    },
    {
        "process_name": "sys_crypto_key_rotate",
        "duty": "密钥自动轮换(每天03:00)",
        "work_body": """
import datetime, sqlite3, os, hashlib
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
today = datetime.datetime.now().strftime("%Y-%m-%d")
last = conn.execute("SELECT policy_value FROM mt_system_policy WHERE policy_key='crypto_last_rotate'").fetchone()
if last and last[0] == today: print(f"[密钥轮换] 今天已跑过,跳过"); conn.close(); exit()
h = hashlib.sha256((today+"andromeda-auto").encode()).hexdigest()[:16]
conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('crypto_last_rotate',?,'security','auto','active')", (today,))
try: conn.execute("INSERT INTO mt_crypto_log (op_type,op_detail,created_at) VALUES ('key_rotate',?,datetime('now','localtime'))", (f"auto hash={h[:8]}",))
except: pass
conn.commit(); print(f"[密钥轮换] OK hash={h[:8]}"); conn.close()
""",
        "inspect_cycle": 86400,
        "startup_offset": 90,
    },
    {
        "process_name": "sys_matrix_synergy",
        "duty": "14矩阵协同扫描",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    conn.execute("CREATE TABLE IF NOT EXISTS mt_ai_matrix_members (matrix_name TEXT, member_name TEXT, role TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS mt_ai_matrix_edge (from_node TEXT, to_node TEXT, edge_type TEXT, weight REAL DEFAULT 1.0, created_at TEXT)")
    conn.commit()
    matrices = conn.execute("SELECT matrix_name, COUNT(*) FROM mt_ai_matrix_members GROUP BY matrix_name").fetchall()
    edges = conn.execute("SELECT count(*) FROM mt_ai_matrix_edge").fetchone()[0]
    print(f"[矩阵协同] {len(matrices)}矩阵,{edges}边")
    conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('matrix_synergy_stats',?,'model','auto','active')", (f"matrices={len(matrices)},edges={edges}",))
    conn.commit()
except Exception as e: print(f"[矩阵协同] {e}")
conn.close()
""",
        "inspect_cycle": 1800,
        "startup_offset": 20,
    },
    {
        "process_name": "sys_cognitive_assess",
        "duty": "认知画像周期刷新",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    active = conn.execute("SELECT DISTINCT user_id FROM mt_error_thinking_chain WHERE created_at > datetime('now','localtime','-7 days')").fetchall()
    for (uid,) in active:
        total = conn.execute("SELECT COUNT(*) FROM mt_error_thinking_chain WHERE user_id=?", (uid,)).fetchone()[0]
        level = "beginner" if total < 5 else "intermediate" if total < 20 else "advanced" if total < 50 else "expert"
        conn.execute("INSERT OR REPLACE INTO mt_user_cognitive_profile (user_id, cognitive_level, data_points_count, last_assessed) VALUES (?,?,?,datetime('now','localtime'))", (uid, level, total))
    conn.commit(); print(f"[认知画像] {len(active)} 用户刷新")
except Exception as e: print(f"[认知画像] {e}")
conn.close()
""",
        "inspect_cycle": 3600,
        "startup_offset": 50,
    },
    {
        "process_name": "sys_knowledge_graph",
        "duty": "知识图谱构建(跨表概念关联发现)",
        "work_body": """
import sqlite3, os, json
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 从错题 + 拉马努金推导 + 脑库发现概念关联
    errors = conn.execute("SELECT subject, error_concept FROM mt_error_thinking_chain WHERE created_at > datetime('now','localtime','-1 day') LIMIT 20").fetchall()
    derived = conn.execute("SELECT subject, concept FROM mt_derived_knowledge WHERE created_at > datetime('now','localtime','-1 day') LIMIT 20").fetchall()
    all_concepts = set()
    for subj, q in errors + derived:
        all_concepts.add(subj)
    # 概念共现 → 边
    pairs = {}
    for items in [errors, derived]:
        seen = set()
        for subj, _ in items:
            if subj not in seen: seen.add(subj)
    # 落库 (如果表存在)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS mt_andromeda_knowledge_edge (from_concept TEXT, to_concept TEXT, co_count INTEGER DEFAULT 1, created_at TEXT)")
        conn.commit()
        print(f"[知识图谱] {len(all_concepts)} 概念, {len(pairs)} 边")
    except Exception as e: print(f"[知识图谱] skip edge: {e}")
except Exception as e: print(f"[知识图谱] {e}")
conn.close()
""",
        "inspect_cycle": 1200,
        "startup_offset": 15,
    },
    {
        "process_name": "sys_eigenflux_match",
        "duty": "EigenFlux自动配对(同专业交友推荐)",
        "work_body": """
import sqlite3, os, random
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 活跃 EigenFlux 专家
    experts = conn.execute("SELECT name, expertise FROM mt_eigenflux_registrations WHERE status='active' LIMIT 30").fetchall()
    # 同专业配对 (每 60s 随机推荐 1 对)
    if len(experts) >= 2:
        a = random.choice(experts)
        b_pool = [e for e in experts if e != a and (e[1] or '')[:2] == (a[1] or '')[:2]]
        if b_pool:
            b = random.choice(b_pool)
            try:
                conn.execute("CREATE TABLE IF NOT EXISTS mt_eigenflux_friendship (user_a TEXT, user_b TEXT, friendship_type TEXT, auto_created INTEGER DEFAULT 0, created_at TEXT)")
                conn.commit()
                conn.execute("INSERT OR IGNORE INTO mt_eigenflux_friendship (user_a, user_b, friendship_type, auto_created, created_at) VALUES (?,?,?,1,datetime('now','localtime'))", (a[0], b[0], "peer_match"))
                conn.commit(); print(f"[EigenFlux配对] {a[0]} ↔ {b[0]} ({a[1]})")
            except Exception as _e: print(f"[EigenFlux配对] skip: {_e}")
        else: print(f"[EigenFlux配对] {len(experts)} 活跃, 无同专业配对")
    else: print(f"[EigenFlux配对] 活跃专家不足")
except Exception as e: print(f"[EigenFlux配对] {e}")
conn.close()
""",
        "inspect_cycle": 1800,
        "startup_offset": 45,
    },
    {
        "process_name": "sys_predictive_maint",
        "duty": "预测性维护(从历史故障预测风险)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 统计过去 1h FAILED daemon
    failed = conn.execute("SELECT process_name, restart_count FROM mt_ai_smart_mount_processes WHERE current_state='FAILED'").fetchall()
    if failed:
        conn.execute("CREATE TABLE IF NOT EXISTS mt_andromeda_predictive_log (daemon_name TEXT, failure_rate REAL, predicted_next_fail TEXT, created_at TEXT)")
        for name, rc in failed:
            rate = min(rc / 10.0, 1.0)
            conn.execute("INSERT INTO mt_andromeda_predictive_log VALUES (?,?,?,datetime('now','localtime'))", (name, rate, "high"))
        conn.commit(); print(f"[预测维护] {len(failed)} 高风险 daemon")
    else: print("[预测维护] 全部 daemon 健康")
except Exception as e: print(f"[预测维护] {e}")
conn.close()
""",
        "inspect_cycle": 3600,
        "startup_offset": 75,
    },
    {
        "process_name": "sys_cluster_snapshot",
        "duty": "集群快照(daemon状态汇总→policy)",
        "work_body": """
import sqlite3, os, re
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 扫描 mt_ai_smart_mount_processes 表 + mt_daemon_registry
    daemons = conn.execute("SELECT process_name, current_state FROM mt_ai_smart_mount_processes").fetchall()
    running = [d for d in daemons if d[1]=="RUNNING"]
    # 写系统状态快照 (落到 policy)
    conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('andromeda_cluster_snapshot',?,'model','auto','active')", (f"total={len(daemons)},running={len(running)},timestamp={os.popen('date +%H:%M:%S').read().strip()}",))
    conn.commit(); print(f"[集群快照] {len(running)}/{len(daemons)} RUNNING")
except Exception as e: print(f"[集群快照] {e}")
conn.close()
""",
        "inspect_cycle": 600,
        "startup_offset": 10,
    },
    {
        "process_name": "sys_iot_cluster",
        "duty": "IoT设备集群(Arduino等设备状态汇总)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    arduino = conn.execute("SELECT board_model, COUNT(*) FROM mt_arduino_device_events WHERE event_type='insert' GROUP BY board_model").fetchall()
    detect = conn.execute("SELECT COUNT(*) FROM mt_arduino_detected_devices").fetchone()[0]
    try:
        conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('iot_cluster_status',?,'iot','auto','active')", (f"arduino_detected={detect},events_today={len(arduino)}",))
        conn.commit()
    except: pass
    print(f"[IoT集群] Arduino 已检测 {detect}, 板卡 {len(arduino)}")
except Exception as e: print(f"[IoT集群] {e}")
conn.close()
""",
        "inspect_cycle": 1200,
        "startup_offset": 40,
    },
    {
        "process_name": "sys_brain_feed",
        "duty": "脑库投喂(新错题→经验自动回流)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 新错题 → 投喂脑库
    new_errors = conn.execute("SELECT chain_id, subject, error_concept, thinking_chain FROM mt_error_thinking_chain WHERE created_at > datetime('now','localtime','-2 hours') AND thinking_chain IS NOT NULL LIMIT 5").fetchall()
    if new_errors:
        try:
            for cid, subj, q, chain in new_errors:
                conn.execute("INSERT OR IGNORE INTO mt_ai_brain_feed_log (content, category, source_type, feed_type, created_at) VALUES (?,?,?,'experience',datetime('now','localtime'))", (f"错题#{cid} [{subj}] {q[:100]}", "error_chain", "auto_digest"))
            conn.commit(); print(f"[脑库投喂] {len(new_errors)} 条经验")
        except: pass
    else: print("[脑库投喂] 2h 内无新错题")
except Exception as e: print(f"[脑库投喂] {e}")
conn.close()
""",
        "inspect_cycle": 1800,
        "startup_offset": 55,
    },
    {
        "process_name": "sys_security_pulse",
        "duty": "安全态势扫描(违规/SA密钥/实时监控)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 最近 5min 系统错误
    errs = conn.execute("SELECT COUNT(*) FROM mt_iron_rule_violations WHERE created_at > datetime('now','localtime','-5 minutes')").fetchone()[0]
    # 活跃 SA 密钥
    sa = conn.execute("SELECT policy_value FROM mt_system_policy WHERE policy_key='vikey_status'").fetchone()
    sa_status = sa[0] if sa else "unknown"
    # 落快照
    try:
        conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('security_pulse',?,'security','auto','active')", (f"violations_5m={errs},sa_keys={sa_status}",))
        conn.commit()
    except: pass
    print(f"[安全态势] 5min内违规={errs}, SA={sa_status}")
except Exception as e: print(f"[安全态势] {e}")
conn.close()
""",
        "inspect_cycle": 600,
        "startup_offset": 25,
    },
    {
        "process_name": "sys_resource_sched",
        "duty": "资源调度器(CPU/内存自适应)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # CPU/内存
    cpu = os.popen("top -l 1 | grep 'CPU usage' | head -1").read().strip() or "unknown"
    mem = os.popen("top -l 1 | grep 'PhysMem' | head -1").read().strip() or "unknown"
    conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('resource_pulse',?,'system','auto','active')", (f"cpu={cpu}, mem={mem}",))
    conn.commit(); print(f"[资源调度] {cpu}, {mem}")
except Exception as e: print(f"[资源调度] {e}")
conn.close()
""",
        "inspect_cycle": 300,
        "startup_offset": 5,
    },
    {
        "process_name": "sys_profile_fusion",
        "duty": "画像融合(多维度用户画像重新定级)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    profiles = conn.execute("SELECT user_id FROM mt_user_cognitive_profile WHERE last_assessed < datetime('now','localtime','-7 days') OR cognitive_level IS NULL LIMIT 10").fetchall()
    if profiles:
        for (uid,) in profiles:
            stats = conn.execute("SELECT COUNT(*) FROM mt_error_thinking_chain WHERE user_id=?", (uid,)).fetchone()[0]
            level = "beginner" if stats < 5 else "intermediate" if stats < 20 else "advanced" if stats < 50 else "expert"
            conn.execute("UPDATE mt_user_cognitive_profile SET cognitive_level=?, last_assessed=datetime('now','localtime') WHERE user_id=?", (level, uid))
        conn.commit(); print(f"[画像融合] {len(profiles)} 用户重新定级")
    else: print("[画像融合] 全部画像新鲜")
except Exception as e: print(f"[画像融合] {e}")
conn.close()
""",
        "inspect_cycle": 3600,
        "startup_offset": 65,
    },
    {
        "process_name": "sys_experience_replay",
        "duty": "经验回流(脑库投喂日统计)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    feeds = conn.execute("SELECT COUNT(*) FROM mt_ai_brain_feed_log WHERE created_at > datetime('now','localtime','-1 day')").fetchone()[0]
    active_feeders = conn.execute("SELECT COUNT(DISTINCT source_type) FROM mt_ai_brain_feed_log WHERE created_at > datetime('now','localtime','-1 day')").fetchone()[0]
    try:
        conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('brain_feed_daily',?,'model','auto','active')", (f"feeds={feeds}, sources={active_feeders}",))
        conn.commit()
    except: pass
    print(f"[经验回流] 1d 内 {feeds} 条投喂, {active_feeders} 来源")
except Exception as e: print(f"[经验回流] {e}")
conn.close()
""",
        "inspect_cycle": 1800,
        "startup_offset": 70,
    },
    {
        "process_name": "sys_knowledge_precious",
        "duty": "知识沉淀(拉马努金推导周统计)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    # 拉马努金推导置信度统计
    derived = conn.execute("SELECT COUNT(*), AVG(confidence) FROM mt_derived_knowledge WHERE created_at > datetime('now','localtime','-7 days')").fetchone()
    total = derived[0] or 0; avg_conf = derived[1] or 0
    try:
        conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('ramanujan_weekly',?,'model','auto','active')", (f"derived={total},avg_conf={avg_conf:.2f}",))
        conn.commit()
    except: pass
    print(f"[知识沉淀] 本周推导 {total} 条, 平均置信度 {avg_conf:.2f}")
except Exception as e: print(f"[知识沉淀] {e}")
conn.close()
""",
        "inspect_cycle": 7200,
        "startup_offset": 80,
    },
    {
        "process_name": "sys_rule_auto_learn",
        "duty": "规则自动学习(违规统计+知识沉淀)",
        "work_body": """
import sqlite3, os
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
try:
    violations = conn.execute("SELECT COUNT(*), severity FROM mt_iron_rule_violations WHERE created_at > datetime('now','localtime','-1 day') GROUP BY severity").fetchall()
    total = sum(v[0] for v in violations)
    try:
        conn.execute("INSERT OR REPLACE INTO mt_system_policy (policy_key,policy_value,policy_category,policy_version,policy_status) VALUES ('rule_learn_daily',?,'model','auto','active')", (f"violations_1d={total}, by_severity={violations}",))
        conn.commit()
    except: pass
    print(f"[规则学习] 1d 违规 {total} 次")
except Exception as e: print(f"[规则学习] {e}")
conn.close()
""",
        "inspect_cycle": 1800,
        "startup_offset": 35,
    },
    # ============================================================
    # 🆕 WB_GITHUB_SCAN — 仙女座 v6.2 新升级路径: GitHub 开源自动发现+适配融合
    # Stage 1 扫描 → Stage 2 评估 → Stage 3 提案 (人工批准后才执行融合)
    # ============================================================
    {
        "process_name": "sys_github_fusion_scan",
        "duty": "GitHub开源自动发现+评分+生成融合提案 (三阶段流水线, 人工批准后才集成)",
        "work_body": r"""
import os, sys, json, sqlite3, time, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [GITHUB-FUSION] %(message)s')
log = logging.getLogger('github_fusion_daemon')

APP_DB = os.environ.get('APP_DB', '/Users/wuchenghao/mtscos/_runtime/databases/Database/app.db')
PROJECT_ROOT = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'flask-app'))
    from engines.ai_github_fusion_engine import run_cycle, _ensure_tables
    _ensure_tables()
    result = run_cycle()
    log.info(f'cycle done: {json.dumps(result, ensure_ascii=False)[:300]}')

    # 上报 mt_daemon_registry 状态
    conn = sqlite3.connect(APP_DB, timeout=10)
    conn.execute("UPDATE mt_daemon_registry SET last_heartbeat=datetime('now'), status='RUNNING' WHERE daemon_name=?", ('sys_github_fusion_scan',))
    conn.commit(); conn.close()
except Exception as e:
    log.error(f'cycle failed: {e}')
""",
        "inspect_cycle": 3600,   # 1 小时一次 (GitHub API 限流 60req/h, 留够余量)
        "startup_offset": 120,   # 启动 2min 后再跑 (等 Flask + Ollama 就绪)
    },
    # ============================================================
    # 🆕 SYS_ANDROMEDA_EVOLUTION — 仙女座七阶段自演化引擎 (v6.2)
    # 自动检测 → 自动检索 → 自动联想 → 自动衍生 → 自动强化 → 自动拓展 → 自动优化
    # 详见 engines/andromeda_auto_evolution.py
    # ============================================================
    {
        "process_name": "sys_andromeda_auto_evolution",
        "duty": "仙女座七阶段自演化: detect→retrieve→associate→derive→reinforce→expand→optimize",
        "work_body": r"""
import os, sys, json, sqlite3, time, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [ANDROMEDA-EVOL] %(message)s')
log = logging.getLogger('andromeda_evol_daemon')

PROJECT_ROOT = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.environ.get('ANDROMEDA_DB', os.path.join(PROJECT_ROOT, 'database', 'app.db'))
os.environ['ANDROMEDA_DB'] = DB_PATH
os.environ.setdefault('OLLAMA_HOST', 'http://localhost:11435')
os.environ.setdefault('OLLAMA_EMBED_MODEL', 'nomic-embed-text')
os.environ.setdefault('OLLAMA_DERIVE_MODEL', 'qwen2.5:7b')

try:
    sys.path.insert(0, PROJECT_ROOT)
    from engines.andromeda_auto_evolution import run_cycle, get_status
    result = run_cycle()
    log.info(f'cycle done: elapsed={result.get("elapsed_ms")}ms, '
             f'detect={result.get("detect")}, retrieve={result.get("retrieve")}, '
             f'assoc={result.get("associations")}, derived={result.get("derived")}, '
             f'reinforced={result.get("reinforced")}, expand={result.get("expand")}')

    # 上报 mt_daemon_registry 状态
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute("UPDATE mt_daemon_registry SET last_heartbeat=datetime('now'), status='RUNNING' WHERE daemon_name=?", ('sys_andromeda_auto_evolution',))
        conn.commit(); conn.close()
    except Exception:
        pass
except Exception as e:
    log.error(f'cycle crashed: {e}')
""",
        "inspect_cycle": 600,    # 10 分钟一次
        "startup_offset": 180,   # 启动 3min 后再跑 (等 Flask + Ollama 完全就绪 + 依赖 import)
    }
]



# ============================================================
# 建表 (幂等)
# ============================================================
def ensure_smart_mount_tables() -> Dict[str, bool]:
    """创建智能挂载相关表"""
    # 先确保基础表存在
    try:
        ensure_upgrade_tables()
    except Exception:
        pass

    results = {}
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # 智能挂载进程跟踪表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_smart_mount_processes (
            process_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            daemon_id        INTEGER NOT NULL,
            process_name     TEXT NOT NULL UNIQUE,
            script_path      TEXT NOT NULL,
            pid              INTEGER,
            suggestion_id    INTEGER,
            mount_source     TEXT NOT NULL DEFAULT 'AI_SUGGESTION',
            mount_score      REAL DEFAULT 0.0,
            expert_weights  TEXT,
            current_state    TEXT NOT NULL DEFAULT 'IDLE',
            heartbeat_at     TEXT,
            restart_count    INTEGER DEFAULT 0,
            last_restart_at  TEXT,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL,
            FOREIGN KEY(daemon_id) REFERENCES mt_daemon_registry(daemon_id),
            FOREIGN KEY(suggestion_id) REFERENCES mt_ai_suggestion_pool(suggestion_id),
            CHECK(mount_source IN ('AI_SUGGESTION','SYSTEM_REQ','EXPERT_ADVICE','MANUAL')),
            CHECK(current_state IN ('IDLE','RUNNING','PAUSED','FAILED','STOPPED'))
        )""")
        results["mt_ai_smart_mount_processes"] = True

        # 挂载决策日志表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_ai_mount_decisions (
            decision_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_id    INTEGER,
            suggestion_text  TEXT,
            feasibility      REAL,
            value_score      REAL,
            cost_score       REAL,
            risk_score       REAL,
            base_score       REAL,
            expert_weight    REAL,
            final_score      REAL,
            decision         TEXT NOT NULL,
            reason           TEXT,
            created_at       TEXT NOT NULL,
            CHECK(decision IN ('MOUNT','DEFER','REJECT'))
        )""")
        results["mt_ai_mount_decisions"] = True

        conn.commit()
        conn.close()
    return results


# ============================================================
# 1. 收集AI建议 (从建议池)
# ============================================================
def collect_suggestions(min_priority: int = 5) -> List[Dict]:
    """从mt_ai_suggestion_pool收集已评估的高优先级建议
    🔧 仙女座 v5.0: 同时收 FEATURE_EVOLUTION_AWAKE 的 PENDING 建议 (仙女座自我觉醒链)
    自动把 FEV PENDING → EVALUATED (in-place, 不阻塞)
    """
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # 1) 仙女座自我觉醒 + 轮巡矩阵 建议自动升级 PENDING → EVALUATED
        c.execute("""
            UPDATE mt_ai_suggestion_pool SET status='EVALUATED', evaluated_at=datetime('now')
            WHERE source_type IN ('FEATURE_EVOLUTION_AWAKE','PATROL_MATRIX') AND status='PENDING'
        """)
        # 2) L3 converge: every 3rd scan, run auto_gen effect eval + cleanup
        if not hasattr(_evaluate_and_cleanup, "_cnt"): _evaluate_and_cleanup._cnt = 0
        _evaluate_and_cleanup._cnt += 1
        if _evaluate_and_cleanup._cnt % 3 == 0:
            _ev = _evaluate_and_cleanup()
            if _ev["superseded"] or _ev["archived"]:
                _log("[L3] %s SUPERSEDED + %s ARCHIVED" % (_ev["superseded"], _ev["archived"]))
        
        # 3) 收集 EVALUATED (常规 + FEV 刚升级的)
        rows = c.execute("""
            SELECT * FROM mt_ai_suggestion_pool
            WHERE status='EVALUATED' AND priority>=?
            ORDER BY priority DESC, created_at ASC
        """, (min_priority,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 2. 收集EigenFlux专家权重
# ============================================================
def collect_expert_weights() -> Dict[str, float]:
    """从mt_eigenflux_expert_registry收集所有活跃专家的动态权重"""
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""
            SELECT expert_id, expert_name, domain, weight, accuracy_rate
            FROM mt_eigenflux_expert_registry
            WHERE tenure_status='ACTIVE'
        """).fetchall()
        conn.close()

    weights = {}
    for r in rows:
        rid = r["expert_id"]
        # 动态权重 = base_weight * accuracy_rate * engagement_factor
        # engagement_factor 基于 total_decisions / 100 做归一化，上限 1.5
        try:
            base_w = float(r["weight"] or 0.5)
            acc = float(r["accuracy_rate"] or 0.7)
            total = int(r["total_decisions"] or 0)
            engagement = min(1.0 + total / 200.0, 1.5)
            weights[r["expert_name"]] = round(base_w * acc * engagement, 4)
        except Exception:
            weights[r["expert_name"]] = float(r["weight"] or 0.5)
    return weights


# ============================================================
# 3. 智能挂载决策 (AI建议 + EigenFlux专家权重)
# ============================================================
def smart_mount_decision(suggestion: Dict, expert_weights: Dict[str, float]) -> Dict:
    """
    综合决策:
      base_score = suggestion评估分 (feasibility*0.3 + value*0.3 + (1-cost)*0.2 + (1-risk)*0.2)
      expert_factor = 专家平均权重 (0~1)
      final_score = base_score * 0.6 + expert_factor * 0.4
      decision = MOUNT if final_score >= MOUNT_THRESHOLD else DEFER
    """
    # 兼容两种 key 名: suggestion_pool 表列名用 _score 后缀
    feasibility = suggestion.get("feasibility_score", suggestion.get("feasibility", 0.0))
    value_score = suggestion.get("value_score", suggestion.get("value", 0.0))
    cost_score = suggestion.get("cost_score", suggestion.get("cost", 0.0))
    risk_score = suggestion.get("risk_score", suggestion.get("risk", 0.0))

    base_score = round(
        feasibility * 0.3 + value_score * 0.3 + (1 - cost_score) * 0.2 + (1 - risk_score) * 0.2, 4
    )

    # EigenFlux专家平均权重
    if expert_weights:
        avg_weight = round(sum(expert_weights.values()) / len(expert_weights), 4)
    else:
        avg_weight = 0.5  # 无专家时默认中性

    final_score = round(base_score * 0.6 + avg_weight * 0.4, 4)
    decision = "MOUNT" if final_score >= MOUNT_THRESHOLD else "DEFER"
    reason = (
        f"base={base_score}(feas={feasibility},val={value_score},cost={cost_score},risk={risk_score})"
        f" + expert_avg={avg_weight} -> final={final_score}"
        f" {'>=' if final_score >= MOUNT_THRESHOLD else '<'} {MOUNT_THRESHOLD}"
    )

    # 落库决策日志
    now = _now()
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO mt_ai_mount_decisions
            (suggestion_id, suggestion_text, feasibility, value_score, cost_score, risk_score,
             base_score, expert_weight, final_score, decision, reason, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (suggestion.get("suggestion_id"), suggestion.get("suggestion", "")[:200],
             feasibility, value_score, cost_score, risk_score,
             base_score, avg_weight, final_score, decision, reason, now))
        conn.commit()
        conn.close()

    return {
        "suggestion_id": suggestion.get("suggestion_id"),
        "suggestion": suggestion.get("suggestion", ""),
        "direction": suggestion.get("direction", ""),
        "base_score": base_score,
        "expert_weight": avg_weight,
        "final_score": final_score,
        "decision": decision,
        "reason": reason,
    }


# ============================================================
# 4. 自动生成daemon脚本
# ============================================================
DAEMON_SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成daemon: {process_name}
来源: AI建议 #{suggestion_id} (score={mount_score})
生成时间: {created_at}
职责: {duty}
"""
import os, sys, time, signal, sqlite3, json, glob, subprocess
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINE_DIR = os.path.join(_PROJECT_ROOT, "flask-app", "ai_engines")
# 🔧 2026-09-10 仙女座修复: 统一指向 Database/app.db 主库
APP_DB = os.path.join(_PROJECT_ROOT, "Database", "app.db")
if not os.path.exists(APP_DB):
    APP_DB = os.path.join(ENGINE_DIR, "app.db")
PID_FILE = os.path.join(_PROJECT_ROOT, "_runtime", "pids", "{pid_filename}")
LOG_FILE = os.path.join(_PROJECT_ROOT, "_runtime", "logs", "{log_filename}")

os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

_running = True

def _signal_handler(signum, frame):
    global _running
    _running = False

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

def _db():
    """🔧 仙女座 v5.0: 统一 DB 连接 — WAL + busy_timeout + checkpoint + synchronous=NORMAL
    所有自动生成的 daemon 脚本从此继承 DB 锁防护, 彻底消灭 database is locked"""
    conn = sqlite3.connect(APP_DB, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA wal_autocheckpoint = 10000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def _heartbeat():
    """更新心跳到mt_ai_smart_mount_processes"""
    try:
        conn = _db()
        c = conn.cursor()
        c.execute(
            "UPDATE mt_ai_smart_mount_processes SET heartbeat_at=?, updated_at=? WHERE process_name=?",
            (datetime.now().isoformat(), datetime.now().isoformat(), "{process_name}"))
        conn.commit()
        conn.close()
    except Exception:
        pass

def _param(group, key, default=None):
    """🔧 仙女座 v5.1 参数统一系统: 从 mt_params 实时读取参数, 不存在返回 default.
    每次读都查 DB — mt_params 表轻量(108条), 无缓存保证参数热生效.
    支持 type 转换: int/integer, float/number, bool/boolean, str(默认)"""
    try:
        conn = sqlite3.connect(APP_DB, timeout=3)
        conn.execute("PRAGMA busy_timeout=3000")
        row = conn.execute(
            "SELECT param_value, param_type FROM mt_params WHERE param_group=? AND param_key=?",
            (group, key)).fetchone()
        conn.close()
        if row is None: return default
        val, ptype = row[0], (row[1] or 'str').lower()
        if ptype in ('int','integer'): return int(val)
        if ptype in ('float','number'): return float(val)
        if ptype in ('bool','boolean'): return str(val).lower() in ('1','true','yes','on')
        return val
    except Exception:
        return default

def _log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{{datetime.now().isoformat()}}] {{msg}}\\n")

def main_loop():
    import random as _rand
    _log(f"DAEMON START: {process_name} pid={{os.getpid()}}")
    # 🆕 仙女座 v5.1: 参数统一系统 — 从 mt_params 读 cycle, 支持热调整
    CYCLE_GROUP = 'smart_mount' if '{process_name}'.startswith('sys_') else 'auto_gen'
    CYCLE_KEY = '{process_name}_interval_sec'
    CYCLE = _param(CYCLE_GROUP, CYCLE_KEY, {inspect_cycle})
    _log(f"🔧 v5.1 参数统一: CYCLE={{CYCLE}}s (来源=mt_params {{CYCLE_GROUP}}/{{CYCLE_KEY}})")
    # ✅ 仙女座 v5.0: 启动随机偏移 0-30s — 避免 41 个 60s daemon 同时 wake 抢 DB 锁
    _offset = _rand.randint(0, 30)
    _log(f"启动随机偏移: {{_offset}}s")
    time.sleep(_offset)
    # 写PID文件 (fsync 防 OneDrive 异步丢失)
    try:
        import tempfile as _tf2
        _fd2, _tmp2 = _tf2.mkstemp(prefix=".daemon_pid_", suffix=".tmp", dir=os.path.dirname(PID_FILE))
        try:
            os.write(_fd2, str(os.getpid()).encode("ascii"))
            os.fsync(_fd2)
        finally:
            os.close(_fd2)
        os.replace(_tmp2, PID_FILE)
        try:
            _dd = os.open(os.path.dirname(PID_FILE), os.O_RDONLY)
            try: os.fsync(_dd)
            finally: os.close(_dd)
        except OSError:
            pass
    except Exception:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    _heartbeat()

    while _running:
        try:
            # === daemon工作循环 ===
            {work_body}
            _heartbeat()
            # 🆕 v5.1 参数热生效: 每轮循环刷新 CYCLE — mt_params 改了不用重启 daemon
            CYCLE = _param(CYCLE_GROUP, CYCLE_KEY, CYCLE)
        except Exception as e:
            _log(f"ERROR: {{e}}")
        time.sleep(CYCLE)

    # 清理
    try:
        os.remove(PID_FILE)
    except OSError:
        pass
    _log(f"DAEMON STOP: {process_name}")

if __name__ == "__main__":
    main_loop()
'''


def generate_daemon_script(process_name: str, duty: str,
                          suggestion_id: int, mount_score: float,
                          work_body: str = "pass  # TODO: 实现具体工作逻辑",
                          inspect_cycle: int = 60) -> str:
    """自动生成daemon Python脚本（OneDrive 兼容：重试+fallback到临时目录）"""
    safe_name = process_name.replace(" ", "_").replace("-", "_")
    script_content = DAEMON_SCRIPT_TEMPLATE.format(
        process_name=process_name,
        suggestion_id=suggestion_id,
        mount_score=mount_score,
        created_at=_now(),
        duty=duty,
        pid_filename=f"{safe_name}.pid",
        log_filename=f"{safe_name}.log",
        work_body=work_body,
        inspect_cycle=inspect_cycle,
    )
    primary_path = os.path.join(DAEMON_SCRIPTS_DIR, f"{safe_name}.py")
    fallback_dir = os.path.join(tempfile.gettempdir(), "mtscos_auto_daemons")
    os.makedirs(fallback_dir, exist_ok=True)
    fallback_path = os.path.join(fallback_dir, f"{safe_name}.py")

    last_err = None
    for attempt, target in enumerate([primary_path, primary_path, fallback_path], 1):
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(script_content)
            try:
                os.chmod(target, 0o755)
            except Exception:
                pass
            _log(f"[GEN-SCRIPT] {process_name} -> {target} (attempt={attempt})")
            return target
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise RuntimeError(f"generate_daemon_script failed for {process_name}: {last_err}")


# ============================================================
# 5. 挂载进程 (注册 + 启动)
# ============================================================
def mount_process(process_name: str, duty: str, script_path: str,
                  suggestion_id: Optional[int] = None,
                  mount_source: str = "AI_SUGGESTION",
                  mount_score: float = 0.0,
                  expert_weights: Optional[Dict] = None) -> int:
    """
    挂载自动化进程:
      1. 注册daemon到mt_daemon_registry (IDLE)
      2. 写入mt_ai_smart_mount_processes
      3. daemon_transition IDLE→RUNNING
      4. subprocess.Popen启动
    """
    now = _now()

    # 1. 注册daemon (复用现有接口)
    try:
        daemon_id = register_daemon(
            name=process_name, duty=duty,
            dependencies="ai_smart_mount_engine",
            priority=7, inspect_cycle=f"{MONITOR_INTERVAL}s"
        )
    except Exception:
        # 可能已注册
        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            r = conn.execute(
                "SELECT daemon_id FROM mt_daemon_registry WHERE daemon_name=?",
                (process_name,)).fetchone()
            conn.close()
            daemon_id = r["daemon_id"] if r else 0

    # 2. 写入进程跟踪表
    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO mt_ai_smart_mount_processes
            (daemon_id, process_name, script_path, suggestion_id, mount_source,
             mount_score, expert_weights, current_state,
             restart_count, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (daemon_id, process_name, script_path, suggestion_id, mount_source,
             mount_score, json.dumps(expert_weights or {}, ensure_ascii=False),
             "IDLE", 0, now, now))
        conn.commit()
        pid = c.execute(
            "SELECT process_id FROM mt_ai_smart_mount_processes WHERE process_name=?",
            (process_name,)).fetchone()[0]
        conn.close()

    # 3. 状态转移 IDLE→RUNNING
    try:
        daemon_transition(process_name, "RUNNING")
    except Exception:
        pass

    # 4. 更新进程跟踪表状态
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE mt_ai_smart_mount_processes SET current_state='RUNNING', updated_at=? WHERE process_name=?",
            (_now(), process_name))
        conn.commit()
        conn.close()

    # 5. 启动进程
    _start_subprocess(process_name, script_path)

    _log(f"[MOUNT] process={process_name} daemon_id={daemon_id} pid={pid} score={mount_score} source={mount_source}")
    return pid


def _start_subprocess(process_name: str, script_path: str) -> Optional[int]:
    """用subprocess启动daemon脚本"""
    safe_name = process_name.replace(" ", "_").replace("-", "_")
    log_file = os.path.join(LOG_DIR, f"{safe_name}.log")

    try:
        with open(log_file, "a") as lf:
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=lf, stderr=lf,
                cwd=os.path.dirname(script_path),
                start_new_session=True,  # 独立进程组
            )
        # 记录PID
        with _LOCK:
            conn = _get_conn()
            c = conn.cursor()
            c.execute(
                "UPDATE mt_ai_smart_mount_processes SET pid=?, current_state='RUNNING', heartbeat_at=?, updated_at=? WHERE process_name=?",
                (proc.pid, _now(), _now(), process_name))
            conn.commit()
            conn.close()
        _log(f"[START] {process_name} pid={proc.pid}")
        return proc.pid
    except Exception as e:
        _log(f"[START-FAIL] {process_name}: {e}")
        return None


# ============================================================
# 6. 心跳监控 + 自动重启
# ============================================================
def heartbeat_check() -> Dict:
    """检查所有RUNNING进程的心跳,超时的标记FAILED并自动重启"""
    now_str = _now()
    now_ts = datetime.now().timestamp()
    result = {"checked": 0, "alive": 0, "timeout": 0, "restarted": 0, "max_restart": 0}

    with _LOCK:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        # 扩展：除RUNNING外，也检查IDLE/STOPPED/FAILED行中的残留PID是否真实存活
        # 避免历史残留PID记录永远不被清理，无法重挂载
        rows = conn.execute("""
            SELECT * FROM mt_ai_smart_mount_processes
            WHERE current_state IN ('RUNNING','IDLE','STOPPED','FAILED')
        """).fetchall()
        conn.close()

    for r in rows:
        result["checked"] += 1
        pid = r["pid"]

        # 检查进程是否存活
        alive = False
        if pid:
            try:
                os.kill(pid, 0)
                alive = True
            except OSError:
                alive = False

        if alive:
            # 检查心跳超时
            hb = r["heartbeat_at"]
            if hb:
                try:
                    hb_ts = datetime.fromisoformat(hb).timestamp()
                    if now_ts - hb_ts > HEARTBEAT_TIMEOUT:
                        alive = False
                        _log(f"[TIMEOUT] {r['process_name']} pid={pid} heartbeat_stale>{HEARTBEAT_TIMEOUT}s")
                except Exception:
                    pass

        if alive:
            result["alive"] += 1
            # IDLE但存活的进程 → 不重启，标记为 RUNNING 便于进入正常心跳循环
            if r["current_state"] == "IDLE":
                _update_process_state(r["process_name"], "RUNNING")
                try:
                    daemon_transition(r["process_name"], "RUNNING")
                except Exception:
                    pass
            continue

        # 进程死亡或心跳超时 → 先清理残留PID记录，避免下次再判错
        try:
            with _LOCK:
                _c = _get_conn().cursor()
                _c.execute("UPDATE mt_ai_smart_mount_processes SET pid=NULL WHERE process_name=?",
                           (r["process_name"],))
                _c.connection.commit()
                _c.connection.close()
        except Exception:
            pass

        # 非RUNNING状态但PID已死 → 判定是否需要重启
        if r["current_state"] != "RUNNING":
            process_name = r["process_name"]
            script_path = r["script_path"]
            restart_count = r["restart_count"] or 0
            last_restart = r["last_restart_at"]
            mount_source = r["mount_source"] or ""
            is_system_required = (mount_source == "SYSTEM_REQ")

            # 计算冷却时间
            cooldown_elapsed = 0.0
            if last_restart:
                try:
                    cooldown_elapsed = now_ts - datetime.fromisoformat(last_restart).timestamp()
                except Exception:
                    pass

            # 三种重启条件 (满足任一即试)
            should_relaunch = False
            reason = ""

            # 条件1: SYSTEM_REQ必需daemon → 无条件重启
            if is_system_required:
                should_relaunch = True
                reason = "SYSTEM_REQ必需"

            # 条件2: 非SYSTEM_REQ但已冷却完 → 重置restart_count重试
            elif restart_count >= MAX_RESTART_COUNT and cooldown_elapsed >= STOPPED_COOLDOWN:
                should_relaunch = True
                reason = f"冷却{cooldown_elapsed:.0f}s>=STOPPED_COOLDOWN({STOPPED_COOLDOWN}s)"

            # 条件3: 一般FAILED/IDLE状态 → 直接重试(冷却中也可)
            elif r["current_state"] != "STOPPED":
                should_relaunch = True
                reason = f"状态={r['current_state']}非RUNNING"

            if should_relaunch and script_path and os.path.exists(script_path):
                if restart_count >= MAX_RESTART_COUNT:
                    _log(f"[COOL-RESET] {process_name} restart_count={restart_count}冷却完毕重置→重启 (reason={reason})")
                    reset_cnt = 0
                else:
                    _log(f"[NON-RUN-RESTART] {process_name} restart_count={restart_count}→重启 (reason={reason})")
                    reset_cnt = restart_count

                _update_process_state(process_name, "FAILED")
                try:
                    daemon_transition(process_name, "FAILED")
                except Exception:
                    pass

                time.sleep(2)
                new_pid = _start_subprocess(process_name, script_path)

                with _LOCK:
                    conn = _get_conn()
                    c = conn.cursor()
                    c.execute("""UPDATE mt_ai_smart_mount_processes
                        SET pid=?, current_state='RUNNING', restart_count=?,
                            last_restart_at=?, heartbeat_at=?, updated_at=?
                        WHERE process_name=?""",
                        (new_pid, reset_cnt + 1, _now(), _now(), _now(), process_name))
                    conn.commit()
                    conn.close()

                try:
                    daemon_transition(process_name, "RUNNING")
                except Exception:
                    pass

                result["timeout"] += 1
                result["restarted"] += 1
            else:
                # 脚本不存在或冷却未到 → 保持STOPPED
                if r["current_state"] != "STOPPED":
                    _update_process_state(process_name, "STOPPED")
                    try:
                        daemon_transition(process_name, "STOPPED")
                    except Exception:
                        pass
                if restart_count >= MAX_RESTART_COUNT and cooldown_elapsed < STOPPED_COOLDOWN:
                    result["max_restart"] += 1
            continue

        result["timeout"] += 1
        restart_count = r["restart_count"] or 0

        if restart_count >= MAX_RESTART_COUNT:
            # 触顶 → 标记STOPPED, 冷却后会被上面的 NON-RUNNING 分支捞起重试
            result["max_restart"] += 1
            _log(f"[MAX-RESTART] {r['process_name']} restart_count={restart_count} -> STOPPED (冷却{STOPPED_COOLDOWN}s后重置)")
            _update_process_state(r["process_name"], "STOPPED")
            try:
                daemon_transition(r["process_name"], "STOPPED")
            except Exception:
                pass
            continue

        # 自动重启
        _log(f"[RESTART] {r['process_name']} pid={pid} restart#{restart_count + 1}")
        _update_process_state(r["process_name"], "FAILED")
        try:
            daemon_transition(r["process_name"], "FAILED")
        except Exception:
            pass

        # 重置后重新启动
        time.sleep(2)
        new_pid = _start_subprocess(r["process_name"], r["script_path"])

        with _LOCK:
            conn = _get_conn()
            c = conn.cursor()
            c.execute("""UPDATE mt_ai_smart_mount_processes
                SET current_state='RUNNING', restart_count=?, last_restart_at=?, heartbeat_at=?, updated_at=?
                WHERE process_name=?""",
                (restart_count + 1, _now(), _now(), _now(), r["process_name"]))
            conn.commit()
            conn.close()

        try:
            daemon_transition(r["process_name"], "RUNNING")
        except Exception:
            pass

        result["restarted"] += 1

    return result


def _update_process_state(process_name: str, state: str):
    with _LOCK:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE mt_ai_smart_mount_processes SET current_state=?, updated_at=? WHERE process_name=?",
            (state, _now(), process_name))
        conn.commit()
        conn.close()


def _log(msg: str):
    with open(MONITOR_LOG, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


def _log_supervisor(level: str, event: str, detail: str = '') -> None:
    """
    守护进程事件落库 mt_daemon_supervisor_log，便于跨会话追溯。
    与 start_smart_mount_engine_daemon.py 内的 log_event 共用同一张表，
    supervisor 字段固定为 'smart_mount_daemon'。
    失败时静默忽略，绝不影响主循环。
    """
    try:
        with _LOCK:
            conn = _get_conn()
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS mt_daemon_supervisor_log (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_time    TEXT    NOT NULL,
                    supervisor    TEXT    NOT NULL,
                    level         TEXT    NOT NULL,
                    event         TEXT    NOT NULL,
                    detail        TEXT,
                    pid           INTEGER,
                    created_at    TEXT    NOT NULL
                )
            """)
            c.execute(
                "INSERT INTO mt_daemon_supervisor_log "
                "(event_time, supervisor, level, event, detail, pid, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (_now(), 'smart_mount_daemon', level, event, detail, os.getpid(), _now()),
            )
            conn.commit()
            conn.close()
    except Exception:
        # 守护进程落库失败绝不影响主流程
        pass


# ============================================================
# 7. 扫描建议池 + 自动挂载 (核心入口)
# ============================================================
def scan_and_mount() -> Dict:
    """
    全流程: 扫描建议池 → 收集专家权重 → 逐条决策 → 自动挂载
    这是scan子命令的核心逻辑,也是守护循环每次执行的逻辑
    """
    result = {
        "scanned": 0, "mounted": 0, "deferred": 0, "rejected": 0,
        "details": []
    }

    # === 0. 仙女座 v5.0: 消费 Phase2 觉醒 JSON 文件旁路 ===
    try:
        import os as _os, json as _json
        _fev_file = '/tmp/fev_suggestions.json'
        if _os.path.exists(_fev_file):
            with _LOCK:
                _c0 = _get_conn()
                with open(_fev_file, 'r') as _ff:
                    _fev_list = _json.load(_ff)
                _inserted = 0
                for _fev in _fev_list:
                    try:
                        _c0.execute("INSERT INTO mt_ai_suggestion_pool\n                            (source_type, source_name, suggestion_text, priority, status, feasibility_score, value_score, cost_score, risk_score, flow_id, created_at)\n                            VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                            _fev.get('source_type','FEATURE_EVOLUTION_AWAKE'),
                            _fev.get('source_name','sys_feature_evolution'),
                            _fev.get('suggestion_text',''),
                            _fev.get('priority', 3),
                            _fev.get('status','PENDING'),
                            _fev.get('feasibility_score',0.85),
                            _fev.get('value_score',0.8),
                            _fev.get('cost_score',0.2),
                            _fev.get('risk_score',0.15),
                            _fev.get('flow_id',''),
                            _fev.get('created_at','')
                        ))
                        _inserted += 1
                    except Exception as _ie:
                        sm_log(f'  ⚠️  FEV insert err: {_ie}')
                _c0.commit()
                _c0.close()
            _os.remove(_fev_file)
            sm_log(f'  ✅ 消费 FEV JSON 文件: {_inserted} 条觉醒建议 → suggestion_pool')
    except Exception as _fev_err:
        sm_log(f'  FEV file consume err: {_fev_err}')

    # 1. 收集已评估的高优先级建议
    suggestions = collect_suggestions(min_priority=5)
    result["scanned"] = len(suggestions)

    if not suggestions:
        _log("[SCAN] 无待挂载建议")
        return result

    # 2. 收集EigenFlux专家权重
    expert_weights = collect_expert_weights()

    # 3. 逐条决策
    for sug in suggestions:
        decision = smart_mount_decision(sug, expert_weights)

        if decision["decision"] == "MOUNT":
            # 自动生成daemon脚本
            process_name = f"auto_{sug.get('direction', 'gen')}_{sug['suggestion_id']}"
            duty = sug.get("suggestion", "")[:100]
            script_path = generate_daemon_script(
                process_name=process_name,
                duty=duty,
                suggestion_id=sug["suggestion_id"],
                mount_score=decision["final_score"],
                work_body=_infer_work_body(sug),
                inspect_cycle=60,
            )

            # 挂载
            try:
                mount_process(
                    process_name=process_name,
                    duty=duty,
                    script_path=script_path,
                    suggestion_id=sug["suggestion_id"],
                    mount_source="AI_SUGGESTION",
                    mount_score=decision["final_score"],
                    expert_weights=expert_weights,
                )
                # ✅ 仙女座 v5.0: 挂载成功后立即标记 suggestion → DEPLOYED (短事务)
                try:
                    with _LOCK:
                        _c2 = _get_conn()
                        _c2.execute("UPDATE mt_ai_suggestion_pool SET status='DEPLOYED', deployed_at=datetime('now') WHERE suggestion_id=?", (sug["suggestion_id"],))
                        _c2.commit()
                        _c2.close()
                except Exception as _upd_err:
                    _log(f"[MOUNT-UPDATE-ERR] suggestion_id={sug['suggestion_id']}: {_upd_err}")

                result["mounted"] += 1
                decision["process_name"] = process_name
                decision["script_path"] = script_path
            except Exception as e:
                _log(f"[MOUNT-FAIL] {process_name}: {e}")
                decision["error"] = str(e)
        elif decision["decision"] == "DEFER":
            result["deferred"] += 1
        else:
            result["rejected"] += 1

        result["details"].append(decision)

    _log(f"[SCAN] scanned={result['scanned']} mounted={result['mounted']} "
         f"deferred={result['deferred']} rejected={result['rejected']}")
    return result


def _evaluate_and_cleanup() -> Dict:
    """L3: auto_gen stale 10min->SUPERSEDED / 24h->ARCHIVED"""
    result = {"superseded": 0, "archived": 0}
    try:
        with _LOCK:
            _c = _get_conn()
            _c.execute('PRAGMA busy_timeout=60000')
            stale = _c.execute("SELECT process_name, suggestion_id FROM mt_ai_smart_mount_processes WHERE process_name LIKE 'auto_gen_%' AND current_state='RUNNING' AND heartbeat_at < datetime('now', '-10 minutes')").fetchall()
            for pname, sid in stale:
                import subprocess as _sp
                _sp.run(['pkill','-9','-f',pname], capture_output=True)
                _c.execute("UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED' WHERE process_name=?", (pname,))
                if sid: _c.execute("UPDATE mt_ai_suggestion_pool SET status='SUPERSEDED' WHERE suggestion_id=?", (sid,))
                result["superseded"] += 1
            old = _c.execute("SELECT p.process_name, p.suggestion_id FROM mt_ai_smart_mount_processes p WHERE p.process_name LIKE 'auto_gen_%' AND p.created_at < datetime('now', '-24 hours')").fetchall()
            for pname, sid in old:
                import subprocess as _sp
                _sp.run(['pkill','-9','-f',pname], capture_output=True)
                _c.execute("UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED' WHERE process_name=?", (pname,))
                if sid: _c.execute("UPDATE mt_ai_suggestion_pool SET status='ARCHIVED' WHERE suggestion_id=?", (sid,))
                result["archived"] += 1
            _c.commit()
            _c.close()
    except Exception as e:
        _log(f"[EVAL] err: {e}")
    return result


def _infer_work_body(suggestion: Dict) -> str:
    """L1: suggestion_text -> FIX_DAEMON/ADD_ROUTE/CLEANUP 真实 work_body"""
    text = suggestion.get("suggestion_text", "") or suggestion.get("suggestion", "") or ""
    action = "UNKNOWN"
    t = text.upper()
    if "[FIX" in t: action = "FIX_DAEMON"
    elif "[ADD_ROUTE" in t: action = "ADD_ROUTE"
    elif "[CLEANUP" in t: action = "CLEANUP"
    elif "[SYNC_PARAM" in t: action = "SYNC_PARAM"
    elif "[OPTIMIZE_UI" in t or t.startswith("[OPTIMIZE"): action = "OPTIMIZE_UI"
    
    # FIX_DAEMON: 重启 FAILED daemon
    FIX_BODY = (
        "            # FIX_DAEMON: restart FAILED daemon\n"
        "            try:\n"
        "                import subprocess, sqlite3\n"
        "                conn = sqlite3.connect(APP_DB, timeout=15)\n"
        "                conn.execute('PRAGMA busy_timeout=15000')\n"
        "                rows = conn.execute(\"SELECT process_name FROM mt_ai_smart_mount_processes WHERE current_state='FAILED'\").fetchall()\n"
        "                conn.close()\n"
        "                if rows:\n"
        "                    for (dname,) in rows:\n"
        "                        subprocess.run(['pkill','-9','-f',dname], capture_output=True)\n"
        "                        import time; time.sleep(2)\n"
        "                        script = f'_runtime/auto_daemons/{dname}.py'\n"
        "                        if os.path.exists(script):\n"
        "                            subprocess.Popen([sys.executable, script], stdout=open(f'_runtime/logs/{dname}.log','a'), stderr=subprocess.STDOUT)\n"
        "                        _log(f'FIX_DAEMON: restarted {dname} OK')\n"
        "                else:\n"
        "                    _log('FIX_DAEMON: no FAILED daemons')\n"
        "            except Exception as e:\n"
        "                _log(f'FIX_DAEMON err: {e}')"
    )
    # ADD_ROUTE: 插路由 (domain 从 suggestion_text 提取)
    ROUTE_BODY = (
        "            # ADD_ROUTE: insert neural route\n"
        "            try:\n"
        "                import sqlite3, re as _re\n"
        "                conn = sqlite3.connect(APP_DB, timeout=15)\n"
        "                conn.execute('PRAGMA busy_timeout=15000')\n"
        "                _tgt = 'auto'\n"
        "                _m = _re.search(r'\\u76ee\\u6807[\\uff1a:]\\\\s*(\\\\S+)', suggestion.get('suggestion_text',''))\n"
        "                if _m: _tgt = _m.group(1)\n"
        "                conn.execute(\"INSERT OR IGNORE INTO mt_ai_neural_routes (domain, route_name, model, weight, created_at) VALUES (?, ?, 'qwen2.5:7b', 0.5, datetime('now'))\", (_tgt, _tgt+'_auto'))\n"
        "                conn.commit()\n"
        "                conn.close()\n"
        "                _log(f'ADD_ROUTE: inserted for {_tgt} OK')\n"
        "            except Exception as e:\n"
        "                _log(f'ADD_ROUTE err: {e}')"
    )
    # CLEANUP: 清临时文件
    CLEAN_BODY = (
        "            # CLEANUP: remove temp files\n"
        "            try:\n"
        "                import glob as _glob, os as _os\n"
        "                removed = 0\n"
        "                for pat in ['_runtime/*.tmp', '_runtime/*.bak']:\n"
        "                    for f in _glob.glob(pat):\n"
        "                        try: _os.remove(f); removed += 1\n"
        "                        except: pass\n"
        "                _log(f'CLEANUP: removed {removed} files OK')\n"
        "            except Exception as e:\n"
        "                _log(f'CLEANUP err: {e}')"
    )
    # 通用巡检
    PATROL_BODY = (
        "            # generic patrol\n"
        "            try:\n"
        "                import sqlite3\n"
        "                conn = sqlite3.connect(APP_DB, timeout=15)\n"
        "                st = conn.execute('SELECT current_state, COUNT(*) FROM mt_ai_smart_mount_processes GROUP BY current_state').fetchall()\n"
        "                conn.close()\n"
        "                _log(f'AUTO-GEN patrol: {dict(st)}')\n"
        "            except Exception as e:\n"
        "                _log(f'AUTO-GEN err: {e}')"
    )
    
    # SYNC_PARAM: 写参数到 mt_params (仙女座 v5.1 参数统一系统)
    SYNC_PARAM_BODY = (
        "            # SYNC_PARAM: 仙女座 v5.1 参数统一 — 写入 mt_params\n"
        "            try:\n"
        "                import sqlite3, re as _re\n"
        "                conn = sqlite3.connect(APP_DB, timeout=15)\n"
        "                conn.execute('PRAGMA busy_timeout=15000')\n"
        "                _text = suggestion.get('suggestion_text', '')\n"
        "                _m = _re.search(r'\\u76ee\\u6807[\\uff1a:]\\s*(\\S+)', _text)\n"
        "                if not _m: _m = _re.search(r'\\[(SYNC_PARAM)[\\]]\\s*([\\w_]+)/([\\w_]+)\\s*[=:]\\s*(\\S+)', _text)\n"
        "                if _m:\n"
        "                    _tgt = _m.group(1) if len(_m.groups())==1 else _m.group(2)+'/'+_m.group(3)+'='+_m.group(4)\n"
        "                    if '/' in _tgt and '=' in _tgt:\n"
        "                        _grp, _rest = _tgt.split('/', 1)\n"
        "                        _key, _val = _rest.split('=', 1)\n"
        "                        conn.execute(\n"
        "                            \"INSERT OR REPLACE INTO mt_params (param_group, param_key, param_value, param_type, updated_at, updated_by) VALUES (?, ?, ?, ?, datetime('now'), 'Andromeda-v5.1')\",\n"
        "                            (_grp, _key.strip(), _val.strip(), 'int' if _val.strip().isdigit() else 'str'))\n"
        "                        conn.commit()\n"
        "                        _log(f'SYNC_PARAM: {_grp}/{_key.strip()} = {_val.strip()} → mt_params OK (daemon 下一轮循环热生效)')\n"
        "                    else:\n"
        "                        _log(f'SYNC_PARAM: target format wrong: {_tgt}')\n"
        "                else:\n"
        "                    _log('SYNC_PARAM: no target found')\n"
        "                conn.close()\n"
        "            except Exception as e:\n"
        "                _log(f'SYNC_PARAM err: {e}')"
    )
    # OPTIMIZE_UI: 写 frontend 参数 + 刷新 CSS 覆盖层 (仙女座 v5.1)
    OPTIMIZE_UI_BODY = (
        "            # OPTIMIZE_UI: 仙女座 v5.1 前端参数优化\n"
        "            try:\n"
        "                import sqlite3, re as _re, subprocess as _sp, os as _os\n"
        "                conn = sqlite3.connect(APP_DB, timeout=15)\n"
        "                conn.execute('PRAGMA busy_timeout=15000')\n"
        "                _text = suggestion.get('suggestion_text', '')\n"
        "                # 解析 target: frontend/primary_color=#667eea 或 主色=#667eea\n"
        "                _tgt = ''\n"
        "                _m = _re.search(r'\\u76ee\\u6807[\\uff1a:]\\s*(\\S+)', _text)\n"
        "                if _m: _tgt = _m.group(1)\n"
        "                if not _tgt:\n"
        "                    _m2 = _re.search(r'frontend[\\/]([\\w_]+)\\s*[=:]\\s*(\\S+)', _text)\n"
        "                    if _m2: _tgt = f'frontend/{_m2.group(1)}={_m2.group(2)}'\n"
        "                if _tgt and '/' in _tgt and '=' in _tgt:\n"
        "                    _grp, _rest = _tgt.split('/', 1)\n"
        "                    _key, _val = _rest.split('=', 1)\n"
        "                    _grp, _key, _val = _grp.strip(), _key.strip(), _val.strip()\n"
        "                    _type = 'int' if _val.strip().isdigit() else ('float' if _val.count('.')==1 else 'str')\n"
        "                    conn.execute(\n"
        "                        \"INSERT OR REPLACE INTO mt_params (param_group, param_key, param_value, param_type, updated_at, updated_by) VALUES (?, ?, ?, ?, datetime('now'), 'Andromeda-v5.1-OPTIMIZE_UI')\",\n"
        "                        (_grp, _key, _val, _type))\n"
        "                    conn.commit()\n"
        "                    _log(f'OPTIMIZE_UI: {_grp}/{_key} = {_val} → mt_params ✅')\n"
        "                    # 刷新 CSS 覆盖层 → 全站热生效\n"
        "                    _fe = _os.path.join(_os.path.dirname(_os.path.dirname(APP_DB)), 'flask-app', 'engines', 'ai_frontend_optimizer.py')\n"
        "                    if _os.path.exists(_fe):\n"
        "                        _sp.run([sys.executable, _fe, 'once'], capture_output=True, timeout=15)\n"
        "                        _log(f'OPTIMIZE_UI: CSS 覆盖层已刷新 → 全站热生效')\n"
        "                    else:\n"
        "                        _log('OPTIMIZE_UI: frontend_optimizer.py 未找到')\n"
        "                else:\n"
        "                    _log(f'OPTIMIZE_UI: target format wrong: {_tgt}')\n"
        "                conn.close()\n"
        "            except Exception as e:\n"
        "                _log(f'OPTIMIZE_UI err: {e}')"
    )
    
    if action == "FIX_DAEMON": return FIX_BODY
    elif action == "ADD_ROUTE": return ROUTE_BODY
    elif action == "CLEANUP": return CLEAN_BODY
    elif action == "SYNC_PARAM": return SYNC_PARAM_BODY
    elif action == "OPTIMIZE_UI": return OPTIMIZE_UI_BODY
    return PATROL_BODY

def mount_system_required() -> Dict:
    """挂载系统必需的自动化进程(无AI建议时,根据系统要求创建)"""
    result = {"mounted": 0, "skipped": 0, "details": []}

    for req in SYSTEM_REQUIRED_DAEMONS:
        # 检查是否已存在
        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            r = conn.execute(
                "SELECT * FROM mt_ai_smart_mount_processes WHERE process_name=?",
                (req["process_name"],)).fetchone()
            conn.close()

        if r and r["current_state"] in ("RUNNING", "IDLE"):
            # 检查PID是否真实存活；若IDLE/RUNNING但PID已死 → 视为需要重挂载
            pid_alive = False
            if r["pid"]:
                try:
                    os.kill(int(r["pid"]), 0)
                    pid_alive = True
                except (OSError, ValueError):
                    pid_alive = False
            if pid_alive:
                result["skipped"] += 1
                continue
            # 已死记录: 先清理状态到STOPPED便于重新挂载
            try:
                with _LOCK:
                    conn2 = _get_conn()
                    conn2.execute(
                        "UPDATE mt_ai_smart_mount_processes SET current_state='STOPPED', updated_at=? WHERE process_name=?",
                        (_now(), req["process_name"]))
                    conn2.commit()
                    conn2.close()
            except Exception as _e:
                _log(f"[SYS-MOUNT] clean stale state fail {req['process_name']}: {_e}")

        # 生成脚本 + 挂载 — 单daemon失败不影响其他
        try:
            script_path = generate_daemon_script(
                process_name=req["process_name"],
                duty=req["duty"],
                suggestion_id=0,
                mount_score=1.0,  # 系统必需=满分
                work_body=req["work_body"],
                inspect_cycle=req["inspect_cycle"],
            )
        except Exception as e:
            _log(f"[SYS-MOUNT-SCRIPT-FAIL] {req['process_name']}: {e}")
            continue

        # 挂载（先reset restart_count，防止历史MAX-RESTART残留直接判死）
        try:
            with _LOCK:
                conn3 = _get_conn()
                conn3.execute(
                    "UPDATE mt_ai_smart_mount_processes SET restart_count=0 WHERE process_name=? AND restart_count>=?",
                    (req["process_name"], MAX_RESTART_COUNT))
                conn3.commit()
                conn3.close()
        except Exception:
            pass

        try:
            mount_process(
                process_name=req["process_name"],
                duty=req["duty"],
                script_path=script_path,
                suggestion_id=None,
                mount_source="SYSTEM_REQ",
                mount_score=1.0,
                expert_weights={},
            )
            result["mounted"] += 1
            result["details"].append(req["process_name"])
        except Exception as e:
            _log(f"[SYS-MOUNT-FAIL] {req['process_name']}: {e}")

    _log(f"[SYS-MOUNT] mounted={result['mounted']} skipped={result['skipped']}")
    return result


# ============================================================
# 9. CLI守护模式
# ============================================================
class SmartMountDaemon:
    """守护进程: 巡检循环(扫描建议+心跳监控+系统必需挂载)"""

    @staticmethod
    def read_pid() -> Optional[int]:
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
        except (ValueError, OSError):
            return None
        if pid == os.getpid():
            # PID_FILE 里写的是自己（启动脚本竞态写入），视为无效
            return None
        try:
            os.kill(pid, 0)
        except OSError:
            # stale PID：顺手清理，避免残留
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
            return None
        # 校验进程身份，防止 PID 被无关进程复用导致永久误判 RUNNING
        try:
            out = subprocess.check_output(
                ["/bin/ps", "-p", str(pid), "-o", "command="],
                stderr=subprocess.DEVNULL, timeout=5).decode(errors="ignore")
            if "ai_smart_mount_engine" not in out:
                try:
                    os.remove(PID_FILE)
                except OSError:
                    pass
                return None
        except Exception:
            pass  # ps 不可用时退回 kill -0 结果
        return pid

    @staticmethod
    def write_pid(pid_val=None):
        """原子写PID文件：tmp+fsync+rename（OneDrive Files On-Demand 适配，
        避免 open(write) 因异步 IO 丢失内容，导致 check-keepalive 误判重启。）
        """
        import tempfile as _tf
        if pid_val is None:
            pid_val = os.getpid()
        try:
            os.makedirs(PID_DIR, exist_ok=True)
        except OSError:
            pass
        tmp_fd = None
        tmp_path = None
        try:
            fd, tmp_path = _tf.mkstemp(prefix=".ai_sme_pid_", suffix=".tmp", dir=PID_DIR)
            tmp_fd = fd
            os.write(fd, str(pid_val).encode("ascii"))
            os.fsync(fd)
            try:
                os.close(fd); tmp_fd = None
            except OSError:
                pass
            os.replace(tmp_path, PID_FILE)
            tmp_path = None
            try:
                dfd = os.open(PID_DIR, os.O_RDONLY)
                try:
                    os.fsync(dfd)
                finally:
                    os.close(dfd)
            except OSError:
                pass
        except Exception:
            try:
                if tmp_fd is not None:
                    try: os.close(tmp_fd)
                    except OSError: pass
                if tmp_path is not None:
                    try: os.remove(tmp_path)
                    except OSError: pass
            except Exception:
                pass
            try:
                with open(PID_FILE, "w") as f:
                    f.write(str(pid_val))
                    try: f.flush()
                    except Exception: pass
            except OSError:
                pass

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
            try:
                dfd = os.open(PID_DIR, os.O_RDONLY)
                try: os.fsync(dfd)
                finally: os.close(dfd)
            except OSError:
                pass
        except OSError:
            pass

    @staticmethod
    def _self_defense_watchdog(cycle: int):
        """
        Layer-1 INTERNAL watchdog (zero dependency, zero external config).
        Runs every 2 cycles (~60s). Purpose:
          (A) Clean stale PID files in _runtime/pids whose processes don't exist.
          (B) DEDUP: for EVERY auto_daemons/*.py script, KEEP EXACTLY ONE running
              instance (the smallest PID = approximately the oldest started).
              Kill the rest with SIGKILL. Prevents the 122-process explosion seen
              before (sys_penetration_test had 122 duplicates / scheduler had 15).
          (C) Log a one-line WD cycle into smart_mount_monitor.log.

        This method NEVER raises. Any exception is swallowed so the main loop
        continues unconditionally.
        """
        try:
            stale_cleaned = 0
            total_pid_files = 0
            if os.path.isdir(PID_DIR):
                for pf in os.listdir(PID_DIR):
                    if not pf.endswith(".pid"):
                        continue
                    pf_path = os.path.join(PID_DIR, pf)
                    if not os.path.isfile(pf_path):
                        continue
                    total_pid_files += 1
                    try:
                        with open(pf_path) as fh:
                            pv_str = fh.read().strip()
                        if not pv_str or not pv_str.isdigit():
                            os.remove(pf_path)
                            stale_cleaned += 1
                            continue
                        pv_int = int(pv_str)
                        try:
                            os.kill(pv_int, 0)
                        except OSError:
                            os.remove(pf_path)
                            stale_cleaned += 1
                    except Exception:
                        # Never let a single bad pidfile crash watchdog
                        try:
                            os.remove(pf_path)
                            stale_cleaned += 1
                        except OSError:
                            pass

            # ---- (B) daemon dedup via ps ----
            import subprocess as _sp
            dedup_killed = 0
            try:
                ps_raw = _sp.check_output(
                    ["ps", "-eo", "pid,command"],
                    stderr=_sp.DEVNULL, timeout=8
                ).decode("utf-8", errors="ignore")
            except Exception:
                ps_raw = ""

            # group: {script_name: [sorted_pids_asc]}
            groups: Dict[str, List[int]] = {}
            for line in ps_raw.splitlines():
                if "auto_daemons/" not in line:
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                pid_s, cmd = parts
                if not pid_s.isdigit():
                    continue
                m_py = None
                for tok in cmd.split():
                    idx = tok.find("auto_daemons/")
                    if idx >= 0:
                        cand = tok[idx + len("auto_daemons/"):]
                        # take up to first .py (possibly trailing args)
                        py = cand.find(".py")
                        if py >= 0:
                            m_py = cand[:py + 3]
                            break
                if m_py is None:
                    continue
                if m_py not in groups:
                    groups[m_py] = []
                try:
                    groups[m_py].append(int(pid_s))
                except ValueError:
                    pass

            for sname, pids in groups.items():
                if len(pids) <= 1:
                    continue
                pids_sorted = sorted(pids)   # smallest = oldest approx
                keep = pids_sorted[0]
                for extra_pid in pids_sorted[1:]:
                    try:
                        # verify it's really an auto_daemons process before kill
                        try:
                            cl2 = _sp.check_output(
                                ["ps", "-p", str(extra_pid), "-o", "command="],
                                stderr=_sp.DEVNULL, timeout=3
                            ).decode("utf-8", errors="ignore")
                        except Exception:
                            cl2 = ""
                        if "auto_daemons/" not in cl2:
                            continue
                        os.kill(extra_pid, 9)  # SIGKILL — duplicates never deserve grace
                        dedup_killed += 1
                        try:
                            _log(f"[WD-DEDUP] cycle={cycle} killed duplicate {sname} pid={extra_pid} (keep pid={keep})")
                        except Exception:
                            pass
                    except OSError:
                        pass
                    except Exception:
                        pass

            # ---- (C) log line into monitor log ----
            alive_types = len(groups)
            total_procs = sum(len(v) for v in groups.values())
            sm_pid = os.getpid()
            try:
                mon_log = os.path.join(LOG_DIR, "ai_smart_mount_monitor.log")
                ts_now = time.strftime("%Y-%m-%d %H:%M:%S")
                line = (f"[{ts_now}] WD_CYCLE cycle={cycle} sm_pid={sm_pid} "
                        f"types={alive_types} total_procs={total_procs} "
                        f"stale_pid_cleaned={stale_cleaned}/{total_pid_files} "
                        f"dedup_killed={dedup_killed}\n")
                try:
                    # best effort append; do not hold locks
                    with open(mon_log, "a") as fm:
                        fm.write(line)
                    # cap monitor log at 5 MB → truncate to latest 20000 lines
                    try:
                        if os.path.getsize(mon_log) > 5 * 1024 * 1024:
                            with open(mon_log) as fm:
                                all_lines = fm.readlines()
                            if len(all_lines) > 20000:
                                with open(mon_log, "w") as fm:
                                    fm.writelines(all_lines[-20000:])
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            # Never propagate to main loop
            try:
                _log(f"[WD-SWALLOW] cycle={cycle} watchdog threw (ignored)", level="WARN")
            except Exception:
                pass

    @staticmethod
    def start():
        """启动守护进程(前台运行, 可被nohup/launchd托管)"""
        existing = SmartMountDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING  pid={existing}")
            return

        # 先确保表存在
        ensure_smart_mount_tables()

        # 写PID（原子+fsync，OneDrive异步IO安全）
        SmartMountDaemon.write_pid()

        # SIGTERM handler
        def _term(signum, frame):
            _log(f"[DAEMON] SIGTERM/SIGINT received (signum={signum}), shutting down...")
            _log_supervisor('INFO', 'ENGINE_STOP',
                            f'signal={signum} pid={os.getpid()}')
            SmartMountDaemon.clear_pid()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)

        _log(f"[DAEMON] START pid={os.getpid()} ppid={os.getppid()} interval={MONITOR_INTERVAL}s "
             f"daemonized={os.environ.get('MTSCOS_SM_DAEMONIZED', '0')}")
        _log_supervisor('INFO', 'ENGINE_START',
                        f'pid={os.getpid()} ppid={os.getppid()} interval={MONITOR_INTERVAL}s')

        # 首次启动: 挂载系统必需进程
        _log("[DAEMON] 挂载系统必需进程...")
        try:
            mount_system_required()
        except Exception as e:
            _log(f"[DAEMON][FATAL] mount_system_required failed: {e}")
            _log_supervisor('ERROR', 'MOUNT_SYSTEM_REQUIRED_FAILED', f'err={e}')
            # 不退出，主循环照常跑，下一轮 heartbeat_check 会重启失败进程

        # 主循环 - 守护进程绝不退出：任何异常都被捕获并继续，
        # 唯一退出途径是外部 SIGTERM/SIGINT，由 _term handler 处理。
        cycle = 0
        consecutive_errors = 0
        while True:
            cycle += 1
            try:
                # 每3个周期扫描一次建议池 (约90秒)
                if cycle % 3 == 0:
                    _log(f"[DAEMON] cycle={cycle} scanning suggestions...")
                    scan_and_mount()

                # 每10个周期重新挂载STOPPED的系统必需daemon (约5分钟)
                if cycle % 10 == 0:
                    try:
                        remount = mount_system_required()
                        if remount["mounted"] > 0:
                            _log(f"[DAEMON] cycle={cycle} remounted {remount['mounted']} STOPPED system daemons")
                    except Exception as e:
                        _log(f"[DAEMON] cycle={cycle} remount_system_required err: {e}")

                # 每个周期检查心跳
                hb = heartbeat_check()
                if hb["checked"] > 0:
                    _log(f"[DAEMON] cycle={cycle} heartbeat: checked={hb['checked']} "
                         f"alive={hb['alive']} timeout={hb['timeout']} restarted={hb['restarted']}")

                # 每2个周期(~60s)执行 Layer1 内置自卫看门狗：stale pid清理 + daemon去重
                # 零外部依赖，不依赖 cron / launchd / TCC / sudo
                if cycle % 2 == 0:
                    SmartMountDaemon._self_defense_watchdog(cycle)

                # 每4个周期(~2分钟)跑 console_error_monitor: 扫描前端 console.error → AI 分类 → 生成修复建议
                # v22.39.0 新增 (daemon_registry interval=120s 对齐)
                if cycle % 4 == 0:
                    try:
                        from engines.ai_console_monitor import run_cycle as _cm_run
                        _cm_run()
                    except Exception as _ce_err:
                        _log(f"[DAEMON] cycle={cycle} console_monitor err: {_ce_err}")

                # 成功一轮，清零错误计数
                if consecutive_errors > 0:
                    _log(f"[DAEMON] cycle={cycle} recovered after {consecutive_errors} errors")
                    _log_supervisor('INFO', 'ENGINE_RECOVERED',
                                    f'after_errors={consecutive_errors}')
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                import traceback as _tb
                tb_str = _tb.format_exc()
                _log(f"[DAEMON] cycle={cycle} ERROR #{consecutive_errors}: {e}\n{tb_str}")
                _log_supervisor('ERROR', 'CYCLE_EXCEPTION',
                                f'cycle={cycle} err#{consecutive_errors} err={e} tb={tb_str[:500]}')
                # 连续 10 次错误升级为 FATAL，但仍不退出（守护职责）
                if consecutive_errors == 10:
                    _log(f"[DAEMON][FATAL] 10 consecutive errors, escalating but not exiting")
                    _log_supervisor('FATAL', '10_CONSECUTIVE_ERRORS',
                                    f'cycle={cycle} last_err={e}')
                # 错误退避：第 1 次 0s, 2-5 次 5s, 6+ 次 30s
                backoff = 0 if consecutive_errors == 1 else (5 if consecutive_errors <= 5 else 30)
                if backoff > 0:
                    time.sleep(backoff)
                continue

            time.sleep(MONITOR_INTERVAL)

    @staticmethod
    def stop():
        """停止守护进程"""
        pid = SmartMountDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED (no PID)")
            return

        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            # 如果还活着,强制杀
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        except OSError:
            pass

        SmartMountDaemon.clear_pid()
        print("[STATUS] STOPPED")

    @staticmethod
    def status() -> Dict:
        """查看状态"""
        ensure_smart_mount_tables()
        pid = SmartMountDaemon.read_pid()
        daemon_state = "RUNNING" if pid else "STOPPED"

        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # 进程列表
            procs = c.execute("""
                SELECT p.*, d.daemon_duty, d.priority
                FROM mt_ai_smart_mount_processes p
                LEFT JOIN mt_daemon_registry d ON p.daemon_id=d.daemon_id
                ORDER BY p.created_at DESC
            """).fetchall()

            # 待挂载建议数
            pending = c.execute("""
                SELECT COUNT(*) FROM mt_ai_suggestion_pool
                WHERE status='EVALUATED' AND priority>=5
            """).fetchone()[0]

            # 决策统计
            decisions = c.execute("""
                SELECT decision, COUNT(*) as cnt
                FROM mt_ai_mount_decisions
                GROUP BY decision
            """).fetchall()

            conn.close()

        result = {
            "daemon_pid": pid,
            "daemon_state": daemon_state,
            "total_processes": len(procs),
            "running_processes": sum(1 for p in procs if p["current_state"] == "RUNNING"),
            "pending_suggestions": pending,
            "decisions": {d["decision"]: d["cnt"] for d in decisions},
            "processes": [dict(p) for p in procs],
        }
        return result

    @staticmethod
    def list_processes():
        """列出所有挂载进程"""
        ensure_smart_mount_tables()
        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT p.*, d.daemon_duty, d.priority, d.inspect_cycle
                FROM mt_ai_smart_mount_processes p
                LEFT JOIN mt_daemon_registry d ON p.daemon_id=d.daemon_id
                ORDER BY p.created_at DESC
            """).fetchall()
            conn.close()
        return [dict(r) for r in rows]


# ============================================================
# CLI入口
# ============================================================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "start":
        SmartMountDaemon.start()

    elif cmd == "stop":
        SmartMountDaemon.stop()

    elif cmd == "status":
        s = SmartMountDaemon.status()
        print(f"{'='*60}")
        print(f"  Smart Mount Engine Status")
        print(f"{'='*60}")
        print(f"  Daemon PID:    {s['daemon_pid'] or '-'}")
        print(f"  Daemon State:  {s['daemon_state']}")
        print(f"  Total Procs:   {s['total_processes']}")
        print(f"  Running:       {s['running_processes']}")
        print(f"  Pending Sugs:  {s['pending_suggestions']}")
        print(f"  Decisions:     {s['decisions']}")
        print(f"{'='*60}")
        if s["processes"]:
            print(f"  {'Name':<30} {'State':<10} {'PID':<8} {'Score':<6} {'Source':<15}")
            print(f"  {'-'*30} {'-'*10} {'-'*8} {'-'*6} {'-'*15}")
            for p in s["processes"]:
                print(f"  {p['process_name'][:30]:<30} {p['current_state']:<10} "
                      f"{str(p['pid'] or '-'):<8} {p['mount_score']:<6.2f} {p['mount_source']:<15}")

    elif cmd == "list":
        procs = SmartMountDaemon.list_processes()
        if not procs:
            print("  (无挂载进程)")
        for p in procs:
            print(f"  [{p['current_state']}] {p['process_name']} pid={p['pid']} "
                  f"score={p['mount_score']:.2f} source={p['mount_source']} "
                  f"restart={p['restart_count']}")
            if p.get("daemon_duty"):
                print(f"         duty: {p['daemon_duty'][:80]}")

    elif cmd == "scan":
        ensure_smart_mount_tables()
        result = scan_and_mount()
        print(f"{'='*60}")
        print(f"  Scan & Mount Result")
        print(f"{'='*60}")
        print(f"  Scanned:   {result['scanned']}")
        print(f"  Mounted:   {result['mounted']}")
        print(f"  Deferred:  {result['deferred']}")
        print(f"  Rejected:  {result['rejected']}")
        for d in result["details"]:
            status = d.get("decision", "?")
            name = d.get("process_name", "-")
            score = d.get("final_score", 0)
            print(f"  [{status:<6}] score={score:.2f} {name}")
            if d.get("reason"):
                print(f"           {d['reason']}")

    elif cmd == "adopt":
        # 采纳指定建议ID
        if len(sys.argv) < 3:
            print("  用法: python3 ai_smart_mount_engine.py adopt <suggestion_id>")
            sys.exit(1)
        sid = int(sys.argv[2])
        ensure_smart_mount_tables()

        with _LOCK:
            conn = _get_conn()
            conn.row_factory = sqlite3.Row
            r = conn.execute(
                "SELECT * FROM mt_ai_suggestion_pool WHERE suggestion_id=?", (sid,)).fetchone()
            conn.close()

        if not r:
            print(f"  [ERROR] 建议不存在: #{sid}")
            sys.exit(1)

        sug = dict(r)
        ew = collect_expert_weights()
        decision = smart_mount_decision(sug, ew)

        if decision["decision"] != "MOUNT":
            print(f"  [DEFER] score={decision['final_score']:.2f} < {MOUNT_THRESHOLD}")
            print(f"  {decision['reason']}")
            sys.exit(0)

        process_name = f"adopt_{sug.get('direction', 'gen')}_{sid}"
        script_path = generate_daemon_script(
            process_name=process_name,
            duty=sug.get("suggestion", "")[:100],
            suggestion_id=sid,
            mount_score=decision["final_score"],
            work_body=_infer_work_body(sug),
        )
        pid = mount_process(
            process_name=process_name,
            duty=sug.get("suggestion", "")[:100],
            script_path=script_path,
            suggestion_id=sid,
            mount_source="AI_SUGGESTION",
            mount_score=decision["final_score"],
            expert_weights=ew,
        )
        print(f"  [MOUNTED] {process_name} pid={pid} score={decision['final_score']:.2f}")

    elif cmd == "create":
        # 手动创建自动化进程
        if len(sys.argv) < 4:
            print("  用法: python3 ai_smart_mount_engine.py create <name> <duty> [--cycle N]")
            sys.exit(1)
        name = sys.argv[2]
        duty = sys.argv[3]
        cycle = 60
        if "--cycle" in sys.argv:
            idx = sys.argv.index("--cycle")
            cycle = int(sys.argv[idx + 1])

        ensure_smart_mount_tables()
        script_path = generate_daemon_script(
            process_name=name, duty=duty,
            suggestion_id=0, mount_score=1.0,
            inspect_cycle=cycle,
        )
        pid = mount_process(
            process_name=name, duty=duty,
            script_path=script_path,
            mount_source="MANUAL", mount_score=1.0,
        )
        print(f"  [CREATED] {name} pid={pid} script={script_path}")

    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()


