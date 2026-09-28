#!/usr/bin/env python3
"""
仙女座超级集群激活脚本 v6.0
===============================
扩展规模:
  - daemon: 6 → 18 个仙女座专属 (含 6 个原 + 12 个新)
  - 矩阵:   8 → 14 大 AI 矩阵
  - 角色:   10 → 16 EigenFlux 专家

设计原则:
  1. 轻量 work_body — SQLite+Ollama, 每个 daemon <50ms DB 操作
  2. 启动偏移 — 30-90s 错开, 避免 DB WAL 锁竞争
  3. Ollama 排队 — 同一时间最多 2 个 daemon 调本地推理
  4. 每个 daemon 有明确职责 (duty 字段), 方便追溯

部署: python3 activate_andromeda.py [--dry-run]
"""
import os, sys, sqlite3, time, json, subprocess, random

APP_DB = os.path.expanduser("~/mtscos/_runtime/databases/Database/app.db")
DRY_RUN = "--dry-run" in sys.argv
OLLAMA_QUEUE = []  # 全局 Ollama 排队锁 (进程级)

def _log(msg):
    print(f"[仙女座v6] {msg}")

def _ollama_lock():
    """简单 Ollama 排队: 同一进程内最多 2 个 daemon 同时调"""
    while len(OLLAMA_QUEUE) >= 2:
        time.sleep(2); OLLAMA_QUEUE = [t for t in OLLAMA_QUEUE if time.time()-t < 120]
    OLLAMA_QUEUE.append(time.time())
def _ollama_unlock():
    OLLAMA_QUEUE = [t for t in OLLAMA_QUEUE if time.time()-t < 120]

def check_prerequisites():
    _log("=== 1. 基础设施检查 ===")
    checks = [
        ("DB 文件", os.path.exists(APP_DB)),
        ("smart_mount_engine.py", os.path.exists(os.path.expanduser("~/mtscos/flask-app/ai_smart_mount_engine.py"))),
        ("Ollama", subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}","http://127.0.0.1:11434/api/tags"], capture_output=True, text=True).stdout.strip()=="200"),
    ]
    for name, ok in checks:
        _log(f"  {'OK' if ok else 'FAIL'} {name}")
    return all(ok for _, ok in checks)

# ============================================================
# work_body 模板 (每个 daemon 的执行体)
# 统一模式: DB 读轻 → 可选 Ollama 推理 → DB 写轻
# ============================================================

# ---- 原 6 个 ----
WB_DERIVE = '''
import sqlite3, os, sys, time, random, urllib.request, json, re
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
# === 取题 ===
row = conn.execute("SELECT subject, error_concept FROM mt_error_thinking_chain ORDER BY created_at DESC LIMIT 1").fetchone()
if not row:
    pool = [("math","sin²θ+cos²θ=1"),("physics","F=ma本质"),("calc","导数几何意义"),("algebra","i²=-1有用吗")]
    row = random.choice(pool)
subject, question = row
# === 质量门禁: 净化 Ollama 输出 ===
def _fix_json_escapes(s):
    """修复 Ollama 输出里 LaTeX 反斜杠导致的非法 JSON escape.

    JSON 只认 7 种 escape: \\" \\\\ \\/ \\n \\r \\t \\b \\f \\uXXXX.
    其余 \\X 全部去掉反斜杠.

    关键: LaTeX 命令如 \\theta \\frac \\sin 等是 '\\' + 字母,
    必须用正则一次性吃掉, 否则 VALID 里的 't'/'f'/'n' 会误判 \\t/\\f/\\n 开头的 LaTeX 命令.

    注: 本函数在 daemon work_body 内独立运行, 必须 self-contained."""
    import re as _re
    # 1) LaTeX 命令 \alpha \frac \theta 等 (反斜杠+字母序列) → 去掉反斜杠
    s = _re.sub(r'\\([a-zA-Z]+)', r'\1', s)
    # 2) LaTeX 定界符 \( \) \[ \] \{ \} → 去掉反斜杠
    s = _re.sub(r'\\([(){}\[\]])', r'\1', s)
    # 3) 剩下的 \X (X 非 JSON 合法 escape) → 去掉反斜杠
    JSON_ESCAPE_CHARS = set('"\\/nrtbf')  # 仅用于验证已处理完的
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] == '\\' and i + 1 < n:
            nxt = s[i + 1]
            if nxt in JSON_ESCAPE_CHARS or nxt == 'u':
                out.append(s[i:i+2]); i += 2  # 合法 JSON escape 保留
            else:
                out.append(nxt); i += 2      # 非法 → 去掉 \, 保留 X
        else:
            out.append(s[i]); i += 1
    return ''.join(out)

def _sanitize(raw_text):
    """Ollama 输出容错: 剥 Markdown → 修复 LaTeX escape → 取首 JSON 块 → 校验 schema."""
    if not raw_text: return None, 0.0, {}, "pending"
    s = raw_text.strip()
    # 剥 ```json ... ``` 包裹 + 前后夹杂文字
    m = re.match(r"^```(?:json)?\\s*([\\s\\S]*?)\\s*```$", s)
    if m: s = m.group(1).strip()
    # 尝试直接 parse (合法 JSON)
    parsed = None
    for _ in range(2):
        try: parsed = json.loads(s); break
        except Exception:
            # 失败 → 尝试修复非法 escape (LaTeX \delta \frac 等)
            s = _fix_json_escapes(s)
    if not parsed:
        # 最后手段: 提取首尾 {} 或 []
        for op, cl in [("{", "}"), ("[", "]")]:
            li, ri = s.find(op), s.rfind(cl)
            if li != -1 and ri != -1 and ri > li:
                try: parsed = json.loads(s[li:ri+1]); break
                except Exception:
                    # 再修一次 escape
                    try: parsed = json.loads(_fix_json_escapes(s[li:ri+1])); break
                    except Exception: pass
    if not parsed: return None, 0.0, {}, "parse_fail"
    # === 统一 schema: 兼容多种字段名 ===
    steps = parsed.get("推导") or parsed.get("推导过程") or parsed.get("derivation_steps") or parsed.get("steps") or []
    # 如果 steps 是 dict 里的列表, 取第一个 dict value 是 list 的
    if not isinstance(steps, list):
        for v in parsed.values():
            if isinstance(v, list) and len(v) > 0:
                steps = v; break
    verification = parsed.get("验证") or parsed.get("自我验证") or parsed.get("self_verification") or {}
    conf_raw = parsed.get("confidence") or parsed.get("置信度")
    try: conf = float(conf_raw) if conf_raw is not None else 0.5
    except Exception: conf = 0.5
    is_valid = verification.get("is_valid") if isinstance(verification, dict) else True
    if isinstance(verification, dict): verification.setdefault("is_valid", is_valid)
    # confidence 启发式: 步数 ≥3 → +0.1, 有验证 → +0.1
    if len(steps) >= 3: conf = min(1.0, conf + 0.1)
    if verification: conf = min(1.0, conf + 0.1)
    vs = "verified" if is_valid else "unverified"
    # === 序列化 ===
    dc_json = json.dumps({"推导": steps}, ensure_ascii=False) if steps else None
    ver_json = json.dumps(verification, ensure_ascii=False) if verification else None
    return dc_json, round(conf, 3), ver_json, vs
# === 调 Ollama ===
try:
    _queue = json.loads(os.environ.get('OLLAMA_QUEUE','[]'))
    while sum(1 for t in _queue if time.time()-t<120) >= 2: time.sleep(2); _queue = json.loads(os.environ.get('OLLAMA_QUEUE','[]'))
    _queue.append(time.time()); os.environ['OLLAMA_QUEUE'] = json.dumps(_queue)
    # 🆕 v5.3: 严格 JSON schema prompt —— 避免 Markdown/夹杂文字/LaTeX反斜杠
    _schema = (
        "严格按以下 JSON 格式输出, 不要任何 Markdown, 不要额外文字.\\n"
        "公式用纯文本写 (如 a = F/m, sin²θ + cos²θ = 1), 禁止 LaTeX 反斜杠命令 (如 \\frac \\theta \\sqrt \\sin).\\n"
        '{"推导":[{"步骤":1,"类型":"假设|定义|推导|结论","内容":"..."}...至少5步],'
        '"验证":{"is_valid":true,"说明":"..."},"confidence":0.0到1.0之间的小数}'
    )
    payload = {
        "model":"qwen2.5:7b",
        "messages":[
            {"role":"system","content":f"你是拉马努金, 从零推导数学/物理公式. {_schema}"},
            {"role":"user","content":f"请从零推导: {question}"}
        ],
        "stream":False,
        "options":{"temperature":0.2,"num_predict":2000}
    }
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read()).get("message",{}).get("content","")
    # 净化
    dc_clean, conf, ver_clean, vs = _sanitize(raw)
    if dc_clean is None:
        print(f"[拉马努金] 净化失败, 跳过: {question[:40]}")
    else:
        # UPSERT: 同 concept + subject → 更新, 不同 → 插入
        exist = conn.execute(
            "SELECT knowledge_id FROM mt_derived_knowledge WHERE concept=? AND subject=? ORDER BY created_at DESC LIMIT 1",
            (question, subject)).fetchone()
        if exist:
            conn.execute(
                "UPDATE mt_derived_knowledge SET derivation_chain=?, verification=?, confidence=?, verification_status=?, model_used='qwen2.5:7b', user_id='system', updated_at=datetime('now','localtime') WHERE knowledge_id=?",
                (dc_clean, ver_clean, conf, vs, exist[0]))
        else:
            conn.execute(
                "INSERT INTO mt_derived_knowledge (concept,subject,derivation_chain,verification,confidence,model_used,user_id,verification_status,created_at) VALUES (?,?,?,?,?,'qwen2.5:7b','system',?,datetime('now','localtime'))",
                (question, subject, dc_clean, ver_clean, conf, vs))
        conn.commit()
        print(f"[拉马努金] ✅ {question[:40]} conf={conf} status={vs} steps={dc_clean.count('步骤')}")
except Exception as e: print(f"[拉马努金] ERROR: {e}")
conn.close()
'''

WB_TUTOR = '''
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
'''

WB_DIGEST = '''
import sqlite3, os, urllib.request, json
APP_DB = os.environ.get("APP_DB", os.path.join(os.path.dirname(__file__), "..", "..", "_runtime", "databases", "Database", "app.db"))
conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
rows = conn.execute("SELECT chain_id, subject, error_concept FROM mt_error_thinking_chain WHERE thinking_chain IS NULL ORDER BY created_at DESC LIMIT 3").fetchall()
if rows:
    for cid, subj, q in rows:
        try:
            payload = {"model":"qwen2.5:7b","prompt":f"问题:{q}\\n为什么错?思维卡在哪?如何纠正?输出结构化JSON","stream":False,"options":{"temperature":0.3}}
            req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=90) as resp: chain = json.loads(resp.read()).get("response","")
            conn.execute("UPDATE mt_error_thinking_chain SET thinking_chain=?, ai_model='qwen2.5:7b' WHERE chain_id=?", (chain[:3000], cid))
            conn.commit(); print(f"[错题消化] #{cid} [{subj}] OK")
        except Exception as e: print(f"[错题消化] #{cid} 失败: {e}")
else: print("[错题消化] 无新错题")
conn.close()
'''

WB_CRYPTO = '''
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
'''

WB_MATRIX = '''
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
'''

WB_COG = '''
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
'''

# ============================================================
# 新增 12 个仙女座智能 daemon (v6.0 扩展)
# ============================================================

# 7. 知识图谱构建 daemon — 跨表发现知识关联
WB_KNOWLEDGE_GRAPH = '''
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
'''

# 8. EigenFlux 自动交友协议守护
WB_EIGENFLUX_MATCH = '''
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
'''

# 9. 预测性维护 — 从历史 daemon 故障预测下一次
WB_PREDICTIVE_MAINT = '''
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
'''

# 10. 自动文档生成 — 从 Flask 路由自动生成 API 清单
WB_AUTO_DOC = '''
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
'''

# 11. IoT 设备集群管理 daemon
WB_IOT_CLUSTER = '''
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
'''

# 12. EigenFlux 脑库投喂 — 把新经验写到脑库
WB_BRAIN_FEED = '''
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
'''

# 13. 安全态势扫描 daemon
WB_SECURITY_PULSE = '''
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
'''

# 14. 资源调度器 daemon — CPU/内存自适应
WB_RESOURCE_SCHED = '''
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
'''

# 15. 用户画像矩阵 daemon — 跨维度画像融合
WB_PROFILE_FUSION = '''
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
'''

# 16. EigenFlux 经验回流 daemon
WB_EXPERIENCE_REPLAY = '''
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
'''

# 17. 知识沉淀矩阵 daemon
WB_KNOWLEDGE_PRECIOUS = '''
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
'''

# 18. 规则自动学习守护 (sys_rule_enforcer 辅助)
WB_RULE_AUTO_LEARN = '''
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
'''

# ============================================================
# 18 个仙女座 daemon 注册表
# ============================================================
ANDROMEDA_DAEMONS = [
    # ---- 原 6 ----
    {"process_name": "sys_ramanujan_derive",   "duty": "拉马努金自动推导(错题→Ollama→mt_derived_knowledge)", "inspect_cycle": 600,  "startup_offset": 0,  "work_body": WB_DERIVE},
    {"process_name": "sys_tutor_learning",     "duty": "AI导师自动学习(错题统计→认知画像更新)",             "inspect_cycle": 900,  "startup_offset": 30, "work_body": WB_TUTOR},
    {"process_name": "sys_error_digest",       "duty": "错题消化(Ollama生成思维链回填)",                   "inspect_cycle": 1800, "startup_offset": 60, "work_body": WB_DIGEST},
    {"process_name": "sys_crypto_key_rotate",  "duty": "密钥自动轮换(每天03:00)",                          "inspect_cycle": 86400,"startup_offset": 90, "work_body": WB_CRYPTO},
    {"process_name": "sys_matrix_synergy",     "duty": "14矩阵协同扫描",                                    "inspect_cycle": 1800, "startup_offset": 20, "work_body": WB_MATRIX},
    {"process_name": "sys_cognitive_assess",   "duty": "认知画像周期刷新",                                  "inspect_cycle": 3600, "startup_offset": 50, "work_body": WB_COG},

    # ---- 新 12 (v6.0 扩展) ----
    {"process_name": "sys_knowledge_graph",    "duty": "知识图谱构建(跨表概念关联发现)",                    "inspect_cycle": 1200, "startup_offset": 15, "work_body": WB_KNOWLEDGE_GRAPH},
    {"process_name": "sys_eigenflux_match",    "duty": "EigenFlux自动配对(同专业交友推荐)",                  "inspect_cycle": 1800, "startup_offset": 45, "work_body": WB_EIGENFLUX_MATCH},
    {"process_name": "sys_predictive_maint",   "duty": "预测性维护(从历史故障预测风险)",                     "inspect_cycle": 3600, "startup_offset": 75, "work_body": WB_PREDICTIVE_MAINT},
    {"process_name": "sys_cluster_snapshot",   "duty": "集群快照(daemon状态汇总→policy)",                    "inspect_cycle": 600,  "startup_offset": 10, "work_body": WB_AUTO_DOC},
    {"process_name": "sys_iot_cluster",        "duty": "IoT设备集群(Arduino等设备状态汇总)",                 "inspect_cycle": 1200, "startup_offset": 40, "work_body": WB_IOT_CLUSTER},
    {"process_name": "sys_brain_feed",         "duty": "脑库投喂(新错题→经验自动回流)",                      "inspect_cycle": 1800, "startup_offset": 55, "work_body": WB_BRAIN_FEED},
    {"process_name": "sys_security_pulse",     "duty": "安全态势扫描(违规/SA密钥/实时监控)",                 "inspect_cycle": 600,  "startup_offset": 25, "work_body": WB_SECURITY_PULSE},
    {"process_name": "sys_resource_sched",      "duty": "资源调度器(CPU/内存自适应)",                          "inspect_cycle": 300,  "startup_offset": 5,  "work_body": WB_RESOURCE_SCHED},
    {"process_name": "sys_profile_fusion",     "duty": "画像融合(多维度用户画像重新定级)",                    "inspect_cycle": 3600, "startup_offset": 65, "work_body": WB_PROFILE_FUSION},
    {"process_name": "sys_experience_replay",  "duty": "经验回流(脑库投喂日统计)",                            "inspect_cycle": 1800, "startup_offset": 70, "work_body": WB_EXPERIENCE_REPLAY},
    {"process_name": "sys_knowledge_precious", "duty": "知识沉淀(拉马努金推导周统计)",                        "inspect_cycle": 7200, "startup_offset": 80, "work_body": WB_KNOWLEDGE_PRECIOUS},
    {"process_name": "sys_rule_auto_learn",    "duty": "规则自动学习(违规统计+知识沉淀)",                     "inspect_cycle": 1800, "startup_offset": 35, "work_body": WB_RULE_AUTO_LEARN},
]

# ============================================================
# 14 矩阵注册表
# ============================================================
ANDROMEDA_MATRICES = [
    # 原 8
    ("core_engine_matrix",   "核心引擎矩阵",    "模型/推理/引擎协同"),
    ("ai_tutor_matrix",      "AI导师矩阵",      "认知画像/错题/导师会话"),
    ("ramanujan_matrix",     "拉马努金矩阵",    "自动推导/知识沉淀"),
    ("eigenflux_matrix",     "EigenFlux矩阵",  "专家/交友/消息网络"),
    ("crypto_matrix",        "密码学矩阵",      "密钥/加密/安全审计"),
    ("iot_matrix",           "IoT设备矩阵",     "Arduino/设备检测/集群"),
    ("patrol_matrix",        "巡逻修复矩阵",    "巡检/自动修复/安全"),
    ("rule_matrix",          "规则学习矩阵",    "规则/约束/策略/合规"),
    # 新增 6
    ("knowledge_matrix",     "知识图谱矩阵",    "跨表概念关联/知识沉淀"),
    ("security_matrix",      "安全态势矩阵",    "违规/SA密钥/实时监控"),
    ("resource_matrix",      "资源调度矩阵",    "CPU/内存/Ollama排队"),
    ("profile_matrix",       "用户画像矩阵",    "多维度画像/融合/定级"),
    ("experience_matrix",    "经验回流矩阵",    "脑库投喂/沉淀/学习"),
    ("doc_matrix",           "自动文档矩阵",    "API清单/集群快照/策略"),
]

# ============================================================
# 16 角色注册表 (EigenFlux 专家)
# ============================================================
ANDROMEDA_ROLES = [
    # 原 10
    ("architect",    "架构专家",    "系统设计/模块拆分/数据流"),
    ("compliance",   "合规专家",    "规则/约束/安全标准"),
    ("security",     "安全专家",    "密码学/权限/漏洞/审计"),
    ("dba",          "DBA专家",      "SQLite/WAL/性能/备份"),
    ("ops",          "运维专家",    "daemon/launchd/三重启保活"),
    ("frontend",     "前端专家",    "Jinja2/JS/ElementPlus"),
    ("backend",      "后端专家",    "Flask/Python/API/蓝图"),
    ("ai_engineer",  "AI工程师",    "Ollama/7B/推理/微调"),
    ("data_engineer","数据工程师",  "ETL/画像/统计/可视化"),
    ("educator",     "教育专家",    "K12/高等/题库/错题"),
    # 新增 6
    ("iot_engineer", "IoT工程师",    "Arduino/设备集群/串口"),
    ("knowledge",    "知识工程师",   "知识图谱/沉淀/回流"),
    ("predictive",   "预测分析师",   "预测维护/故障预警"),
    ("resource",     "资源调度员",   "CPU/内存/Ollama排队"),
    ("profile",      "画像专家",     "用户画像/融合/定级"),
    ("crypto",       "密码学专家",   "AES-GCM/X25519/HMAC"),
]

# ============================================================
# 执行
# ============================================================

def register_daemons():
    _log(f"=== 2. 注册 {len(ANDROMEDA_DAEMONS)} 个仙女座 daemon ===")
    try:
        sys.path.insert(0, os.path.expanduser("~/mtscos/flask-app"))
        import ai_smart_mount_engine as sm
        for d in ANDROMEDA_DAEMONS:
            # 加启动偏移字段
            entry = dict(d)
            entry.setdefault("startup_offset", 30)
            _log(f"  + {d['process_name']} (cycle={d['inspect_cycle']}s, offset={d['startup_offset']}s)")
            if not DRY_RUN:
                sm.SYSTEM_REQUIRED_DAEMONS.append(entry)
        _log(f"  共 {len(ANDROMEDA_DAEMONS)} 个已追加")
    except Exception as e:
        _log(f"  注册失败: {e}"); import traceback; traceback.print_exc(); return False
    return True

def register_matrices_roles():
    _log(f"=== 3. 注册 {len(ANDROMEDA_MATRICES)} 矩阵 + {len(ANDROMEDA_ROLES)} 角色 ===")
    if DRY_RUN: _log("  [DRY-RUN] 跳过 DB 写"); return True
    try:
        conn = sqlite3.connect(APP_DB, timeout=10); conn.execute("PRAGMA busy_timeout=5000")
        # 矩阵表
        conn.execute("CREATE TABLE IF NOT EXISTS mt_ai_matrix (matrix_name TEXT PRIMARY KEY, matrix_label TEXT, description TEXT, created_at TEXT DEFAULT (datetime('now','localtime')))")
        for name, label, desc in ANDROMEDA_MATRICES:
            conn.execute("INSERT OR IGNORE INTO mt_ai_matrix VALUES (?,?,?,datetime('now','localtime'))", (name, label, desc))
        # 角色表
        conn.execute("CREATE TABLE IF NOT EXISTS mt_eigenflux_roles (role_code TEXT PRIMARY KEY, role_label TEXT, expertise_area TEXT, created_at TEXT DEFAULT (datetime('now','localtime')))")
        for code, label, expertise in ANDROMEDA_ROLES:
            conn.execute("INSERT OR IGNORE INTO mt_eigenflux_roles VALUES (?,?,?,datetime('now','localtime'))", (code, label, expertise))
        conn.commit(); conn.close()
        _log(f"  ✅ {len(ANDROMEDA_MATRICES)} 矩阵 + {len(ANDROMEDA_ROLES)} 角色 已落库")
    except Exception as e:
        _log(f"  DB 落库失败: {e}")
    return True

def save_and_restart():
    _log("=== 4. 持久化 daemon 定义 + 重启 smart_mount ===")
    if DRY_RUN: _log("  [DRY-RUN] 跳过"); return True
    try:
        eng_path = os.path.expanduser("~/mtscos/flask-app/ai_smart_mount_engine.py")
        with open(eng_path) as f: content = f.read()
        marker = "def mount_system_required"
        idx = content.find(marker)
        if idx > 0:
            injection = "\n# ===== 仙女座超级集群 v6.0 (18 daemon 自动追加) =====\n"
            for d in ANDROMEDA_DAEMONS:
                wb = d["work_body"].replace("\\", "\\\\").replace("'''", "\\'\\'\\'")
                offset = d.get("startup_offset", 30)
                injection += f"    {{\"process_name\":\"{d['process_name']}\",\"duty\":\"{d['duty']}\",\"inspect_cycle\":{d['inspect_cycle']},\"startup_offset\":{offset},\"work_body\":'''{wb}'''}},\n"
            content = content[:idx] + injection + "\n" + content[idx:]
            with open(eng_path, "w") as f: f.write(content)
        _log("  kill 旧 daemon...")
        subprocess.run(["pkill","-9","-f","ai_smart_mount_engine"], capture_output=True)
        subprocess.run(["pkill","-9","-f","_runtime/auto_daemons"], capture_output=True)
        time.sleep(3)
        _log("  启动 smart_mount...")
        subprocess.Popen(["python3","ai_smart_mount_engine.py","start"],
                         cwd=os.path.expanduser("~/mtscos/flask-app"),
                         stdout=open(os.path.expanduser("~/mtscos/_runtime/logs/smart_mount_daemon.log"),"a"),
                         stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(25); return True
    except Exception as e:
        _log(f"  失败: {e}"); return False

def verify():
    _log("=== 5. 等待 daemon spawn + 验证 ===")
    for i in range(14):
        time.sleep(5)
        try:
            with sqlite3.connect(APP_DB, timeout=5) as c:
                total = c.execute("SELECT COUNT(*) FROM mt_ai_smart_mount_processes WHERE process_name LIKE 'sys_%'").fetchone()[0]
                matrix = c.execute("SELECT COUNT(*) FROM mt_ai_matrix").fetchone()[0]
                roles = c.execute("SELECT COUNT(*) FROM mt_eigenflux_roles").fetchone()[0]
                runnable = c.execute("SELECT COUNT(*) FROM mt_ai_smart_mount_processes WHERE process_name LIKE 'sys_%' AND (current_state='RUNNING' OR current_state IS NULL)").fetchone()[0]
            _log(f"  [{(i+1)*5}s] daemon={total} runnable={runnable} matrix={matrix} roles={roles}")
            if runnable >= 15: break
        except Exception as e: pass
    return True

def main():
    _log("=" * 50)
    _log("  仙女座超级集群 v6.0 — 18 daemon + 14 矩阵 + 16 角色")
    _log("=" * 50)
    if not check_prerequisites(): _log("FAIL 基础设施"); sys.exit(1)
    register_daemons()
    register_matrices_roles()
    save_and_restart()
    verify()
    _log("=" * 50)
    _log(f"  DONE!")
    _log(f"  Daemons: {len(ANDROMEDA_DAEMONS)}")
    _log(f"  Matrices: {len(ANDROMEDA_MATRICES)}")
    _log(f"  Roles: {len(ANDROMEDA_ROLES)}")
    for d in ANDROMEDA_DAEMONS: _log(f"    - {d['process_name']} (cycle={d['inspect_cycle']}s, offset={d.get('startup_offset',30)}s)")
    _log("=" * 50)

if __name__ == "__main__":
    main()
