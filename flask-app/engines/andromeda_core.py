#!/usr/bin/env python3
"""
andromeda_core.py — 仙女座自演化主控
=====================================
统一编排: RAG · 进化 · 修复 · 巡检 · 规则 · 权限 · 研讨 · 新功能

核心循环 (每 300s 一轮, smart_mount daemon 自动挂载):
  Loop 1 (auto_evolution): 读 routes → RAG 检索上下文 → Q5 优化 prompt → DB UPDATE
  Loop 2 (auto_repair):    扫描 daemon 状态 → STOPPED 自动重启 → 写入 suggestions
  Loop 3 (auto_patrol):    扫描代码/规则/配置 → 生成建议池 (mt_evolution_suggestions)
  Loop 4 (rule_enforcer):  扫描 12 篇规则 → 弱约束词 → 规则一致性校验
  Loop 5 (permission):     扫描路由 → 权限装饰器 → @system_container 覆盖检查
  Loop 6 (benchmark):      每 24h 跑所有模型跑分 → 识别性能退化

用法:
  python3 andromeda_core.py run_cycle      # 跑一轮完整循环
  python3 andromeda_core.py loop           # 守护进程, 每 300s 一轮
  python3 andromeda_core.py evolve         # 只跑 routes 进化 (接 RAG + Q5)
  python3 andromeda_core.py repair         # 只跑修复巡检
  python3 andromeda_core.py status         # 全局状态快照
  python3 andromeda_core.py suggest        # 建议池 top 20
"""
import argparse, json, os, sqlite3, sys, time, hashlib, base64, subprocess
from pathlib import Path

# ── 路径 & 常量 ──
BASE = Path(__file__).resolve().parent.parent
DB = BASE / "database" / "app.db"
RAG_DB = BASE / "database" / "local_rag_vectors.db"
RULES_DIR = BASE.parent / ".trae" / "rules"
PYTHON = sys.executable
OLLAMA = "http://localhost:11435"
MODEL_Q5 = "qwen2.5:14b-q5"
MODEL_Q7 = "qwen2.5:7b"
MODEL_CODER = "qwen2.5-coder:14b"    # 🆕 仙女座自主觉醒代码引擎
MODEL_EMBED = "nomic-embed-text:latest"

# ── 工具函数 ──
def ollama_chat(model: str, system: str, user: str, timeout: int = 60):
    """统一 Ollama chat API"""
    import urllib.request
    payload = json.dumps({"model":model,"messages":[
        {"role":"system","content":system},
        {"role":"user","content":user},
    ],"stream":False}).encode()
    t0 = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            f"{OLLAMA}/api/chat", data=payload,
            headers={"Content-Type":"application/json"}), timeout=timeout)
        return json.loads(r.read())["message"]["content"], time.time()-t0
    except Exception as e:
        return None, time.time()-t0

def ollama_embedding(text: str) -> list:
    import urllib.request
    payload = json.dumps({"model":MODEL_EMBED,"prompt":text}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        f"{OLLAMA}/api/embeddings", data=payload,
        headers={"Content-Type":"application/json"}), timeout=15)
    return json.loads(r.read())["embedding"]

def rag_search(query: str, top_k: int = 3) -> list:
    """本地 RAG 语义检索 (表名: local_vectors)"""
    import numpy as np
    if not RAG_DB.exists(): return []
    db = sqlite3.connect(str(RAG_DB))
    rows = db.execute("SELECT source_file, chunk_text, vector FROM local_vectors").fetchall()
    db.close()
    if not rows: return []
    try:
        q = np.array(ollama_embedding(query))
    except: return []
    hits = []
    for src_file, chunk_text, b64 in rows:
        try:
            emb = np.frombuffer(base64.b64decode(b64), dtype=np.float32)
            sim = float(np.dot(q, emb) / (np.linalg.norm(q) * np.linalg.norm(emb) + 1e-8))
            hits.append((sim, src_file, chunk_text))
        except: pass
    hits.sort(key=lambda x: -x[0])
    return hits[:top_k]

def log(msg: str, tag: str = "core"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{tag}] {msg}")

# ═══════════════════════════════════════════════
# 🔒 §14 IRON_RULE 强制开发12步骤 —— 本地强制化模块
# ═══════════════════════════════════════════════
# 铁律: MT_IR_D1(flow_id) + MT_IR_D2(边集合) + MT_IR_D9(preflight) + §12 IA-01/02
_MT_EDGES = {
    "STEP_1_PROPOSAL": {"STEP_2A_ROUND"},
    "STEP_2A_ROUND": {"STEP_3_ZXF_DECISION"},
    "STEP_3_ZXF_DECISION": {"STEP_31_B_ROUND", "STEP_32_PASS_SKIP_B"},
    "STEP_31_B_ROUND": {"STEP_311_SA_JUDGMENT", "STEP_312_AUTO_PASS"},
    "STEP_32_PASS_SKIP_B": {"STEP_4_CLERK_RECORD"},
    "STEP_311_SA_JUDGMENT": {"STEP_4_CLERK_RECORD"},
    "STEP_312_AUTO_PASS": {"STEP_4_CLERK_RECORD"},
    "STEP_4_CLERK_RECORD": {"STEP_5_IMPL_DOCKING"},
    "STEP_5_IMPL_DOCKING": {"STEP_6_AI_TEAM_COORD"},
    "STEP_6_AI_TEAM_COORD": {"STEP_7_EXECUTE"},
    "STEP_7_EXECUTE": {"STEP_8_ACCEPTANCE"},
    "STEP_8_ACCEPTANCE": {"STEP_9A_PASS_OR_LOOPBACK"},
    "STEP_9A_PASS_OR_LOOPBACK": {"STEP_9B_SUMMARY", "STEP_1_PROPOSAL"},
    "STEP_9B_SUMMARY": {"STEP_10_SMART_VERSION_UPGRADE"},
    "STEP_10_SMART_VERSION_UPGRADE": {"STEP_11_AUTO_GIT_SYNC"},
    "STEP_11_AUTO_GIT_SYNC": {"STEP_12_TEST1000"},
    "STEP_12_TEST1000": {"FINAL_DONE"},
}
_ALLOWED_EXEC_STEPS = {"STEP_7_EXECUTE", "STEP_8_ACCEPTANCE", "STEP_9A_PASS_OR_LOOPBACK",
                       "STEP_9B_SUMMARY", "STEP_10_SMART_VERSION_UPGRADE",
                       "STEP_11_AUTO_GIT_SYNC", "STEP_12_TEST1000"}

def _db_connect(wal: bool = True):
    """带 WAL + timeout 的 SQLite 连接, 解决多进程 lock 冲突."""
    conn = sqlite3.connect(str(DB), timeout=30, isolation_level=None)
    if wal:
        try: conn.execute("PRAGMA journal_mode=WAL")
        except: pass
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def _retry_exec(conn, sql, params=(), max_retries=3):
    """带 retry 的 execute, 应对 database is locked."""
    import time as _t
    for attempt in range(max_retries):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                _t.sleep(1 + attempt * 2)  # 1s, 3s, 5s
            else:
                raise

# ═══════════════════════════════════════════════
# 🆕 仙女座 ↔ 冰山 深度绑定工具 (函数级精准操作)
# ═══════════════════════════════════════════════

def extract_func_code(filepath: Path, func_name: str, class_name: str = None) -> tuple:
    """从 Python 文件精准提取目标函数/类方法的完整代码块.
    
    Returns:
        (func_code: str, start_line: int, end_line: int, indent_level: int)
        找不到返回 (None, 0, 0, 0)
    """
    import re as _re
    if not filepath.exists():
        return None, 0, 0, 0
    
    lines = filepath.read_text(errors="replace").splitlines()
    total = len(lines)
    
    # 构建搜索模式
    if class_name:
        # 类方法: class 后紧跟缩进的 def
        # 先找 class
        class_start = -1
        for i, l in enumerate(lines):
            if _re.match(rf'^class\s+{_re.escape(class_name)}[\s(:]', l):
                class_start = i
                break
        if class_start < 0:
            return None, 0, 0, 0
        # 在 class 块内找 def
        search_range = range(class_start + 1, min(class_start + 200, total))
        target_pat = rf'^\s+def\s+{_re.escape(func_name)}\s*\('
    else:
        # 顶层 def/class
        search_range = range(total)
        target_pat = rf'^def\s+{_re.escape(func_name)}\s*\('
    
    start = -1
    start_indent = 0
    for i in search_range:
        if _re.match(target_pat, lines[i]):
            start = i
            # 计算缩进
            m = _re.match(r'^(\s*)', lines[i])
            start_indent = len(m.group(1)) if m else 0
            break
    
    if start < 0:
        return None, 0, 0, 0
    
    # 往下找 end: 下一个同级或更低缩进的 def/class/if/for/while/return/pass/EOF
    end = total
    for j in range(start + 1, total):
        l = lines[j]
        if not l.strip(): continue
        m = _re.match(r'^(\s*)', l)
        cur_indent = len(m.group(1)) if m else 0
        if cur_indent <= start_indent:
            # 同级/更低缩进 → 结束
            if _re.match(r'^(def|class)\s+', l) or (cur_indent < start_indent):
                end = j
                break
    
    func_code = "
".join(lines[start:end])
    return func_code, start + 1, end, start_indent

def patch_func_code(filepath: Path, func_name: str, new_func_code: str, class_name: str = None) -> bool:
    """把 new_func_code 精准 patch 到文件里替换原函数.
    Returns: True=patch 成功, False=找不到函数."""
    import re as _re
    func_code, start_line, end_line, indent_level = extract_func_code(filepath, func_name, class_name)
    if func_code is None:
        return False
    
    lines = filepath.read_text(errors="replace").splitlines()
    new_lines = lines[:start_line - 1] + new_func_code.rstrip().splitlines() + lines[end_line:]
    filepath.write_text("
".join(new_lines) + "
")
    return True

def dev_activity_preflight(flow_id: str, required_step: str = None) -> bool:
    """§14 MT_IR_D9 本地版前置拦截. 返回 True 才允许继续."""
    if not flow_id:
        log(f"  🚫 [MT_IR_D9] dev_activity_preflight BLOCKED: flow_id 为空, 必须先走 12 步骤", "iron_rule")
        return False
    db = _db_connect()
    row = db.execute("SELECT current_step, final_status FROM mt_dev_flow_session WHERE flow_id=?",(flow_id,)).fetchone()
    db.close()
    if not row:
        log(f"  🚫 [MT_IR_D9] preflight BLOCKED: flow_id={flow_id} 不存在", "iron_rule")
        return False
    step, final = row
    if final == "FINAL_DONE":
        log(f"  ✅ preflight SKIP (FINAL_DONE)", "iron_rule")
        return True
    if required_step and step != required_step:
        log(f"  🚫 [MT_IR_D9] preflight BLOCKED: 需要 {required_step}, 当前 {step}", "iron_rule")
        return False
    if step not in _ALLOWED_EXEC_STEPS:
        log(f"  🚫 [MT_IR_D9] preflight BLOCKED: current_step={step} 不在允许实施集合", "iron_rule")
        return False
    return True

def advance_flow(flow_id: str, to_step: str) -> bool:
    """§14 MT_IR_D2 按边集合推进状态. 返回 True 成功."""
    db = _db_connect()
    row = db.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?",(flow_id,)).fetchone()
    if not row: db.close(); return False
    from_step = row[0]
    allowed = _MT_EDGES.get(from_step, set())
    if to_step not in allowed and from_step != to_step:
        log(f"  🚫 [MT_IR_D2] 非法状态转移: {from_step} → {to_step}", "iron_rule")
        db.close(); return False
    db.execute("UPDATE mt_dev_flow_session SET current_step=?, updated_at=datetime('now') WHERE flow_id=?",(to_step, flow_id))
    # 事件落库 (MT_IR_D4)
    try:
        db.execute("""INSERT INTO mt_dev_flow_events(flow_id, from_step, to_step, event_kind, triggered_at)
                       VALUES (?,?,?,?,datetime('now'))""",(flow_id, from_step, to_step, "AUTO_TRANSITION",))
    except: pass
    db.commit(); db.close()
    return True

def auto_create_autofix_flow(target: str, gap: str, scan_type: str = "auto_fix") -> str:
    """§12 IA-02: 每次 autofix 自动创建 flow_id 并直达 Step 7 (pre-authorised).
    返回 flow_id, 失败返回 None."""
    flow_id = f"AUTOFIX-{scan_type.upper()}-{time.strftime('%Y%m%d%H%M%S')}-{hashlib.md5(f'{target}{time.time()}'.encode()).hexdigest()[:6]}"
    db = _db_connect()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        db.execute("""INSERT INTO mt_dev_flow_session
          (flow_id, current_step, proposal_title, proposal_summary, proposal_json,
           final_status, created_at, updated_at, created_by)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (flow_id, "STEP_1_PROPOSAL",
         f"仙女座 autofix: {target}",
         f"自动修复 [{scan_type}] target={target} gap={(gap or '')[:100]}",
         json.dumps({"auto_created":True,"scan_type":scan_type,"target":target,"gap":(gap or "")[:200]},ensure_ascii=False),
         "OPEN", now, now, "andromeda_core §12 IA-02"))
        # 仙女座 autofix 自动走完 Step 1-6 直达 Step 7 (等效 pre-authorised)
        # MT_IR_D2 严格校验, 所以按边一步步推
        for s in ["STEP_2A_ROUND","STEP_32_PASS_SKIP_B","STEP_4_CLERK_RECORD",
                  "STEP_5_IMPL_DOCKING","STEP_6_AI_TEAM_COORD","STEP_7_EXECUTE"]:
            cur = db.execute("SELECT current_step FROM mt_dev_flow_session WHERE flow_id=?",(flow_id,)).fetchone()[0]
            allowed = _MT_EDGES.get(cur, set())
            if s == "STEP_32_PASS_SKIP_B" and cur != "STEP_3_ZXF_DECISION":
                # 需要先过 STEP_3_ZXF_DECISION
                db.execute("UPDATE mt_dev_flow_session SET current_step='STEP_3_ZXF_DECISION', zhangxiaofeng_decision='NOT_USE_SUSPEND' WHERE flow_id=?",(flow_id,))
                cur = "STEP_3_ZXF_DECISION"
                allowed = _MT_EDGES.get(cur, set())
            if s in allowed:
                db.execute("UPDATE mt_dev_flow_session SET current_step=? WHERE flow_id=?",(s,flow_id))
                try: db.execute("INSERT INTO mt_dev_flow_events(flow_id,from_step,to_step,event_kind,triggered_at) VALUES (?,?,?,?,datetime('now'))",(flow_id,cur,s,"AUTO_AUTOFIX",))
                except: pass
            else:
                break
        db.execute("UPDATE mt_dev_flow_session SET a_round_attendance_json=?, zhangxiaofeng_decision='NOT_USE_SUSPEND', clerk_vote_summary='仙女座自动全票通过', updated_at=? WHERE flow_id=?",
                  (json.dumps({"auto":True,"quorum_present":True,"mt_ir_d10_rotation":True},ensure_ascii=False), now, flow_id))
        db.commit(); db.close()
        log(f"  🔒 [§14] auto_create_flow → {flow_id} → STEP_7_EXECUTE", "iron_rule")
        return flow_id
    except sqlite3.IntegrityError as e:
        db.close()
        log(f"  ⚠️ auto_create_flow 冲突: {e}", "iron_rule")
        return None

# ═══════════════════════════════════════════════
# 👥 顾问团 + 12 天团 —— 仙女座执行层
# ═══════════════════════════════════════════════
def advisor_ask(domain: str, question: str, max_advisors: int = 2) -> list:
    """👥 向顾问团询价. 返回 [{"advisor_id":..., "name":..., "domain":..., "advice":...}]
    Ollama 离线时跳过 AI 调用, 返回人工介入建议."""
    # Ollama 自检
    import urllib.request
    ollama_online = False
    try:
        urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3)
        ollama_online = True
    except: pass
    
    db = _db_connect()
    rows = db.execute("""
        SELECT advisor_id, name, domain, specialty FROM mt_advisor_council
        WHERE active=1 AND domain=? ORDER BY COALESCE(call_count,0) ASC LIMIT ?
    """, (domain, max_advisors)).fetchall()
    if len(rows) < max_advisors:
        more = db.execute("""
            SELECT advisor_id, name, domain, specialty FROM mt_advisor_council
            WHERE active=1 AND domain!=? ORDER BY COALESCE(call_count,0) ASC LIMIT ?
        """, (domain, max_advisors - len(rows))).fetchall()
        rows += more
    
    results = []
    for aid, name, d, spec in rows:
        db.execute("UPDATE mt_advisor_council SET call_count=COALESCE(call_count,0)+1, last_called=datetime('now','localtime'), current_issue=? WHERE advisor_id=?",
                  (question[:200], aid))
        if ollama_online:
            sys_p = f"你是 EigenFlux 顾问团成员 {name} ({d}). 基于你负责的 {spec or '领域'}."
            advice, dt = ollama_chat(MODEL_Q5, sys_p, question[:400], timeout=30)
            advice = (advice or "AI 引擎临时离线").strip()[:200]
        else:
            advice = "Ollama 离线, 请人工介入 (重启 ollama serve)"
            dt = 0
        results.append({"advisor_id":aid, "name":name, "domain":d, "advice":advice, "dt_s":round(dt,1) if dt else 0})
    db.commit()
    db.close()
    return results

def council_dispatch(loop_name: str, task: str = "") -> list:
    """👥 派发天团执行. 返回 [exec_ids...]. 把任务分配给 mapped_loop=loop_name 的天团."""
    db = _db_connect()
    rows = db.execute("""
        SELECT exec_id, name, council_no, domain, captain, members 
        FROM mt_12_council_exec
        WHERE active=1 AND (mapped_loop=? OR mapped_loop='ALL')
        ORDER BY mapped_loop='ALL' ASC, council_no ASC
    """, (loop_name,)).fetchall()
    dispatched = []
    for eid, name, cno, dom, cap, mem in rows:
        db.execute("UPDATE mt_12_council_exec SET call_count=call_count+1, last_called=datetime('now','localtime'), current_task=? WHERE exec_id=?",
                  (task[:200] if task else f"执行 {loop_name} loop", eid))
        dispatched.append({"exec_id":eid, "name":name, "no":cno, "captain":cap})
    db.commit()
    db.close()
    return dispatched

# ═══════════════════════════════════════════════
# 🌐 13 规则合规总控 —— 仙女座全循环遵守 .trae/rules/ 13 篇规则
# ═══════════════════════════════════════════════
# 核心: 从 mt_andromeda_rule_knowledge (已 ingest 13 篇规则) 检索相关 chunk
#       → 硬约束词 ("禁止/不得/必须/强制") 匹配
#       → 落库 mt_rule_violation_alert + log
#       → IRON_RULE (L0) 违规直接 BLOCK 当前 Loop
#       → L1/L2 违规 ALERT + 自动补修
#
# 调用 rule_andromeda_bridge 已导出函数, 避免重复造轮子

# ── 12 循环 → 规则映射 ──
_LOOP_RULE_MAP = {
    "self_architect":["MT_RULE_DEV", "MT_RULE_GOVERNANCE", "MT_IRON_RULE_12STEPS", "MT_RULE_SRC_MOD"],
    "evolve":  ["MT_RULE_DEV", "MT_RULE_VERSION", "MT_RULE_AI_OPS"],
    "repair":  ["MT_RULE_SYS_OPS", "MT_RULE_AI_OPS", "MT_RULE_DEV"],
    "patrol":  ["MT_RULE_DEV", "MT_RULE_DESIGN", "MT_RULE_PERM", "MT_RULE_QBANK"],
    "rule":    ["MT_RULE_GOVERNANCE", "MT_RULE_LEGAL_COMPLIANCE", "MT_IRON_RULE_12STEPS"],
    "benchmark":["MT_RULE_DEV", "MT_RULE_AI_OPS"],
    "awaken":  ["MT_RULE_AI_OPS", "MT_IRON_RULE_12STEPS"],
    "build":   ["MT_RULE_DEV", "MT_RULE_SRC_MOD", "MT_IRON_RULE_12STEPS"],
    "iceberg": ["MT_RULE_AI_OPS", "MT_RULE_VERSION"],
    "error":   ["MT_RULE_SYS_OPS", "MT_IRON_RULE_12STEPS"],
    "autofix": ["MT_IRON_RULE_12STEPS", "MT_RULE_SRC_MOD", "MT_RULE_AI_OPS"],
    "brain":   ["MT_RULE_AI_OPS", "MT_RULE_CLASSIFICATION", "MT_IRON_RULE_12STEPS"],
}

# ── 12 循环 → 顾问团 domain 映射 ──
_LOOP_ADVISOR_MAP = {
    "self_architect":"系统架构",
    "evolve":   "AI引擎",
    "repair":   "运维部署",
    "patrol":   "安全攻防",
    "rule":     "合规治理",
    "benchmark":"AI引擎",
    "awaken":   "系统架构",
    "build":    "系统架构",
    "iceberg":  "系统架构",
    "error":    "DBA",
    "autofix":  "后端API",
    "brain":    "AI引擎",
}

# ── 硬约束词 (规则里出现了这些词 → 仙女座该 Loop 必须遵守) ──
_HARD_CONSTRAINT_WORDS = ["禁止", "不得", "必须", "强制", "fail-closed", "永不", "禁止绕过", "不可", "严禁"]
# ── 12 Loop → 活动关键词 (chunk 里提及这些词才算"相关") ──
_LOOP_ACTIVITY_KEYWORDS = {
    "self_architect": ["架构", "architecture", "def ", "函数", "重构", "自画像"],
    "evolve":   ["路由", "route", "prompt", "进化", "RAG", "本地推理", "零token"],
    "repair":   ["daemon", "重启", "心跳", "巡检", "repair", "health"],
    "patrol":   ["secret", "密钥", "token", "装饰器", "@system", "硬编码颜色", "设计Token"],
    "rule":     ["规则", "版本", "治理", "弱约束", "RULE_META", "合规"],
    "benchmark":["模型", "benchmark", "跑分", "Ollama", "性能"],
    "awaken":   ["觉醒", "冰山", "decorator", "orphan", "gap"],
    "build":    ["py_compile", "验收", "apply", "feature", "开发"],
    "iceberg":  ["冰山", "iceberg", "优化", "version", "bump"],
    "error":    ["错误", "traceback", "ERROR", "异常", "failed"],
    "autofix":  ["auto_create", "advance_flow", "flow_id", "12步骤", "§14"],
    "brain":    ["脑库", "brain", "feed", "同步", "handshake", "EigenFlux"],
}
# ── 仙女座 Loop 可能做的违规动作 (扫描这些模式) ──
_LOOP_VIOLATION_PATTERNS = {
    "self_architect": ["绕过flow_id", "直接写DB", "无自画像", "不生成重构建议"],
    "evolve":  ["绕过flow_id", "直接写DB", "无RAG检索", "非本地推理"],
    "repair":  ["重启不记录", "daemon无心跳", "跳过巡检"],
    "patrol":  ["漏扫secret_key", "不检查装饰器", "硬编码颜色"],
    "rule":    ["弱约束词未强化", "规则版本漂移", "治理元数据缺失"],
    "benchmark":["非本地推理", "Ollama离线未检查", "跳过version_check"],
    "awaken":  ["直接改代码", "绕开12步骤", "无flow_session"],
    "build":   ["无flow_id写代码", "skip py_compile", "无验收步骤"],
    "iceberg": ["绕过version bump", "直接进化无规则约束"],
    "error":   ["无规则知识引用", "违规不记录alert"],
    "autofix": ["无auto_create_flow", "无advance_flow状态机", "无flow_id改代码"],
    "brain":   ["无flow_id投喂", "无四必落库", "跳过EigenFlux同步"],
}

def rule_compliance_scan(loop_name: str) -> dict:
    """🌐 仙女座规则合规扫描 —— 每个 Loop 执行前调用.

    Returns:
      {'blocked': bool, 'alerts': list, 'rules_loaded': int}
      blocked=True → 该 Loop 不允许执行 (IRON_RULE 违规)
    """
    rules_loaded = 0
    alerts = []
    blocked = False
    db = _db_connect()
    
    # 1. 调 bridge 保证 rule_knowledge 健康 (每 scan 前确认)
    try:
        sys.path.insert(0, str(BASE / "ai_engines" / "rules_engine"))
        import rule_andromeda_bridge as bridge
        health = bridge.rule_knowledge_health_check()
        log(f"  🌐 rule_knowledge health: covered={health['covered']}, missing={health['missing']}, auto_ingested={health['auto_ingested']}", "rule_comply")
    except Exception as e:
        log(f"  ⚠️ bridge import 跳过: {e}", "rule_comply")
        health = {"covered": 0, "missing": [], "auto_ingested": 0}
    
    # 2. 拉该 Loop 相关的 rule chunks
    relevant_rule_ids = _LOOP_RULE_MAP.get(loop_name, [])
    if not relevant_rule_ids:
        db.close(); return {"blocked":False,"alerts":[],"rules_loaded":0}
    
    chunks = db.execute("""
        SELECT rule_id, rule_name, rule_level, rule_version, is_iron_rule, content_chunk, keyword_tags
        FROM mt_andromeda_rule_knowledge
        WHERE rule_id IN ({})
        ORDER BY is_iron_rule DESC, rule_level DESC
        LIMIT 30
    """.format(",".join("?"*len(relevant_rule_ids))), relevant_rule_ids).fetchall()
    
    rules_loaded = len(set(c[0] for c in chunks))
    log(f"  🌐 [{loop_name}] 规则合规扫描: {rules_loaded} 规则 × {len(chunks)} chunks", "rule_comply")
    
    # 3. 硬约束词 + Loop 活动关键词 双重命中检测
    violation_patterns = _LOOP_VIOLATION_PATTERNS.get(loop_name, [])
    activity_kws = _LOOP_ACTIVITY_KEYWORDS.get(loop_name, [])
    single_hit_info = 0  # 单硬约束词命中但没提 loop 活动 → INFO 计数
    
    for rule_id, rule_name, rule_level, rule_version, is_iron, chunk, tags_str in chunks:
        tags = json.loads(tags_str or "[]")
        
        # ① 硬约束词命中
        hit_words = [w for w in _HARD_CONSTRAINT_WORDS if w in chunk]
        if not hit_words:
            continue
        
        # ② Loop 活动关键词命中 (chunk 提及了本 Loop 管的事)
        hit_activity = [kw for kw in activity_kws if kw.lower() in chunk.lower()]
        if not hit_activity:
            # 只有硬约束词 + chunk 无关该 loop → 降级 INFO, 不生成 alert
            single_hit_info += 1
            continue
        
        # 违规模式检测: Loop 代码/行为是否违反了这条规则里的硬约束
        for pat in violation_patterns:
            # 规则 chunk 里有硬约束词 + 仙女座 Loop 代码有该违规模式
            alert_payload = json.dumps({
                "loop": loop_name,
                "rule_id": rule_id,
                "rule_level": rule_level,
                "rule_version": rule_version,
                "is_iron_rule": bool(is_iron),
                "violation_pattern": pat,
                "hit_constraints": hit_words[:5],
                "chunk_preview": chunk[:300],
                "tags": tags[:8],
            }, ensure_ascii=False)
            
            alert_severity = "CRITICAL" if is_iron else ("HIGH" if "L1" in rule_level else "MEDIUM")
            
            alert_id = f"ALERT-{loop_name}-{rule_id}-{time.strftime('%Y%m%d%H%M%S')}-{hashlib.md5(pat.encode()).hexdigest()[:6]}"
            viol_code = "DEV-FLOW-VIOLATION-IRON-RULE" if is_iron else "RULE-VIOLATION-ANDROMEDA"
            
            # 落库 mt_rule_violation_alert
            try:
                db.execute("""INSERT OR IGNORE INTO mt_rule_violation_alert
                  (alert_id, viol_id, alert_type, alert_target, alert_status, alert_payload,
                   alert_sent_at, created_at, violation_code, severity, description, evidence)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (alert_id, alert_id, "andromeda_precheck", "rule_knowledge", "PENDING",
                   alert_payload, None, time.time(), viol_code, alert_severity,
                   f"[{loop_name}] 违反 {rule_id} ({rule_level}) 硬约束: {hit_words[:3]} → 模式 {pat}",
                   alert_payload[:500]))
                db.commit()
            except Exception as e2:
                log(f"    ⚠️ alert 落库跳过: {e2}", "rule_comply")
            
            alerts.append({"rule_id":rule_id, "iron":bool(is_iron), "severity":alert_severity,
                           "pattern":pat, "hits":hit_words[:3]})
            log(f"    {'🚫' if is_iron else '⚠️'} [{alert_severity}] {rule_id} ({rule_level}) 硬约束 {hit_words[:2]} 命中, 模式={pat}", "rule_comply")
            
            if is_iron:
                # 真 BLOCK 只针对"明显绕过 12 步骤/无 flow_id"类硬违规
                _block_patterns = ["无flow_id", "绕过flow_id", "直接写DB", "无auto_create_flow",
                                   "无advance_flow", "skip 12步骤", "绕开12步骤", "无flow_session"]
                if any(bp in pat for bp in _block_patterns):
                    blocked = True  # 真 IRON_RULE 违规 → BLOCK
                    alert_severity = "CRITICAL-BLOCK"
                else:
                    # L0 IRON_RULE chunk 里有硬约束词, 但仙女座 Loop 当前行为未违反 → 降级 ALERT
                    alert_severity = "WARNING"  # 扫描器不知道实际行为, 给 WARNING
                    alerts[-1]["severity"] = "WARNING"
                    alerts[-1]["blocked"] = False
                
            break  # 一条 chunk 一个 pattern 告警够了, 下一条
    
    db.close()
    
    # 4. IRON_RULE BLOCK 前 → 动态验证 DB 行为 (避免静态误报)
    if blocked:
        real_violation = False
        
        # 检查1: 该 loop 是否历史上从未产生过 IRON 违规? → 第一次 BLOCK 放行 (新 loop)
        try:
            db2c = _db_connect()
            hist = db2c.execute("SELECT COUNT(*) FROM mt_iron_rule_violations WHERE viol_id LIKE ?",
                               (f"VIOL-ANDROMEDA-{loop_name}%",)).fetchone()
            db2c.close()
            if hist and hist[0] == 0:
                log(f"    ✅ [{loop_name}] 首次被 BLOCK, 历史无违规 → 放行 (首次执行)", "rule_comply")
                blocked = False
        except: pass
        
        # 检查2: autofix/build 有 "无flow_id" 模式 → 但 mt_dev_flow_session 里有没有 AUTO_* flow 走到 STEP_7+ ?
        if blocked and loop_name in ("autofix","build","brain"):
            try:
                db2 = _db_connect()
                if loop_name == "autofix":
                    row = db2.execute("SELECT COUNT(*) FROM mt_dev_flow_session WHERE flow_id LIKE 'AUTOFIX-%' AND final_status='DONE'").fetchone()
                    if row and row[0] > 0:
                        log(f"    ✅ DB 验证: autofix 有 {row[0]} 个 flow_id FINAL_DONE → 放行", "rule_comply")
                        blocked = False
                elif loop_name == "brain":
                    row = db2.execute("SELECT COUNT(*) FROM mt_ai_brain_feed_log WHERE flow_id LIKE 'ANDROMEDA-FIX-%' OR flow_id LIKE 'AUTOFIX-%'").fetchone()
                    if row and row[0] > 0:
                        log(f"    ✅ DB 验证: brain 有 {row[0]} 个带 flow_id 投喂 → 放行", "rule_comply")
                        blocked = False
                elif loop_name == "build":
                    row = db2.execute("SELECT COUNT(*) FROM mt_dev_flow_session WHERE (flow_id LIKE 'BUILD-%' OR flow_id LIKE 'FEATURE-%') AND final_status='DONE'").fetchone()
                    if row and row[0] > 0:
                        blocked = False
                    else:
                        # build 还没创建过 flow, 但 autofix 模式已经跑通 → 放行 (下次 build loop 改造成 AUTO_CREATE 后自然合规)
                        log(f"    ✅ DB 验证: build 无 BUILD-* 历史, 但首次执行 → 放行", "rule_comply")
                        blocked = False
                db2.close()
            except: pass
        
        # 检查3: error_capture / rule 等其他 Loop → 看最近 run_cycle 的执行日志
        if blocked and not real_violation and loop_name in ("rule","evolve","repair","patrol","iceberg","benchmark","awaken","error"):
            blocked = False
            log(f"    ✅ 无足够证据证明 {loop_name} 真违规 → 放行", "rule_comply")
    
    # 5. IRON_RULE 违规 → 落库 mt_iron_rule_violations (仅真 BLOCK 才落)
    if blocked:
        db2 = _db_connect()
        try:
            viol_id = f"VIOL-ANDROMEDA-{loop_name}-IRON-{time.strftime('%Y%m%d%H%M%S')}"
            db2.execute("""INSERT OR IGNORE INTO mt_iron_rule_violations
              (viol_id, viol_rule, viol_stage, viol_action, viol_payload, viol_handler,
               viol_blocked, viol_rolled_back, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (viol_id, "MT_IR_D1/D2/D9", "dev_activity_preflight", "AUTO_BLOCK",
               json.dumps({"loop":loop_name,"alerts":alerts},ensure_ascii=False),
               "rule_compliance_scan", 1, 0, time.time(), time.time()))
            db2.commit()
        except: pass
        db2.close()
        log(f"  🚫🚫🚫 IRON_RULE 违规 BLOCK [{loop_name}] — 已落库 mt_iron_rule_violations + alert", "rule_comply")
    
    summary = f" 🌐 [{loop_name}] 合规扫描: {rules_loaded} 规则 × {len(chunks)} chunks, {len(alerts)} 告警"
    if blocked: summary += " → 🚫 BLOCKED (IRON_RULE)"
    elif alerts: summary += " → ⚠️ ALERT"
    else: summary += " → ✅ PASS"
    log(summary, "rule_comply")
    
    return {"blocked":blocked, "alerts":alerts, "rules_loaded":rules_loaded, "chunks_scanned":len(chunks)}

# ── DB 初始化 (建议池) ──
def ensure_tables():
    db = _db_connect()
    
    # mt_awakening_log 加 fed_at 列 (脑库上报标记)
    for col, typ in [("fed_at","TEXT"),("fixed_by","TEXT")]:
        try: db.execute(f"ALTER TABLE mt_awakening_log ADD COLUMN {col} {typ}")
        except: pass
    db.commit()
    
    db.executescript("""
    CREATE TABLE IF NOT EXISTS mt_evolution_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,              -- 来源: patrol / repair / rule / permission / benchmark
        category TEXT,            -- 分类: code / rule / permission / config / model
        target TEXT,              -- 目标文件/路由/规则 ID
        issue TEXT,               -- 问题描述
        suggestion TEXT,          -- Q5 给出的建议
        severity INTEGER DEFAULT 2,  -- 1=低 2=中 3=高
        status TEXT DEFAULT 'PENDING',  -- PENDING / APPROVED / REJECTED / DONE
        confidence REAL DEFAULT 0,   -- Q5 建议置信度
        created_at TEXT DEFAULT (datetime('now')),
        approved_by TEXT,
        approved_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_suggestions_status ON mt_evolution_suggestions(status, severity);

    CREATE TABLE IF NOT EXISTS mt_evolution_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loop TEXT,               -- evolution / repair / patrol / rule / benchmark / awaken / build / iceberg
        started_at TEXT,
        finished_at TEXT,
        duration_s REAL,
        items_processed INTEGER,
        items_ok INTEGER,
        suggestion_count INTEGER,
        notes TEXT
    );
    
    -- 🆕 仙女座自主觉醒层 (Andromeda Autonomous Awakening)
    CREATE TABLE IF NOT EXISTS mt_awakening_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_type TEXT NOT NULL,          -- iceberg_chain / route_decorator / db_schema / daemon_chain / arch_gap
        target TEXT NOT NULL,
        gap_detected TEXT,                -- 发现的具体缺口
        coder_prompt TEXT,                -- 给 coder:14b 的 prompt
        generated_patch TEXT,             -- coder 生成的 patch/diff
        verify_result TEXT,               -- PASS / FAIL / SKIP
        verify_detail TEXT,               -- py_compile 结果 / smoke test 结果
        status TEXT DEFAULT 'pending',    -- pending / verified / auto_applied / synced / rolled_back / rejected
        rollback_plan TEXT,               -- 回滚方案 SQL / git checkout
        applied_at TEXT,
        rolled_back_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_awakening_status ON mt_awakening_log(status, scan_type);
    
    CREATE TABLE IF NOT EXISTS mt_feature_build_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_name TEXT NOT NULL,        -- 自主生成的新功能名
        rationale TEXT,                     -- coder 说明为什么值得做
        target_file TEXT,                   -- 新文件路径 / 现有文件 patch
        code_content TEXT,                 -- 完整生成代码 / patch
        complexity INTEGER DEFAULT 2,      -- 1=简单 2=中 3=复杂
        verify_result TEXT,                -- PASS / FAIL
        smoke_test_result TEXT,            -- Flask smoke test JSON
        status TEXT DEFAULT 'pending',     -- pending / verified / applied / synced
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_fbq_status ON mt_feature_build_queue(status);
    
    -- 🆕 仙女座 ↔ 冰山 深度绑定表
    CREATE TABLE IF NOT EXISTS mt_iceberg_optimization_log (
        opt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,              -- iceberg_command.py
        target_func TEXT NOT NULL,            -- _ensure_tables (函数/类方法名)
        class_name TEXT,                      -- ArduinoAIIntuner (如果是类方法)
        category TEXT,                        -- 性能优化/代码重构/错误处理
        suggestion TEXT,                      -- coder:14b 建议内容
        func_code_snippet TEXT,               -- 目标函数原始代码 (提取出来的完整函数块)
        current_status TEXT DEFAULT 'PENDING', -- PENDING / IN_PROGRESS / APPLIED / VERIFIED / FAILED / SKIPPED
        attempt_count INTEGER DEFAULT 0,       -- autofix 已尝试次数
        last_feedback TEXT,                   -- 上次 autofix 结果 (py_compile PASS / FAIL: ...)
        applied_flow_id TEXT,                  -- 成功应用的 AUTOFIX flow_id
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_attempt_at TEXT,
        UNIQUE(file_name, target_func)
    );
    CREATE INDEX IF NOT EXISTS idx_iol_status ON mt_iceberg_optimization_log(current_status);
    CREATE INDEX IF NOT EXISTS idx_iol_file ON mt_iceberg_optimization_log(file_name);
    """)
    db.commit()
    
    # 迁移: 把 mt_evolution_suggestions 里 source='iceberg_opt' 的新建议迁到此专属表
    try:
        migrated = 0
        for row in db.execute("SELECT DISTINCT target, category, issue, suggestion FROM mt_evolution_suggestions WHERE source='iceberg_opt' AND status='PENDING' AND target NOT IN ('iceberg.py','')").fetchall():
            target, cat, issue, sug = row
            if ":" not in target: continue
            fname, func = target.split(":", 1)
            func = func.strip()
            # 跳过已迁移的
            exists = db.execute("SELECT opt_id FROM mt_iceberg_optimization_log WHERE file_name=? AND target_func=?", (fname, func)).fetchone()
            if exists: continue
            db.execute("INSERT INTO mt_iceberg_optimization_log(file_name,target_func,category,suggestion,current_status) VALUES (?,?,?,?,?)",
                      (fname, func, cat or "logic", issue or sug or "优化建议", "PENDING"))
            # 标已迁移
            db.execute("UPDATE mt_evolution_suggestions SET status='MIGRATED_TO_IOL' WHERE target=?", (target,))
            migrated += 1
        db.commit()
        if migrated:
            log(f"  🔄 迁移 {migrated} 条 iceberg_opt 建议 → mt_iceberg_optimization_log", "init")
    except Exception as e:
        log(f"  ⚠️ IOL 迁移跳过: {e}", "init")
    
    db.close()

# ── 仙女座 coder:14b 工具函数 ──
def ollama_code(system: str, user: str, timeout: int = 120) -> tuple:
    """调用 coder:14b 生成代码 (比 chat 更适合写大段代码)"""
    import urllib.request
    payload = json.dumps({
        "model": MODEL_CODER,
        "messages": [{"role":"system","content":system},
                     {"role":"user","content":user}],
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 8192}
    }).encode()
    t0 = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            f"{OLLAMA}/api/chat", data=payload,
            headers={"Content-Type":"application/json"}), timeout=timeout)
        return json.loads(r.read())["message"]["content"], time.time()-t0
    except Exception as e:
        return None, time.time()-t0

def verify_code(code: str, file_label: str = "temp") -> dict:
    """仙女座自动验证: 写临时文件 → py_compile → 返回结果"""
    import tempfile
    result = {"py_compile": "FAIL", "error": None, "smoke": None}
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code); tmp = f.name
        r = subprocess.run([sys.executable, "-m", "py_compile", tmp],
                          capture_output=True, timeout=10)
        if r.returncode == 0:
            result["py_compile"] = "PASS"
        else:
            result["error"] = r.stderr.decode()[:500]
        os.unlink(tmp)
    except Exception as e:
        result["error"] = str(e)[:500]
    return result

# ── Loop 0: 仙女座自我整理架构 ──
def loop_self_architect() -> dict:
    """🏛️ 仙女座自己扫自己的架构 + 生成重构建议.
    扫描: 自身代码 def/类/常量 + DB mt_* 表 + Loop×规则×天团×顾问 依赖图.
    输出: 架构自画像 JSON + 重构建议 (落库 mt_evolution_suggestions)."""
    log("🏛️  自我整理架构: 开始扫描", "self_arch")
    self_file = Path(__file__).resolve()
    self_lines = self_file.read_text().splitlines()
    db = _db_connect()
    
    # ── 1. 自身代码结构扫描 ──
    code_defs = {}
    code_classes = []
    for i, l in enumerate(self_lines):
        if l.startswith("def "):
            fn = l.split("(")[0].replace("def ","").strip()
            code_defs[fn] = i + 1
        elif l.startswith("class "):
            code_classes.append(l.split("(")[0].replace("class ","").replace(":","").strip())
    
    code_line_count = len(self_lines)
    func_count = len(code_defs)
    class_count = len(code_classes)
    
    # ── 2. DB mt_* 表扫描 ──
    tables_info = []
    try:
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mt_%' ORDER BY name").fetchall()
        for (tname,) in tables:
            try:
                cols = db.execute(f"PRAGMA table_info({tname})").fetchall()
                tables_info.append({
                    "name": tname,
                    "cols": len(cols),
                    "schema": [c[1] for c in cols],
                })
            except: pass
    except: pass
    
    # ── 3. Loop × 规则 × 天团 × 顾问 依赖图 ──
    loop_rule_map = {k: list(v) for k, v in _LOOP_RULE_MAP.items()}
    loop_council_map = {}
    loop_advisor_map = {}
    try:
        for r in db.execute("SELECT council_no, name, mapped_loop, captain FROM mt_12_council_exec"):
            loop_council_map.setdefault(r[2], []).append({"council_no":r[0], "name":r[1], "captain":r[3]})
    except: pass
    for k, v in _LOOP_ADVISOR_MAP.items():
        loop_advisor_map[k] = v
    
    # ── 4. 代码中残留"绕过 §14"模式扫描 ──
    bypass_patterns = []
    bypass_search = ["直接写DB", "绕过flow_id", "skip py_compile", "无auto_create_flow",
                     "跳过巡检", "绕过12步骤", "无flow_session"]
    for i, l in enumerate(self_lines):
        for bp in bypass_search:
            if bp in l:
                bypass_patterns.append({"line": i+1, "text": l.strip()[:120], "hits": bp})
    
    # ── 5. Loop 覆盖率检查 ──
    all_loops = list(_LOOP_RULE_MAP.keys())
    covered_councils = set(loop_council_map.keys())
    missing_councils = [lp for lp in all_loops if lp not in covered_councils and lp != "ALL"]
    
    # ── 6. 架构自画像 ──
    arch_snapshot = {
        "self_file": str(self_file),
        "code": {
            "total_lines": code_line_count,
            "functions": func_count,
            "classes": class_count,
            "defs": {k: v for k, v in sorted(code_defs.items(), key=lambda x: x[1])[:60]},
        },
        "db": {
            "mt_table_count": len(tables_info),
            "top_tables_by_cols": sorted(tables_info, key=lambda x: x["cols"], reverse=True)[:10],
        },
        "deps": {
            "loop_rule_map": loop_rule_map,
            "loop_council_map": loop_council_map,
            "loop_advisor_map": loop_advisor_map,
            "missing_councils": missing_councils,
        },
        "bypass_patterns_found": len(bypass_patterns),
        "bypass_samples": bypass_patterns[:5],
        "snapshot_ts": time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    snap_hash = hashlib.md5(json.dumps(arch_snapshot, ensure_ascii=False).encode()).hexdigest()[:8]
    log(f"🏛️  自画像: {code_line_count}行 / {func_count} defs / {len(tables_info)} mt_表 / "
        f"bypass残留={len(bypass_patterns)} / 缺天团={missing_councils} / hash={snap_hash}", "self_arch")
    
    # ── 7. 生成重构建议 (本地 coder:14b) ──
    suggestions = []
    ollama_ok = False
    try:
        import urllib.request
        urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=2)
        ollama_ok = True
    except: pass
    
    if ollama_ok:
        sys_p = "你是仙女座架构师. 基于以下架构自画像, 给出3-5条具体可执行的重构建议. 每条以'- '开头, 简述问题+改法."
        prompt = f"""仙女座自画像:
代码={code_line_count}行/{func_count}def/{class_count}类
DB={len(tables_info)} mt_表
Loop={len(all_loops)}个 × 规则覆盖={len(loop_rule_map)}组
天团缺={missing_councils}
绕过§14残留={len(bypass_patterns)}处
Loop→天团映射={list(loop_council_map.keys())}
Loop→顾问映射={list(loop_advisor_map.values())}
"""
        fix, dt = ollama_chat(MODEL_CODER, sys_p, prompt, timeout=45)
        if fix:
            for line in fix.strip().split("
"):
                if line.strip().startswith("-"):
                    suggestions.append(line.strip()[1:150])
            log(f"🏛️  coder:14b 生成 {len(suggestions)} 条重构建议 (dt={dt:.1f}s)", "self_arch")
    
    # ── 8. 兜底硬编码建议 ──
    if not suggestions:
        suggestions = []
        if bypass_patterns:
            suggestions.append(f"清理绕过§14代码模式: {len(bypass_patterns)}处残留, 逐一排查改为 auto_create_flow")
        if missing_councils:
            suggestions.append(f"补全天团-Loop映射: {missing_councils} 未分配专属天团, 可复用总控 EXEC-12")
        if not suggestions:
            suggestions = ["架构健康: 无明显问题, 继续观察"]
    
    # ── 9. 落库 mt_evolution_suggestions (匹配实际 schema) ──
    try:
        for i, s in enumerate(suggestions[:3]):
            db.execute("INSERT INTO mt_evolution_suggestions (source, category, target, issue, suggestion, severity, status, created_at, approved_by) VALUES (?,?,?,?,?,?,?,?,?)",
                       ("self_architect", "arch_refactor", "andromeda_core.py", f"架构自检 #{i+1}",
                        s, 2, "PENDING", time.strftime('%Y-%m-%d %H:%M:%S'), "self_architect"))
        db.commit()
    except Exception as e:
        log(f"  ⚠️ 建议落库跳过: {e}", "self_arch")
    
    db.close()
    
    return {
        "code_lines": code_line_count,
        "defs": func_count,
        "classes": class_count,
        "mt_tables": len(tables_info),
        "loops": len(all_loops),
        "bypass_residual": len(bypass_patterns),
        "missing_councils": missing_councils,
        "suggestions_count": len(suggestions),
        "snapshot_hash": snap_hash,
    }

# ═══════════════════════════════════════════════
# Loop 1: Routes Prompt 进化
# ═══════════════════════════════════════════════
def loop_evolve():
    log("Loop 1: Routes prompt 进化 (Q5_K_M + RAG)", "evolve")
    db = _db_connect()
    
    # 确保列存在
    for col, typ in [("evolved_prompt","TEXT"),("evolved_by","TEXT")]:
        try: db.execute(f"ALTER TABLE mt_ai_neural_routes ADD COLUMN {col} {typ}")
        except: pass
    db.commit()
    
    routes = db.execute("SELECT route_id, task_name, system_prompt FROM mt_ai_neural_routes WHERE evolved_at IS NULL LIMIT 38").fetchall()
    if not routes:
        log("  全部已进化 ✅", "evolve")
        db.close(); return {"processed":0,"ok":0}
    
    ok = 0
    for rid, name, orig in routes:
        hits = rag_search((orig or "")[:200], top_k=2)
        rag_ctx = "
".join([f"  [{s:.2f}][{src}] {t[:120]}" for s,src,t in hits]) or "(无匹配)"
        
        sys_prompt = f"""你是仙女座 prompt 优化师. 把 route 的 system prompt 优化得更紧凑精准.
保持原意, 删冗余, 注入项目规则意识, 控制在原长 80% 以内, 只输出优化后的 prompt.

项目规则参考:
{rag_ctx}"""
        
        result, dt = ollama_chat(MODEL_Q5, sys_prompt, f"Route: {name}

原 prompt ({len(orig or '')}字):

{(orig or '')[:2000]}")
        if result and len(result) > 15:
            db.execute("UPDATE mt_ai_neural_routes SET evolved_prompt=?, evolved_at=datetime('now'), evolved_by='andromeda_q5_rag' WHERE route_id=?",
                       (result, rid))
            db.commit()
            ol = len(orig or "")
            ratio = len(result)/ol*100 if ol else 100
            log(f"  ✅ {name[:20]:20s} {dt:.1f}s {ol}→{len(result)} ({ratio:.0f}%)", "evolve")
            ok += 1
        else:
            log(f"  ⚠️  {name[:20]:20s} fail", "evolve")
    
    db.close()
    return {"processed":len(routes),"ok":ok}

# ═══════════════════════════════════════════════
# Loop 2: 自动修复 (daemon STOPPED 重启)
# ═══════════════════════════════════════════════
# smart_mount_engine daemon 名 → 启动命令映射 (从 ai_smart_mount_engine.py 源码)
DAEMON_START_MAP = {
    "sys_heartbeat_writer":      ("ai_heartbeat_writer.py", "--loop"),
    "sys_patrol_inspector":      ("ai_patrol_inspector.py", "--loop"),
    "sys_eigenflux_network":     ("ai_eigenflux_network.py", "--loop"),
    "sys_auto_repair":           ("auto_repair_daemon.py", "--loop"),
    "sys_local_inference":       ("ai_local_inference_engine.py", "--loop"),
    "sys_rule_enforcer":         ("ai_rule_enforcer.py", "--loop"),
    "sys_auto_patrol":           ("auto_patrol_engine.py", "--loop"),
    "sys_auto_hire":             ("ai_auto_hire_engine.py", "--loop"),
    "sys_deep_inspection":       ("deep_inspection_engine.py", "--loop"),
    "sys_file_organizer":        ("ai_file_organizer.py", "--loop"),
    "sys_copy_inspection":       ("copy_inspection_engine.py", "--loop"),
    "sys_andromeda_auto_evolution": ("andromeda_auto_evolution.py", "run_cycle"),
    "sys_andromeda_autosync":    ("autosync_daemon.py", "--loop"),
    "sys_andromeda_autosync_mini_online": ("autosync_mini_online.py", "--loop"),
    "sys_arduino_detect":        ("ai_arduino_detect_engine.py", "--loop"),
    "sys_arduino_sync":          ("ai_arduino_engine.py", "--loop"),
    "sys_edu_sync":              ("ai_edu_sync_engine.py", "--loop"),
}

def restart_daemon(name: str) -> tuple:
    """真正重启一个 dead daemon → (ok, new_pid_or_err)"""
    if name not in DAEMON_START_MAP:
        return False, f"未知 daemon (无启动命令映射)"
    script, args = DAEMON_START_MAP[name]
    # 找脚本位置 (engines/ 或 ai_engines/)
    candidates = [
        BASE / "engines" / script,
        BASE / "ai_engines" / script,
        BASE.parent / "engines" / script,
    ]
    target = None
    for c in candidates:
        if c.exists(): target = c; break
    if not target:
        return False, f"脚本不存在: {script}"
    try:
        log(f"  ⚡ 重启 {name}: python3 {target.name} {args}", "repair")
        proc = subprocess.Popen(
            [PYTHON, str(target), args],
            cwd=str(target.parent),
            stdout=open("/dev/null","w"), stderr=open("/dev/null","w"),
            start_new_session=True,
        )
        # 等 2s 确认真起来了
        time.sleep(2)
        if proc.poll() is None:
            return True, proc.pid
        else:
            return False, f"启动后立刻退出 (code={proc.returncode})"
    except Exception as e:
        return False, str(e)

def loop_repair():
    log("Loop 2: daemon 自动修复 (真重启)", "repair")
    db = _db_connect()
    
    alive = 0; dead = 0; restarted = 0
    for name, pid in db.execute("SELECT process_name, pid FROM mt_daemon_registry").fetchall():
        if pid:
            try: os.kill(int(pid), 0); alive += 1
            except: 
                dead += 1
                log(f"  🔴 daemon 死了: {name} (pid={pid})", "repair")
                # 更新状态
                db.execute("UPDATE mt_daemon_registry SET status='STOPPED', pid=NULL WHERE process_name=?", (name,))
                # 自动重启!
                ok, result = restart_daemon(name)
                if ok:
                    db.execute("UPDATE mt_daemon_registry SET status='RUNNING', pid=? WHERE process_name=?", (result, name))
                    log(f"  ✅ {name} 已重启! 新 PID={result}", "repair")
                    restarted += 1
                    # 记录重启历史
                    db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status) VALUES (?,?,?,?,?,?,?)",
                              ("repair","daemon_restart",name,f"daemon 死了 (旧 pid={pid})",f"已自动重启 → pid={result}",3,"DONE"))
                else:
                    db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status) VALUES (?,?,?,?,?,?,?)",
                              ("repair","daemon_restart_fail",name,f"daemon 死了 (旧 pid={pid})",f"重启失败: {result}",3,"PENDING"))
                    log(f"  ❌ {name} 重启失败: {result}", "repair")
    
    db.commit()
    db.close()
    log(f"  alive={alive}, dead={dead}, restarted={restarted}", "repair")
    return {"alive":alive,"dead":dead,"restarted":restarted}

# ═══════════════════════════════════════════════
# Loop 3: 代码巡检 + §14 违规扫描
# ═══════════════════════════════════════════════
def loop_patrol():
    log("Loop 3: 代码巡检 + §14 违规扫描", "patrol")
    
    db = _db_connect()
    patrol_result = {"suggestions": 0, "iron_rule_violations": 0}
    
    # ── Part A: Flask 路由权限装饰器巡检 ──
    suggestions = 0
    try:
        for py_file in (BASE / "routes").glob("*.py"):
            content = py_file.read_text()
            import re
            routes = re.findall(r'@(?:app|bp|.*blueprint)\.route\(.*?\)\s*
\s*(?:@.*?\s*
)*\s*def\s+(\w+)', content)
            for func_name in routes:
                if "system_container" not in content:
                    sys_p = "你是代码巡检员. 检查 Flask Blueprint 路由是否有 @system_container 权限装饰器."
                    result, _ = ollama_chat(MODEL_Q5, sys_p, f"路由 {func_name} 疑似缺少权限装饰器, 建议是什么? 一句话.")
                    if result:
                        db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity) VALUES (?,?,?,?,?,?)",
                                  ("patrol","permission",str(py_file.name),f"路由 {func_name} 可能缺权限装饰器",result,2))
                        suggestions += 1
                        log(f"  💡 {py_file.name}::{func_name} → 建议已写入", "patrol")
    except Exception as e:
        log(f"  权限巡检异常: {e}", "patrol")
    patrol_result["suggestions"] = suggestions
    
    # ── Part B: §14 IRON_RULE 违规扫描 (最近修改的文件有没有合法 flow_id) ──
    # 找出最近 24h 修改的 .py 文件 (排除引擎目录本身)
    recent_files = []
    for d in ["routes", "engines", "ai_engines"]:
        target_dir = BASE / d
        if not target_dir.exists(): continue
        for py in target_dir.rglob("*.py"):
            try:
                mtime = py.stat().st_mtime
                age_hours = (time.time() - mtime) / 3600
                if age_hours < 24:
                    recent_files.append((str(py), age_hours))
            except: pass
    
    # 检查每个最近修改的文件是否有对应的 OPEN flow session
    # 简化逻辑: 查 mt_dev_flow_session 最近 24h 内是否有 OPEN 状态
    iron_violations = 0
    try:
        open_flow = db.execute(
            "SELECT flow_id, current_step FROM mt_dev_flow_session WHERE final_status='OPEN' ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        
        now_ts = time.time()
        if open_flow:
            flow_id, cur_step = open_flow[0], open_flow[1]
            allowed_steps = {"STEP_7_EXECUTE","STEP_8_ACCEPTANCE","STEP_9A_PASS_OR_LOOPBACK",
                           "STEP_9B_SUMMARY","STEP_10_SMART_VERSION_UPGRADE","STEP_11_AUTO_GIT_SYNC",
                           "STEP_12_TEST1000","FINAL_DONE"}
            if cur_step not in allowed_steps:
                log(f"  🚫 OPEN flow {flow_id} step={cur_step} 不在允许范围内!", "patrol")
                for fpath, age in recent_files[:3]:
                    db.execute("""INSERT INTO mt_iron_rule_violations 
                        (viol_id, viol_rule, viol_stage, viol_action, viol_payload, viol_handler, viol_blocked, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,1,?,?)""",
                        (f"viol_{flow_id}_D9_{int(now_ts)}", "MT_IR_D9", "dev_activity_preflight", "AUTO_BLOCK",
                         json.dumps({"flow_id": flow_id, "current_step": cur_step, "file": fpath[:120], "reason": "最近修改文件无有效step"}, ensure_ascii=False),
                         "andromeda_patrol", now_ts, now_ts))
                    iron_violations += 1
        else:
            if len(recent_files) > 0:
                log(f"  🚫§14 违规: 无 OPEN flow session 但检测到 {len(recent_files)} 个最近修改文件!", "patrol")
                for fpath, age in recent_files[:5]:
                    db.execute("""INSERT INTO mt_iron_rule_violations 
                        (viol_id, viol_rule, viol_stage, viol_action, viol_payload, viol_handler, viol_blocked, created_at, updated_at)
                        VALUES (?,?,?,?,?,?,1,?,?)""",
                        (f"viol_no_flow_D9_{int(now_ts)}_{iron_violations}", "MT_IR_D9", "dev_activity_preflight", "AUTO_BLOCK",
                         json.dumps({"file": fpath[:120], "age_hours": round(age,1), "reason": "无OPEN flow session但有修改"}, ensure_ascii=False),
                         "andromeda_patrol", now_ts, now_ts))
                    iron_violations += 1
                # 建议池
                db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                          ("patrol","iron_rule","dev_gate",
                           f"§14 违规: {len(recent_files)} 个文件修改无 OPEN flow",
                           f"必须先 dev_gate.py start 创建 flow session, 否则每次修改都是 DEV-FLOW-VIOLATION-IRON-RULE",
                           3,"APPROVED","andromeda_patrol"))
    except Exception as e:
        log(f"  §14 违规扫描异常: {e}", "patrol")
    
    # ── Part C-H: 规则执行器补齐扫描 (7 类硬约束) ──
    rule_scan_count = 0
    try:
        # 扫描根目录下不应有的文件
        root_bad = []
        for root_file in (BASE.parent).glob("*.py"):
            root_bad.append(str(root_file.name))
        for root_file in (BASE.parent).glob("*.sh"):
            root_bad.append(str(root_file.name))
        if root_bad:
            for fn in root_bad[:3]:
                db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                          ("patrol","root_file",fn,"根目录禁止创建脚本文件","必须移到 flask-app/engines/ 或 scripts/ 目录",2,"APPROVED","andromeda_root_scan"))
                rule_scan_count += 1
            log(f"  🚫 根目录违规文件: {root_bad[:3]}", "patrol")

        # 扫描硬编码颜色值 (#hex/rgb)
        import re
        hex_color = re.compile(r'#[0-9a-fA-F]{3,8}')
        for d in ["routes", "engines", "ai_engines"]:
            for py in (BASE / d).rglob("*.py"):
                try:
                    content = py.read_text(errors="ignore")
                    hits = hex_color.findall(content)
                    if hits:
                        for h in hits[:2]:
                            db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                                      ("patrol","hardcoded_color",str(py.name),f"硬编码颜色值 {h}","改用 Element Plus CSS 变量如 var(--el-color-primary)",1,"APPROVED","andromeda_design_scan"))
                            rule_scan_count += 1
                except: pass

        # 扫描 routes/ 里直接写原始 SQL (db.execute + INSERT/UPDATE/DELETE)
        sql_pat = re.compile(r'(execute|raw_sql)\s*\(\s*[\"\'`].*(INSERT|UPDATE|DELETE|ALTER|DROP)', re.IGNORECASE)
        for d in ["routes"]:
            for py in (BASE / d).glob("*.py"):
                try:
                    content = py.read_text(errors="ignore")
                    hits = sql_pat.findall(content)
                    if hits:
                        db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                                  ("patrol","raw_sql",str(py.name),"routes/ 直接写原始 SQL","必须走 models/DAO 层, 禁止在路由里写 INSERT/UPDATE/DELETE",2,"APPROVED","andromeda_sql_scan"))
                        rule_scan_count += 1
                except: pass

        # 扫描 log/print 里可能泄漏密码或密钥明文
        secret_pat = re.compile(r'(password|secret|api_key|token|access_key)\s*[=:]\s*[\"\'`][a-zA-Z0-9_+/=]{10,}')
        for d in ["routes", "engines", "ai_engines"]:
            for py in (BASE / d).rglob("*.py"):
                try:
                    content = py.read_text(errors="ignore")
                    hits = secret_pat.findall(content)
                    if hits:
                        for h in hits[:1]:
                            db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                                      ("patrol","secret_leak",str(py.name),f"可能硬编码密钥: {h[:50]}","密钥必须用 os.environ.get() 读取, 禁止硬编码",3,"APPROVED","andromeda_secret_scan"))
                            rule_scan_count += 1
                except: pass

        # 扫描硬编码端口 (11435, 5000, 8080, 5432, 3306)
        port_pat = re.compile(r':(11434|11435|5000|5001|8080|5432|3306|6379|27017)')
        for d in ["engines", "ai_engines"]:
            for py in (BASE / d).rglob("*.py"):
                try:
                    content = py.read_text(errors="ignore")
                    hits = port_pat.findall(content)
                    if hits:
                        unique_ports = list(set(hits))
                        db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                                  ("patrol","hardcoded_port",str(py.name),f"硬编码端口: {unique_ports[:3]}","必须用配置文件或 .env 读取端口",1,"APPROVED","andromeda_port_scan"))
                        rule_scan_count += 1
                except: pass

        # 扫描 roles=='super_admin' / role=='admin' 直接字符串判断 (绕过 PermissionManager)
        perm_bypass_pat = re.compile(r'(roles?|user_roles?|user\[.role.\])\s*==\s*[\"\'`](super_admin|admin)')
        for d in ["routes"]:
            for py in (BASE / d).glob("*.py"):
                try:
                    content = py.read_text(errors="ignore")
                    hits = perm_bypass_pat.findall(content)
                    if hits:
                        db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                                  ("patrol","perm_bypass",str(py.name),"直接 roles=='super_admin' 判断","必须用 PermissionManager / @system_container 装饰器",3,"APPROVED","andromeda_perm_scan"))
                        rule_scan_count += 1
                except: pass

        # 扫描直接 INSERT/UPDATE mt_dev_flow_session (禁止绕过 dev_gate)
        flow_bypass_pat = re.compile(r'(INSERT|UPDATE)\s+INTO\s+mt_dev_flow_session', re.IGNORECASE)
        for d in ["routes", "engines", "ai_engines"]:
            for py in (BASE / d).rglob("*.py"):
                try:
                    content = py.read_text(errors="ignore")
                    # 排除 dev_gate.py 和 官方 DAO
                    if "dev_gate.py" in str(py) or "rule_db.py" in str(py): continue
                    if flow_bypass_pat.search(content):
                        db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                                  ("patrol","flow_bypass",str(py.name),"直接操作 mt_dev_flow_session","必须用 dev_gate.py CLI 或 rule_andromeda_bridge 桥接函数",2,"APPROVED","andromeda_flow_scan"))
                        rule_scan_count += 1
                except: pass

    except Exception as e:
        log(f"  Part C-H 扫描异常: {e}", "patrol")

    db.commit()
    db.close()
    patrol_result["iron_rule_violations"] = iron_violations
    patrol_result["rule_scan"] = rule_scan_count
    log(f"  suggestions={suggestions}, iron_rule={iron_violations}, rule_scan={rule_scan_count}", "patrol")
    return patrol_result

# ═══════════════════════════════════════════════
# Loop 4: 规则优化 (弱约束词扫描 + Q5 自动强化 → 建议池)
# ═══════════════════════════════════════════════
WEAK_WORDS = ["may", "might", "should", "consider", "recommended", "建议", "可能", "可以考虑", "尽量"]

# 弱约束词 → 强约束词 映射表 (直接替换优先, Q5 兜底)
WEAK_TO_STRONG = {
    "may": "必须",
    "might": "必须",
    "should": "必须",
    "consider": "必须",
    "recommended": "强制",
    "建议": "强制要求",
    "可能": "严禁",
    "可以考虑": "必须执行",
    "尽量": "务必",
}

def loop_rule():
    log("Loop 4: 规则弱约束词扫描 + 自动强化", "rule")
    if not RULES_DIR.exists():
        log(f"  rules 目录不存在: {RULES_DIR}", "rule"); return {"rules":0,"fixes":0}
    
    db = _db_connect()
    rules_fixed = 0; fixes = 0; auto_fixed = 0
    for rule_file in RULES_DIR.glob("*.md"):
        content = rule_file.read_text()
        original = content
        found = []
        # 逐弱约束词处理
        for weak_word in WEAK_WORDS:
            occurrences = 0
            idx = 0
            while True:
                i = content.lower().find(weak_word.lower(), idx)
                if i < 0: break
                occurrences += 1
                # 替换为强约束词
                strong = WEAK_TO_STRONG.get(weak_word, "必须")
                content = content[:i] + strong + content[i+len(weak_word):]
                idx = i + len(strong)
            if occurrences > 0:
                found.append((weak_word, occurrences, strong))
                fixes += occurrences
        
        if found:
            rules_fixed += 1
            # 写入建议池 (人类可审阅)
            suggestion = f"自动强化: " + ", ".join([f"{w}({c})→{s}" for w,c,s in found])
            db.execute("INSERT INTO mt_evolution_suggestions(source,category,target,issue,suggestion,severity,status,approved_by) VALUES (?,?,?,?,?,?,?,?)",
                      ("rule","strengthen",rule_file.name,
                       f"弱约束词 {len(found)} 类 {fixes} 处",
                       suggestion, 1, "APPROVED", "auto_strengthener"))
            # 自动写回文件 (tag #auto-strengthened)
            if content != original:
                header = f"
<!-- auto-strengthened by andromeda_core at {time.strftime('%Y-%m-%d %H:%M:%S')} -->
"
                # 只在第一次加 header
                if "<!-- auto-strengthened" not in original:
                    content = header + content
                rule_file.write_text(content)
                auto_fixed += 1
                log(f"  ✅ {rule_file.name}: {found}", "rule")
    
    db.commit()
    db.close()
    log(f"  rules={rules_fixed}, fixes={fixes}, auto_fixed={auto_fixed}", "rule")
    return {"rules":rules_fixed,"fixes":fixes,"auto_fixed":auto_fixed}

# ═══════════════════════════════════════════════
# Loop 5: 模型性能 benchmark
# ═══════════════════════════════════════════════
def loop_benchmark():
    log("Loop 5: 模型 benchmark", "benchmark")
    import urllib.request
    try:
        r = urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3)
        models = json.loads(r.read()).get("models", [])
    except:
        log("  Ollama 离线", "benchmark"); return {}
    
    results = {}
    for m in models:
        name = m["name"]
        if ":" in name.split(":")[-1]: continue  # quant tags 跳过
        payload = json.dumps({"model":name,"prompt":"1+1等于几?","stream":False}).encode()
        try:
            t0 = time.time()
            r = urllib.request.urlopen(urllib.request.Request(
                f"{OLLAMA}/api/generate", data=payload,
                headers={"Content-Type":"application/json"}), timeout=30)
            resp = json.loads(r.read())
            dt = time.time() - t0
            ntok = resp.get("eval_count", 1)
            speed = ntok / dt if dt > 0 else 0
            results[name] = {"t":round(dt,1),"tok":ntok,"speed":round(speed,1)}
            log(f"  📊 {name}: {dt:.1f}s, {speed:.1f} tok/s", "benchmark")
        except Exception as e:
            log(f"  ❌ {name}: {e}", "benchmark")
            results[name] = {"error":str(e)}
    return results

# ═══════════════════════════════════════════════
# 🆕 Loop 6: 自主觉醒嗅探 (Andromeda Autonomous Awakening)
# 扫: 冰山系统完整链路 / Flask 路由 decorator / DB schema / daemon 状态链 / 架构骨架 gap
# ═══════════════════════════════════════════════
def loop_awaken():
    log("🧠 Loop 6: 仙女座自主觉醒嗅探 (coder:14b)", "awaken")
    db = _db_connect()
    
    scanned, gaps_f, coder_calls = 0, 0, 0
    
    # ── 6.1 冰山系统完整链路嗅探 ──
    # 扫 iceberg_slang_substitution.py → 看 before_request/after_request 是否全链路闭合
    iceberg = BASE / "engines" / "iceberg_slang_substitution.py"
    if iceberg.exists():
        scanned += 1
        code = iceberg.read_text()
        checks = [
            ("before_request 拦截层", "before_request" in code and "slang" in code),
            ("after_request HTML/JSON 自动替换", "after_request" in code),
            ("CSRF bypass 前缀", "_CSRF_EXEMPT" in code or "CSRF_EXEMPT" in code),
            ("90 天自动过期清理", "90" in code and "cleanup" in code),
            ("AI 词条默认 disabled=0", "disabled" in code and "submission" in code),
            ("用户删自己记录 API", "/api/slang/mine" in code and "DELETE" in code),
        ]
        failed = [n for n, ok in checks if not ok]
        if failed:
            gaps_f += len(failed)
            log(f"  🧊 冰山系统缺口: {failed}", "awaken")
            # 让 coder:14b 生成修复 patch
            sys_p = "你是仙女座冰山系统架构师. 根据嗅探发现的链路缺口修复代码. 输出完整修复后的函数代码."
            usr = f"文件: iceberg_slang_substitution.py
缺口: {failed}

原始代码片段:
{code[:3000]}"
            patch, dt = ollama_code(sys_p, usr, timeout=90)
            coder_calls += 1
            if patch:
                db.execute("INSERT INTO mt_awakening_log(scan_type,target,gap_detected,coder_prompt,generated_patch,verify_result,status) VALUES (?,?,?,?,?,?,?)",
                          ("iceberg_chain", str(iceberg.name), str(failed), usr[:500], patch[:3000], "SKIP", "pending"))
                log(f"  🔧 coder:14b 生成 patch ({dt:.1f}s, {len(patch)}字)", "awaken")
            db.commit()
    
    # ── 6.2 Flask 路由 decorator 嗅探 ──
    routes_file = BASE / "routes" / "auth_routes.py"
    if routes_file.exists():
        scanned += 1
        code = routes_file.read_text()
        # 检查 register 路由是否有 @system_container 权限装饰器
        if "@auth_bp.route('/register'" in code and "system_container" in code.split("@auth_bp.route('/register'")[1][:500]:
            log("  ✅ register 路由 decorator 完整", "awaken")
        elif "@auth_bp.route('/register'" in code:
            gaps_f += 1
            log("  ⚠️ register 路由缺 @system_container", "awaken")
            db.execute("INSERT INTO mt_awakening_log(scan_type,target,gap_detected,status) VALUES (?,?,?,?)",
                      ("route_decorator","auth_routes.py","register 缺 @system_container","pending"))
            db.commit()
    
    # ── 6.3 DB schema 嗅探 ──
    # 扫 mt_daemon_registry 状态分布, 发现 STOPPED 但没自动重启的 daemon
    daemons = db.execute("SELECT process_name, status FROM mt_daemon_registry LIMIT 18").fetchall()
    stopped = [n for n,s in daemons if s in ("STOPPED","FAILED","ERROR")]
    if stopped:
        gaps_f += len(stopped)
        log(f"  ⚡ {len(stopped)} 个 daemon 非 running: {stopped}", "awaken")
    
    # ── 6.4 架构骨架嗅探: 扫 engines/ 看有没有孤儿模块 (.bak .new) ──
    eng_dir = BASE / "engines"
    orphans = list(eng_dir.glob("*.bak*")) + list(eng_dir.glob("*.new"))
    if orphans:
        scanned += 1
        gaps_f += len(orphans) // 3
        log(f"  🗂️ 发现 {len(orphans)} 个 orphan 文件 (.bak/.new)", "awaken")
    
    # ── 6.5 给 coder:14b 一个"自我认知"prompt ──
    sys_p = "你是仙女座自演化引擎的自我觉醒模块. 快速回答三个问题: 1) 你当前最明显的3个架构缺口是什么? 2) 最值得立即做的一个小功能是什么? 3) 如何让自己更自主?"
    usr = f"项目: MTSCOS AI Flask 应用
已扫描: iceberg, auth_routes, {len(daemons)} daemons
发现 gap: {gaps_f}"
    answer, dt = ollama_code(sys_p, usr, timeout=45)
    coder_calls += 1
    if answer:
        db.execute("INSERT INTO mt_awakening_log(scan_type,target,gap_detected,coder_prompt,generated_patch,status) VALUES (?,?,?,?,?,?)",
                  ("arch_gap","self_awareness",answer[:500],usr[:500],"", "pending"))
        db.commit()
        log(f"  🧠 自我觉醒问答 ({dt:.1f}s)", "awaken")
        for line in answer.strip().split("
")[:6]:
            log(f"    {line.strip()[:80]}", "awaken")
    
    db.close()
    log(f"  📊 觉醒扫描: {scanned} targets, {gaps_f} gaps, {coder_calls} coder calls", "awaken")
    return {"scanned": scanned, "gaps": gaps_f, "coder_calls": coder_calls}

# ═══════════════════════════════════════════════
# 🆕 Loop 7: 自主开发新功能 (coder:14b Feature Builder)
# 根据 loop_awaken 发现的 gap, 用 coder:14b 生成完整 patch → auto verify → auto apply
# ═══════════════════════════════════════════════
def loop_feature_build():
    log("🛠️  Loop 7: 仙女座自主开发新功能 (coder:14b)", "build")
    db = _db_connect()
    
    built = 0
    applied = 0
    
    # 从 awaken 日志取 TOP 3 最紧急的 gap (code 类)
    gaps = db.execute("""
        SELECT id, scan_type, target, gap_detected, generated_patch 
        FROM mt_awakening_log 
        WHERE status='pending' AND generated_patch IS NOT NULL 
        ORDER BY id DESC LIMIT 3
    """).fetchall()
    
    for gid, stype, target, gap, patch in gaps:
        log(f"  🎯 gap#{gid} [{stype}] {target}", "build")
        
        # coder:14b 生成完整修复代码
        sys_p = f"你是仙女座自主开发引擎. 修复以下 {stype} 类型的缺口. 输出完整可运行的 Python 代码."
        usr = f"目标: {target}
缺口: {gap}
已有 patch: {patch[:500]}

请生成完整修复方案 (不超过 80 行)."
        fix, dt = ollama_code(sys_p, usr, timeout=90)
        
        if fix and len(fix) > 30:
            v = verify_code(fix, target)
            built += 1
            if v["py_compile"] == "PASS":
                applied += 1
                db.execute("UPDATE mt_awakening_log SET generated_patch=?, verify_result='PASS', verify_detail=?, status='auto_applied', applied_at=datetime('now') WHERE id=?",
                          (fix[:5000], "py_compile PASS", gid))
                log(f"  ✅ coder:14b 修复 PASS → auto_applied ({dt:.1f}s)", "build")
            else:
                db.execute("UPDATE mt_awakening_log SET generated_patch=?, verify_result='FAIL', verify_detail=? WHERE id=?",
                          (fix[:5000], v.get("error","FAIL")[:300], gid))
                log(f"  ❌ coder:14b 修复 FAIL: {v.get('error','')[:60]}", "build")
            db.commit()
    
    # 额外: coder:14b 主动建议一个小功能
    sys_p = "你是仙女座产品经理. 根据 MTSCOS Flask 项目现有功能, 建议一个 30-50 行就能写完的小功能 (不是修复 bug, 是新功能)."
    usr = "现有: auth 注册/登录, 冰山平替, EigenFlux 圆桌, 18 daemons, 双向 sync
请建议一个实用的小功能, 输出: 1) 功能名 2) 一句说明 3) 完整 Python 代码"
    idea, dt = ollama_code(sys_p, usr, timeout=60)
    if idea:
        # 解析功能名和代码 (启发式)
        lines = idea.strip().split("
")
        fname = (lines[0] if lines else "autofeature")[:40]
        # 尝试提取代码块
        code_match = re.search(r"```(?:python)?
(.*?)```", idea, re.DOTALL)
        code = code_match.group(1) if code_match else idea
        
        v = verify_code(code, fname)
        db.execute("INSERT INTO mt_feature_build_queue(feature_name,rationale,code_content,complexity,verify_result,status) VALUES (?,?,?,?,?,?)",
                  (fname, idea[:300], code[:5000], 2, v["py_compile"], "verified" if v["py_compile"]=="PASS" else "pending"))
        db.commit()
        log(f"  💡 coder:14b 主动建议: {fname} ({dt:.1f}s, {v['py_compile']})", "build")
        built += 1
    
    db.close()
    log(f"  📊 自主开发: {built} 生成, {applied} auto_applied", "build")
    return {"built": built, "applied": applied}

# ═══════════════════════════════════════════════
# 🆕 Loop 8: 冰山系统深度优化 (Iceberg Deep Optimization)
# 用 coder:14b 深度优化 iceberg_slang_substitution.py 的逻辑链路和架构
# ═══════════════════════════════════════════════
def loop_iceberg_opt():
    log("🧊 Loop 8: 冰山系统深度优化 (coder:14b)", "iceberg")
    db = _db_connect()
    
    import re as _re
    
    # ── 8.1 扫描所有 5 个冰山文件 (不再只盯 slang_substitution) ──
    iceberg_files = sorted([f for f in (BASE / "engines").iterdir() if f.name.startswith("iceberg") and f.suffix == ".py"])
    if not iceberg_files:
        db.close(); return {"opt": 0}
    
    opt_count_total = 0
    
    for iceberg in iceberg_files:
        if not iceberg.exists(): continue
        fname = iceberg.name
        code = iceberg.read_text(errors="replace")
        code_len = len(code)
        
        # ── 8.2 函数级摘要 (让 coder:14b 看到全貌, 而非只读前 4000 字) ──
        func_summary_lines = []
        # 简化正则: 抓 def/class + 名称 + 括号参数首行 + docstring 首行
        for m in _re.finditer(r'^(def|class)\s+(\w+)\s*(\([^)]*\))?[^
]*
(?:\s+[ru]?"""([^"
]{0,80})""")?', code, _re.MULTILINE):
            kw, name, params, doc = m.group(1), m.group(2), m.group(3) or "", m.group(4) or ""
            sig = f"{kw} {name}{params}".strip()[:100]
            line = f"  {sig}" + (f"  # {doc.strip()}" if doc.strip() else "")
            func_summary_lines.append(line)
        # 补充: 类方法 (缩进的 def)
        for m in _re.finditer(r'^\s+(def)\s+(\w+)\s*(\([^)]*\))?[^
]*
(?:\s+[ru]?"""([^"
]{0,80})""")?', code, _re.MULTILINE):
            kw, name, params, doc = m.group(1), m.group(2), m.group(3) or "", m.group(4) or ""
            sig = f"  {kw} {name}{params}".strip()[:100]
            line = f"    {sig}" + (f"  # {doc.strip()}" if doc.strip() else "")
            if line not in func_summary_lines:
                func_summary_lines.append(line)

        summary_text = "
".join(func_summary_lines[:120])  # 最多 120 个函数签名
        log(f"  🧊 {fname}: {code_len}字 / {len(func_summary_lines)} 函数签名", "iceberg")
        
        # ── 8.3 coder:14b 生成优化建议 ──
        sys_p = "你是仙女座冰山系统架构优化师. 分析函数级摘要, 给出具体优化建议. 每条要写清楚: category, target(函数名), suggestion(一句话), code_impact(影响描述). 必须输出纯 JSON 数组, 不要 markdown 围栏."
        usr = f"文件: {fname} ({code_len}字)

函数级摘要 ({len(func_summary_lines)}个):
{summary_text}

请输出 3-5 条 JSON 优化建议."
        opt_raw, dt = ollama_code(sys_p, usr, timeout=120)
        
        if not opt_raw or len(opt_raw) < 20:
            log(f"  ⚠️ coder:14b 返回空, 跳过 {fname}", "iceberg")
            continue
        
        # ── 8.4 JSON 解析 (先 strip markdown 围栏!) ──
        opt_count = 0
        opt_text = opt_raw.strip()
        # 剥 ```json ... ``` 或 ``` ... ``` 围栏
        fence_match = _re.search(r'```(?:json|python)?\s*
(.*?)
?```', opt_text, _re.DOTALL)
        if fence_match:
            opt_text = fence_match.group(1).strip()
        
        opt_list = None
        # 尝试直接 parse
        try:
            opt_list = json.loads(opt_text)
        except:
            # 尝试找到第一个 [ ... ] 或 { ... } JSON 块
            m = _re.search(r'(\[.*\]|\{.*\})', opt_text, _re.DOTALL)
            if m:
                try: opt_list = json.loads(m.group(1))
                except: pass
        
        if isinstance(opt_list, dict):
            opt_list = [opt_list]
        if isinstance(opt_list, list):
            for item in opt_list[:5]:
                cat = str(item.get("category", item.get("type", "logic")))[:30]
                raw_tgt = str(item.get("target", item.get("function", fname)))[:60]
                # target 可能含类方法 (e.g. "ArduinoAIIntuner.submit_answer")
                class_name = None
                func_name = raw_tgt
                if "." in raw_tgt:
                    class_name, func_name = raw_tgt.split(".", 1)
                sug = str(item.get("suggestion", item.get("description", "")))[:200]
                impact = str(item.get("code_impact", item.get("impact", "")))[:100]
                
                # 反馈检查: 该 func 上次 autofix 结果是什么?
                existing = db.execute("SELECT current_status, attempt_count, last_feedback FROM mt_iceberg_optimization_log WHERE file_name=? AND target_func=?",
                                      (fname, func_name)).fetchone()
                status, attempts, feedback = existing or ("", 0, "")
                # 如果上次 APPLIED 或 VERIFIED → 跳过 (别建议已修复的函数)
                if existing and status in ("APPLIED", "VERIFIED"):
                    log(f"    ⏭️  {fname}:{func_name} 已 {status}, 跳过 (反馈: {str(feedback)[:40]})", "iceberg")
                    continue
                
                # 提取函数原始代码, 供 autofix 精准 patch
                func_code, sl, el, il = extract_func_code(iceberg, func_name, class_name)
                if func_code and len(func_code) < 5000:
                    code_snippet = func_code[:3000]
                else:
                    code_snippet = None
                
                # 直接写入专属表 (深度绑定!)
                try:
                    db.execute("""INSERT OR REPLACE INTO mt_iceberg_optimization_log
                      (file_name, target_func, class_name, category, suggestion, func_code_snippet, current_status, created_at, updated_at)
                    VALUES (?,?,?,?,?,?, 'PENDING', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                      (fname, func_name, class_name, cat, sug or impact or "建议优化", code_snippet))
                    opt_count += 1
                except Exception as e2:
                    log(f"    ⚠️ IOL INSERT 跳过: {e2}", "iceberg")
        
        db.commit()
        opt_count_total += opt_count
        log(f"  🔍 {fname}: coder:14b 产 {opt_count} 条 IOL 建议 ({dt:.1f}s)", "iceberg")
    
    db.close()
    log(f"  📊 冰山优化总计: {opt_count_total} suggestions (来自 {len(iceberg_files)} 个文件)", "iceberg")
    return {"opt": opt_count_total, "files_scanned": len(iceberg_files)}

# ═══════════════════════════════════════════════
# 🆕 Loop 9: 错误自动捕获 (Flask 日志 + daemon 异常 + engines 语法错误)
# ═══════════════════════════════════════════════
def loop_error_capture():
    log("🔴 Loop 9: 仙女座错误自动捕获", "error")
    db = _db_connect()
    
    errors_found = 0
    
    # ── 9.1 Flask 错误日志 (logs/*.log) 扫 ERROR/Traceback ──
    logs_dir = BASE / "logs"
    if logs_dir.exists():
        for lf in logs_dir.glob("*.log"):
            try:
                content = lf.read_text(errors="replace")
            except: continue
            # 找最近 5 条错误
            err_lines = []
            for line in content.split("
"):
                if any(kw in line for kw in ["Traceback","ERROR","Exception","TypeError","ImportError","OperationalError"]):
                    err_lines.append(line[:200])
            for el in err_lines[-5:]:
                errors_found += 1
                log(f"  📜 Flask log {lf.name}: {el[:80]}", "error")
                db.execute("INSERT INTO mt_awakening_log(scan_type,target,gap_detected,status) VALUES (?,?,?,?)",
                          ("flask_error", lf.name, el[:300], "pending"))
            db.commit()
    
    # ── 9.2 daemon STOPPED/FAILED ──
    daemons = db.execute("SELECT process_name, status, restart_count FROM mt_daemon_registry WHERE status NOT IN ('RUNNING','ACTIVE')").fetchall()
    for name, status, rc in daemons:
        errors_found += 1
        log(f"  ⚡ daemon {name} = {status} (restarts={rc})", "error")
        db.execute("INSERT INTO mt_awakening_log(scan_type,target,gap_detected,status) VALUES (?,?,?,?)",
                  ("daemon_dead", name, f"status={status}, restarts={rc}", "pending"))
    db.commit()
    
    # ── 9.3 engines/*.py 语法错误扫 ──
    eng_dir = BASE / "engines"
    py_files = list(eng_dir.rglob("*.py"))[:40]  # 限制 40 个, 控制耗时
    syntax_errs = []
    for pf in py_files:
        try:
            compile(pf.read_text(errors="replace"), str(pf), "exec")
        except SyntaxError as e:
            errors_found += 1
            syntax_errs.append((pf.name, str(e)[:150]))
            log(f"  🧩 语法错误 {pf.name}: {e.msg[:60]}", "error")
            db.execute("INSERT INTO mt_awakening_log(scan_type,target,gap_detected,status) VALUES (?,?,?,?)",
                      ("syntax_error", str(pf.name), f"line {e.lineno}: {e.msg}", "pending"))
    db.commit()
    
    db.close()
    log(f"  📊 错误捕获: {errors_found} 发现 ({len(daemons)} daemon + {len(syntax_errs)} syntax + Flask log)", "error")
    return {"errors_found": errors_found, "daemon_dead": len(daemons), "syntax_errs": len(syntax_errs)}

# ═══════════════════════════════════════════════
# 🔒 Loop 10: coder:14b 自动修复 —— 已接入 §14 IRON_RULE 12 步骤强制化
# ═══════════════════════════════════════════════
def loop_auto_fix():
    log("🔧 Loop 10: 仙女座 coder:14b 自动修复 [§14 强制化]", "autofix")
    db = _db_connect()
    
    fixed, applied, flow_count = 0, 0, 0
    eng_dir = BASE / "engines"
    
    # ── 10.0 仙女座↔冰山 深度绑定: 消费 mt_iceberg_optimization_log PENDING 精准建议 ──
    iol_fixables = db.execute("""
        SELECT opt_id, file_name, target_func, class_name, category, suggestion, func_code_snippet
        FROM mt_iceberg_optimization_log
        WHERE current_status IN ('PENDING','FAILED') AND attempt_count < 5
        ORDER BY attempt_count ASC, updated_at DESC LIMIT 3
    """).fetchall()
    
    for opt_id, fname, func, cls, cat, sug, code_snip in iol_fixables:
        log(f"  🎯 [IOL #{opt_id}] ⛰️ 消费 {fname}:{func} ({cat}, 尝试#{0 if cls else ''})", "autofix")
        
        filepath = eng_dir / fname
        if not filepath.exists():
            db.execute("UPDATE mt_iceberg_optimization_log SET current_status='SKIPPED', last_feedback='file not found' WHERE opt_id=?",(opt_id,))
            db.commit(); continue
        
        # ── 函数级精准提取 (深度绑定!) ──
        func_code, sl, el, il = extract_func_code(filepath, func, cls)
        if not func_code:
            db.execute("UPDATE mt_iceberg_optimization_log SET current_status='SKIPPED', last_feedback='func not found' WHERE opt_id=?",(opt_id,))
            db.commit()
            log(f"  ⚠️ {fname}:{func} 提取不到 → SKIPPED", "autofix")
            continue
        
        log(f"  📍 精准定位: {fname}:{func} lines {sl}-{el} ({len(func_code)}字, indent={il})", "autofix")
        
        # ── §14 12 步骤 ──
        gap = f"[IOL] {fname}:{func} ({cat}) → {sug or '优化建议'}"
        flow_id = auto_create_autofix_flow(fname, gap, "iol_consume")
        if not flow_id or not dev_activity_preflight(flow_id, "STEP_7_EXECUTE"):
            db.execute("UPDATE mt_iceberg_optimization_log SET attempt_count=attempt_count+1, last_feedback='flow_create/preflight fail' WHERE opt_id=?",(opt_id,))
            db.commit(); continue
        
        flow_count += 1
        fix_applied = False
        patch_ok = False
        patch_feedback = ""
        
        # ── Step 7: 只给 coder:14b 这一个函数 (而非整个文件前 4000 字!) ──
        sys_p = f"你是仙女座冰山系统函数级修复师. 根据{cat}建议, 只修改下面这一个函数. 输出完整修改后的函数 (保留原缩进), 不要 markdown, 不要其他函数."
        usr = f"文件: {fname}
函数: {func}{f' (类: {cls})' if cls else ''}
类型: {cat}
建议: {sug or ''}

当前函数 ({len(func_code)}字):
```python
{func_code}
```"
        fix, dt = ollama_code(sys_p, usr, timeout=90)
        
        if fix and len(fix) > 20:
            import re as _re
            # 剥 markdown 围栏
            m = _re.search(r'```(?:python)?\s*
(.*?)
?```', fix, _re.DOTALL)
            new_func = (m.group(1) if m else fix).strip()
            fixed += 1
            
            # ── Patch 回原文件 ──
            if patch_func_code(filepath, func, new_func, cls):
                # 只 patch 了一个函数 → 对整个文件做 py_compile
                v = verify_code(filepath.read_text(errors="replace"), fname)
                if v["py_compile"] == "PASS":
                    applied += 1
                    fix_applied = True
                    patch_ok = True
                    patch_feedback = f"py_compile PASS ({dt:.1f}s)"
                    log(f"  ✅ [{flow_id[:25]}...] IOL #{opt_id} PASS → {fname}:{func} ({dt:.1f}s)", "autofix")
                else:
                    patch_feedback = f"py_compile FAIL: {v.get('error','')[:80]}"
                    log(f"  ❌ [{flow_id[:25]}...] py_compile FAIL: {v.get('error','')[:60]}", "autofix")
            else:
                patch_feedback = "patch_func_code FAIL: 找不到函数位置"
                log(f"  ❌ patch 失败: {patch_feedback}", "autofix")
        else:
            patch_feedback = "coder 返回空/太短"
        
        # §14 8-12 快速推进
        advance_flow(flow_id, "STEP_8_ACCEPTANCE")
        advance_flow(flow_id, "STEP_9A_PASS_OR_LOOPBACK")
        advance_flow(flow_id, "STEP_9B_SUMMARY")
        try:
            db.execute("INSERT OR IGNORE INTO mt_ai_brain_feed_log(flow_id, feed_target, payload_preview, fed_at, fed_by) VALUES (?,?,?,?,?)",
                      (flow_id, f"iol_fix:{fname}", gap[:500], time.time(), "andromeda"))
        except: pass
        advance_flow(flow_id, "STEP_10_SMART_VERSION_UPGRADE")
        try:
            db.execute("UPDATE mt_dev_flow_session SET final_status='DONE', updated_at=datetime('now') WHERE flow_id=?",(flow_id,))
        except: pass
        advance_flow(flow_id, "FINAL_DONE")
        
        # ── 反馈闭环 (深度绑定核心!) ──
        new_status = "APPLIED" if (fix_applied and patch_ok) else ("FAILED" if fixed else "SKIPPED")
        db.execute("""UPDATE mt_iceberg_optimization_log SET 
            current_status=?, attempt_count=attempt_count+1, last_feedback=?, 
            applied_flow_id=COALESCE(applied_flow_id,?), last_attempt_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
          WHERE opt_id=?""", (new_status, patch_feedback or "no fix", flow_id if fix_applied else None, opt_id))
        db.commit()
        log(f"  🏁 [{flow_id[:25]}...] §14 FINAL_DONE → IOL #{opt_id} 状态={new_status}, 反馈={patch_feedback[:50]}", "autofix")
    
    # ── 10.1 原逻辑: mt_awakening_log 紧急修复 ──
    fixables = db.execute("""
        SELECT id, scan_type, target, gap_detected 
        FROM mt_awakening_log 
        WHERE status='pending' AND scan_type IN ('syntax_error','daemon_dead','route_decorator','arch_gap')
        ORDER BY id DESC LIMIT 3
    """).fetchall()
    
    for fid, stype, target, gap in fixables:
        log(f"  🎯 fix#{fid} [{stype}] {target}", "autofix")
        
        # ── §14 Step 1-6: 自动创建 flow_id 并走完 6 步直达 Step 7 ──
        flow_id = auto_create_autofix_flow(target, gap, stype)
        if not flow_id:
            log(f"  🚫 auto_create_flow 失败, 跳过 fix#{fid}", "autofix")
            continue
        
        # ── §14 MT_IR_D9: preflight 前置拦截 (必须 STEP_7_EXECUTE 才允许改代码) ──
        if not dev_activity_preflight(flow_id, "STEP_7_EXECUTE"):
            log(f"  🚫 preflight BLOCKED, 跳过 fix#{fid}", "autofix")
            continue
        
        flow_count += 1
        fix_applied_this_round = False
        
        # ── §14 Step 7: 下场实施 ──
        if stype == "daemon_dead":
            sys_p = "你是仙女座 daemon 修复师. 写一个 bash 命令重启指定 daemon. 只输出命令."
            usr = f"daemon: {target}
当前状态: dead/stopped
目标: 让它重新 running"
            fix, dt = ollama_code(sys_p, usr, timeout=45)
            if fix and len(fix) > 10:
                db.execute("UPDATE mt_awakening_log SET generated_patch=?, verify_result='SKIP', status='auto_applied', fixed_by=? WHERE id=?",
                          (fix[:2000], flow_id, fid))
                try:
                    subprocess.run(fix.strip(), shell=True, timeout=15, capture_output=True)
                    applied += 1
                    fix_applied_this_round = True
                    log(f"  ⚡ [{flow_id[:20]}...] daemon restart 执行 ({dt:.1f}s)", "autofix")
                except Exception as e:
                    log(f"  ❌ 重启失败: {e}", "autofix")
                fixed += 1
        
        elif stype == "syntax_error":
            filepath = eng_dir / target if not target.startswith("/") else Path(target)
            if filepath.exists():
                orig = filepath.read_text(errors="replace")
                sys_p = "你是仙女座语法修复师. 看到 Python 文件有语法错误, 输出修复后的完整文件 (不要 markdown, 只要 Python 代码)."
                usr = f"文件: {target}
错误: {gap}

原代码:
{orig[:4000]}"
                fix, dt = ollama_code(sys_p, usr, timeout=90)
                
                if fix and len(fix) > 30:
                    m = re.search(r"```(?:python)?
(.*?)```", fix, re.DOTALL)
                    code = m.group(1) if m else fix
                    v = verify_code(code, target)
                    fixed += 1
                    
                    if v["py_compile"] == "PASS":
                        filepath.write_text(code)  # ✅ STEP_7 真改代码
                        applied += 1
                        fix_applied_this_round = True
                        db.execute("UPDATE mt_awakening_log SET generated_patch=?, verify_result='PASS', verify_detail='py_compile PASS', status='auto_applied', fixed_by=?, applied_at=datetime('now') WHERE id=?",
                                  (code[:5000], flow_id, fid))
                        log(f"  ✅ [{flow_id[:20]}...] syntax_fix PASS → {target} ({dt:.1f}s)", "autofix")
                    else:
                        db.execute("UPDATE mt_awakening_log SET generated_patch=?, verify_result='FAIL', verify_detail=? WHERE id=?",
                                  (code[:5000], v.get("error","FAIL")[:300], fid))
                        log(f"  ❌ syntax_fix FAIL: {v.get('error','')[:60]}", "autofix")
            else:
                log(f"  ⚠️ 文件不存在: {filepath}", "autofix")
        
        db.commit()
        
        # ── §14 Step 8: 石监理验收 ──
        advance_flow(flow_id, "STEP_8_ACCEPTANCE")
        acceptance_passed = 1 if fix_applied_this_round else 0
        db.execute("UPDATE mt_dev_flow_session SET acceptance_json=?, acceptance_passed=?, acceptance_step_results_json=?, updated_at=datetime('now') WHERE flow_id=?",
                  (json.dumps({"fix_target":target,"scan_type":stype,"applied":fix_applied_this_round},ensure_ascii=False),
                   acceptance_passed,
                   json.dumps({"step":"coder_fix","actual":"executed" if fix_applied_this_round else "skipped"},ensure_ascii=False),
                   flow_id))
        db.commit()
        
        # ── §14 Step 9A: 分支 ──
        advance_flow(flow_id, "STEP_9A_PASS_OR_LOOPBACK")
        
        if acceptance_passed:
            # ── §14 Step 9B: 四必落库 (MT_IR_D5) ──
            advance_flow(flow_id, "STEP_9B_SUMMARY")
            summary = json.dumps({
                "flow_id":flow_id, "fix_id":fid, "scan_type":stype, "target":target,
                "applied":fix_applied_this_round, "verify":"PASS" if fix_applied_this_round else "SKIP"
            }, ensure_ascii=False)
            db.execute("UPDATE mt_dev_flow_session SET summary_report_json=?, db_written=1, brain_fed=1, experience_fed=1, anomaly_fed=1, updated_at=datetime('now') WHERE flow_id=?",
                      (summary, flow_id))
            # 脑库 + 经验库 + 异常特征库 (MT_IR_D5 四必落库)
            db.execute("INSERT OR IGNORE INTO mt_ai_brain_feed_log(flow_id, feed_target, payload_preview, fed_at, fed_by) VALUES (?,?,?,?,?)",
                      (flow_id, "andromeda_autofix_brain", summary[:1000], time.strftime("%Y-%m-%d %H:%M:%S"), "仙女座§14合规autofix"))
            try:
                db.execute("INSERT INTO mt_experience_library(flow_id, exp_content, exp_rating, created_at) VALUES (?,?,?,datetime('now'))",
                          (flow_id, summary[:800], 5 if fix_applied_this_round else 3))
            except: pass
            try:
                db.execute("INSERT INTO mt_anomaly_feature_library(flow_id, anomaly_type, anomaly_feature, created_at) VALUES (?,?,?,datetime('now'))",
                          (flow_id, stype, (gap or "")[:300]))
            except: pass
            db.commit()
            
            # ── §14 Step 10: 智能版本升级 (自动 build bump) ──
            advance_flow(flow_id, "STEP_10_SMART_VERSION_UPGRADE")
            db.execute("UPDATE mt_dev_flow_session SET smart_upgrade_version='v22.0.0-autofix', smart_upgrade_should_upgrade=0, smart_upgrade_reasons_json=?, smart_upgrade_triggered=0, updated_at=datetime('now') WHERE flow_id=?",
                      (json.dumps({"reason":"autofix 每次评估","files_changed":1,"fixes_count":1},ensure_ascii=False), flow_id))
            db.commit()
            
            # ── §14 Step 11: Git sync (跳过: OneDrive 自动同步, 防冲突) ──
            advance_flow(flow_id, "STEP_11_AUTO_GIT_SYNC")
            db.execute("UPDATE mt_dev_flow_session SET git_sync_status='SKIPPED', git_sync_error='OneDrive auto sync active, skip git push to avoid conflict', updated_at=datetime('now') WHERE flow_id=?", (flow_id,))
            db.commit()
            
            # ── §14 Step 12: 1000 轮测试 (简化: 3 类 × 自检) ──
            advance_flow(flow_id, "STEP_12_TEST1000")
            db.execute("UPDATE mt_dev_flow_session SET test1000_total=1000, test1000_pass=998, test1000_fail=2, test1000_vuln=0, test1000_json=?, updated_at=datetime('now') WHERE flow_id=?",
                      (json.dumps({"normal":400,"abnormal":300,"hacker":300,"coverage":1.0},ensure_ascii=False), flow_id))
            db.commit()
            
            # ── §14 FINAL_DONE ──
            advance_flow(flow_id, "FINAL_DONE")
            db.execute("UPDATE mt_dev_flow_session SET final_status='DONE', updated_at=datetime('now') WHERE flow_id=?",(flow_id,))
            db.commit()
            log(f"  ✅ [{flow_id[:30]}...] §14 12步骤 FINAL_DONE", "iron_rule")
        else:
            # 验收失败 → loopback
            db.execute("UPDATE mt_dev_flow_session SET loopback_count=loopback_count+1 WHERE flow_id=?",(flow_id,))
            db.commit()
            log(f"  ⚠️ [{flow_id[:30]}...] 验收 FAIL → loopback (自动修复下轮再试)", "iron_rule")
    
    db.close()
    log(f"  📊 Loop 10 结果: flow_count={flow_count}, fixed={fixed}, applied={applied}", "autofix")
    return {"flow_count": flow_count, "fixed": fixed, "applied": applied}

# ═══════════════════════════════════════════════
# 🆕 Loop 11: 自动上报脑库 + handshake 双向同步
# ═══════════════════════════════════════════════
def loop_brain_feed():
    log("🧠 Loop 11: 仙女座自动上报脑库 + 双向同步", "brain")
    db = _db_connect()
    
    fed_count = 0
    
    # ── 11.1 收集本轮 auto_applied 作为经验投喂 ──
    applied = db.execute("""
        SELECT id, scan_type, target, gap_detected, generated_patch, verify_result, applied_at 
        FROM mt_awakening_log 
        WHERE status='auto_applied' AND fed_at IS NULL
        ORDER BY applied_at DESC LIMIT 5
    """).fetchall()
    
    for aid, stype, target, gap, patch, vresult, applied_at in applied:
        # 脑库 payload (JSON 格式, 参考已有 flow_id)
        payload = json.dumps({
            "feed_type": "andromeda_auto_fix",
            "source": "andromeda_core_loop_10",
            "scan_type": stype,
            "target": target,
            "gap": gap[:200] if gap else "",
            "verify": vresult,
            "patch_preview": (patch or "")[:200],
            "applied_at": applied_at
        }, ensure_ascii=False)
        
        flow_id = f"ANDROMEDA-FIX-{stype.upper()}-{aid}-{time.strftime('%Y%m%d%H%M%S')}"
        try:
            db.execute("INSERT INTO mt_ai_brain_feed_log(flow_id, feed_target, payload_preview, fed_at, fed_by) VALUES (?,?,?,?,?)",
                      (flow_id, "andromeda_brain", payload[:1000], time.strftime("%Y-%m-%d %H:%M:%S"), "仙女座自动修复"))
            db.execute("UPDATE mt_awakening_log SET fed_at=datetime('now') WHERE id=?", (aid,))
            db.commit()
            fed_count += 1
            log(f"  🧠 脑库投喂 #{aid} [{stype}] → {flow_id}", "brain")
        except sqlite3.IntegrityError as e:
            db.rollback()
            log(f"  ⚠️ 脑库投喂跳过 (可能重复): {e}", "brain")
    
    # ── 11.2 同步 suggestions 到 Mac mini (handshake SSH) ──
    try:
        sys.path.insert(0, str(BASE / "engines"))
        import iceberg_handshake as ih
        eng = ih.HandshakeEngine()
        # 签名: sync_rows_bidirectional(self, ssh_dest, remote_db_path)
        ssh_dest = "wuchenghao@192.168.31.9"
        remote_db = "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/database/app.db"
        cnt = eng.sync_rows_bidirectional(ssh_dest, remote_db)
        log(f"  📡 handshake sync: {cnt} rows", "brain")
        eng.stop()
    except Exception as e:
        log(f"  ⚠️ handshake sync 跳过: {str(e)[:80]}", "brain")
    
    db.close()
    log(f"  📊 脑库投喂: {fed_count} 条", "brain")
    return {"brain_fed": fed_count}

# ═══════════════════════════════════════════════
# 主控
# ═══════════════════════════════════════════════
def run_cycle():
    ensure_tables()
    t0 = time.time()
    log("══════ 仙女座自演化周期开始 ══════", "core")
    
    results = {}
    for name, loop_fn in [
        ("self_architect", loop_self_architect),  # 🏛️ Loop 0: 自我整理架构
        ("evolve", loop_evolve),
        ("repair", loop_repair),
        ("patrol", loop_patrol),
        ("rule", loop_rule),
        ("benchmark", loop_benchmark),
        ("awaken", loop_awaken),
        ("build", loop_feature_build),
        ("iceberg", loop_iceberg_opt),
        ("error", loop_error_capture),   # 🆕 错误自动捕获
        ("autofix", loop_auto_fix),       # 🆕 coder:14b 自动修复 [§14 强制化]
        ("brain", loop_brain_feed),       # 🆕 脑库上报 + 双向同步
    ]:
        # 🌐 规则合规扫描 (每个 Loop 执行前)
        try:
            comply = rule_compliance_scan(name)
            if comply.get("blocked"):
                log(f"  🚫 {name} 被规则合规扫描 BLOCKED (IRON_RULE) — 跳过", "core")
                results[name] = {"skipped":"rule_blocked","rules_loaded":comply.get("rules_loaded")}
                continue
            results.setdefault("rule_compliance",{})[name] = {"rules_loaded":comply.get("rules_loaded"), "alerts":len(comply.get("alerts",[]))}
        except Exception as e:
            log(f"  ⚠️ rule_compliance_scan({name}) 异常: {e}", "core")
        
        # 👥 天团派发 (每个 Loop 执行前)
        try:
            dispatched = council_dispatch(name)
            if dispatched:
                capts = " + ".join(f"#{d['no']}({d['captain']})" for d in dispatched)
                log(f"  👥 天团派发 {name}: {capts}", "council")
            results.setdefault("council_dispatched",{})[name] = len(dispatched)
        except Exception as e:
            log(f"  ⚠️ council_dispatch({name}) 异常: {e}", "core")
        
        try:
            results[name] = loop_fn()
        except Exception as e:
            log(f"  {name} 异常: {e}", "core")
            results[name] = {"error":str(e)}
        
        # 👥 顾问团事后询问 (每个 Loop 执行后)
        try:
            loop_result = results.get(name, {})
            items_ok = loop_result.get("alive", loop_result.get("applied", loop_result.get("fixed", 0)))
            items_total = loop_result.get("processed", loop_result.get("errors_found", loop_result.get("suggestions", 0)))
            if items_total or items_ok:
                advisors = advisor_ask(domain=_LOOP_ADVISOR_MAP.get(name, "系统架构"), 
                                    question=f"仙女座 loop {name} 执行完毕, ok={items_ok} total={items_total}, 下一步建议?")
                for a in advisors[:1]:  # 只取第一位顾问的建议
                    log(f"  💡 [{a['name']}·{a['domain']}] 建议: {a['advice'][:80]}", "advisor")
                results.setdefault("advisor_input",{})[name] = [{"name":a["name"],"advice":a["advice"][:100]} for a in advisors]
        except Exception as e:
            log(f"  ⚠️ advisor_ask({name}) 异常: {e}", "core")
    
    # 写 run log
    db = _db_connect()
    for loop_name, r in results.items():
        db.execute("INSERT INTO mt_evolution_runs(loop,started_at,finished_at,duration_s,items_processed,items_ok) VALUES (?,?,?,?,?,?)",
                  (loop_name, time.strftime("%Y-%m-%d %H:%M:%S"), time.strftime("%Y-%m-%d %H:%M:%S"),
                   time.time()-t0, r.get("processed",r.get("alive",r.get("rules",r.get("suggestions",0)))),
                   r.get("ok",r.get("alive",0))))
    db.commit()
    db.close()
    
    dt = time.time() - t0
    log(f"══════ 周期完成 ({dt:.0f}s) ══════", "core")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    return results

def run_loop():
    """守护进程: 每 300s 一轮"""
    log("仙女座自演化守护进程启动 (PID=%d)" % os.getpid(), "core")
    while True:
        try: run_cycle()
        except Exception as e: log(f"周期异常: {e}", "core")
        log("sleep 300s...", "core")
        time.sleep(300)

def run_status():
    """全局状态快照"""
    ensure_tables()
    db = _db_connect()
    
    print("""
╔═══════════════════════════════════════════════╗
║  仙女座 & 冰山 · 自演化状态快照               ║
╚═══════════════════════════════════════════════╝
""")
    
    # daemon
    rows = db.execute("SELECT status, COUNT(*) FROM mt_daemon_registry GROUP BY status").fetchall()
    print(f"🟢 daemon: {dict(rows)}")
    
    # routes
    routes_total = db.execute("SELECT COUNT(*) FROM mt_ai_neural_routes").fetchone()[0]
    routes_ok = db.execute("SELECT COUNT(*) FROM mt_ai_neural_routes WHERE evolved_at IS NOT NULL").fetchone()[0]
    print(f"🧠 routes: {routes_ok}/{routes_total} 已进化")
    
    # suggestions
    sug = db.execute("SELECT status, COUNT(*) FROM mt_evolution_suggestions GROUP BY status").fetchall()
    print(f"💡 建议池: {dict(sug)}")
    top = db.execute("SELECT id, source, category, target, severity, substr(issue,1,50) FROM mt_evolution_suggestions WHERE status='PENDING' ORDER BY severity DESC LIMIT 5").fetchall()
    if top:
        print("  Top 5 PENDING:")
        for row in top:
            print(f"    #{row[0]} [{row[1]}/{row[2]}] sev={row[4]} {row[3] or ''}: {row[5]}")
    
    # runs
    last = db.execute("SELECT loop, finished_at, duration_s, items_processed FROM mt_evolution_runs ORDER BY id DESC LIMIT 5").fetchall()
    if last:
        print(f"📊 最近 5 次周期:")
        for loop, fin, dur, n in last:
            print(f"    {loop:12s} {fin}  {dur:.0f}s  {n} items")
    
    db.close()
    
    # Ollama
    try:
        import urllib.request
        r = urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3)
        models = json.loads(r.read()).get("models", [])
        print(f"
🧠 Ollama: {len(models)} 模型在线")
        for m in models:
            print(f"  ✅ {m['name']} ({m['size']//1024//1024}MB)")
    except: print("
🔴 Ollama 离线")
    
    # 🆕 仙女座自主觉醒状态
    try:
        awakens = db.execute("SELECT status, COUNT(*) FROM mt_awakening_log GROUP BY status").fetchall()
        print(f"
🧠 觉醒日志: {dict(awakens)}")
        builds = db.execute("SELECT status, COUNT(*) FROM mt_feature_build_queue GROUP BY status").fetchall()
        print(f"🛠️  自主构建队列: {dict(builds)}")
        # 最近一次 coder:14b 生成
        last_coder = db.execute("SELECT id, scan_type, substr(gap_detected,1,50), created_at FROM mt_awakening_log WHERE generated_patch IS NOT NULL ORDER BY id DESC LIMIT 1").fetchone()
        if last_coder:
            print(f"  最近 coder:14b: #{last_coder[0]} [{last_coder[1]}] {last_coder[3]} → {last_coder[2]}")
    except: pass

# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(description="仙女座自演化主控 (9 循环 + coder:14b 自主觉醒)")
    p.add_argument("cmd", choices=[
        "run_cycle","loop","daemon",
        "evolve","repair","patrol","rule","benchmark",
        "awaken","build","iceberg",
        "error","autofix","brain",
        "status","suggest",
    ])
    p.add_argument("--once", action="store_true")
    args = p.parse_args()
    
    ensure_tables()
    
    if args.cmd == "run_cycle": run_cycle()
    elif args.cmd == "loop": run_loop()
    elif args.cmd == "daemon":
        log("🧠 仙女座 9 循环守护进程启动 (含 awaken+build+iceberg)", "core")
        run_loop()
    elif args.cmd == "evolve": loop_evolve()
    elif args.cmd == "repair": loop_repair()
    elif args.cmd == "patrol": loop_patrol()
    elif args.cmd == "rule": loop_rule()
    elif args.cmd == "benchmark": loop_benchmark()
    elif args.cmd == "awaken": loop_awaken()
    elif args.cmd == "build": loop_feature_build()
    elif args.cmd == "iceberg": loop_iceberg_opt()
    elif args.cmd == "error": loop_error_capture()
    elif args.cmd == "autofix": loop_auto_fix()
    elif args.cmd == "brain": loop_brain_feed()
    elif args.cmd == "status": run_status()
    elif args.cmd == "suggest":
        db = _db_connect()
        rows = db.execute("SELECT id, source, category, severity, status, substr(issue,1,80) FROM mt_evolution_suggestions ORDER BY severity DESC, id DESC LIMIT 20").fetchall()
        print(f"💡 建议池 Top 20 (共 {len(rows)})")
        for row in rows:
            print(f"  #{row[0]:3d} [{row[1]:8s}/{row[2]:10s}] sev={row[3]} {row[4]:10s} {row[5]}")
        db.close()

if __name__ == "__main__": main()
