#!/usr/bin/env python3
"""
§一 拉马努金动态衍生引擎 (Ramanujan Derivation Engine)
======================================================

核心理念: 不要记忆，要自我推导
—— 给定一个数学/科学问题 → 强制模型自己推导 → 验证 → 存入 mt_derived_knowledge

Prompt 设计要点:
  1. 强制"从零开始推导"（禁止直接背答案）
  2. 要求每一步标注假设 + 理由
  3. 要求自我验证（答案合理吗？极端情况成立吗？）
  4. 结构化 JSON 输出

表结构: mt_derived_knowledge
  concept, derivation_chain, verification, confidence, model_used, user_id, created_at

CLI:
  python3 ramanujan_engine.py derive --concept "为什么 e^iπ = -1"
  python3 ramanujan_engine.py batch --file concepts.json
  python3 ramanujan_engine.py verify --id 1
"""
import sqlite3, os, json, time, urllib.request, urllib.error
from datetime import datetime
from typing import Optional, Dict, List

# ==== 路径 ====
_APP_DB = os.path.expanduser("~/mtscos/_runtime/databases/Database/app.db")
_OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_MODEL = os.environ.get("RAMANUJAN_MODEL", "qwen2.5:7b")

def _db():
    conn = sqlite3.connect(_APP_DB, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables():
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mt_derived_knowledge (
                knowledge_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                concept         TEXT NOT NULL,
                subject         TEXT DEFAULT 'mathematics',
                derivation_chain TEXT,
                verification    TEXT,
                confidence      REAL DEFAULT 0.0,
                verification_status TEXT DEFAULT 'pending',
                model_used      TEXT,
                user_id         TEXT DEFAULT 'system',
                source          TEXT DEFAULT 'ramanujan',
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                updated_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dk_concept ON mt_derived_knowledge(concept)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dk_subject ON mt_derived_knowledge(subject)")
        conn.commit()

# ==== 核心 Prompt ====
RAMANUJAN_SYSTEM = """你是拉马努金式的自我推导引擎。核心规则:
1. 不允许直接背诵答案或引用教科书
2. 必须从零开始，像第一次发现这个公式/定理一样推导
3. 每一步标注: [假设] / [定义] / [推导] / [结论]
4. 最后做自我验证: 极端情况? 维度检查? 量纲一致? 特殊值?

输出必须是严格 JSON:
{
  "concept": "问题",
  "derivation_steps": [{"step": 1, "type": "假设/定义/推导", "content": "...", "reason": "..."}],
  "final_result": "...",
  "self_verification": {"extreme_case": "...", "dimensional_check": "...", "edge_test": "...", "is_valid": true/false},
  "confidence": 0.0-1.0
}"""

def derive(concept: str, subject: str = "mathematics", user_id: str = "system",
           model: str = None, timeout: int = 120) -> Dict:
    """对一个概念执行拉马努金推导"""
    ensure_tables()
    tag = model or _MODEL
    prompt = f"""请从零开始推导这个概念，禁止直接给答案。

问题: {concept}
学科: {subject}

像拉马努金一样思考 —— 不用已知公式，用最基础的定义重新发现。"""

    payload = {
        "model": tag,
        "messages": [
            {"role": "system", "content": RAMANUJAN_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1200}  # 低温度确保 JSON 稳定
    }

    # 调 Ollama
    try:
        req = urllib.request.Request(
            f"{_OLLAMA}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read()).get("message", {}).get("content", "")
            elapsed = time.time() - t0
    except Exception as e:
        return {"success": False, "error": f"Ollama 失败: {e}"}

    # 提取 JSON
    parsed = _extract_json(raw)
    if not parsed:
        return {"success": False, "error": "JSON 解析失败", "raw": raw[:300]}

    # 存库
    derivation = json.dumps(parsed.get("derivation_steps", []), ensure_ascii=False)
    verification = json.dumps(parsed.get("self_verification", {}), ensure_ascii=False)
    confidence = float(parsed.get("confidence", 0.5))

    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO mt_derived_knowledge (concept, subject, derivation_chain, verification, confidence, model_used, user_id, verification_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (concept, subject, derivation, verification, confidence, tag, user_id,
             "verified" if parsed.get("self_verification", {}).get("is_valid") else "unverified"))
        kid = cur.lastrowid
        conn.commit()

    return {
        "success": True,
        "knowledge_id": kid,
        "concept": concept,
        "steps_count": len(parsed.get("derivation_steps", [])),
        "result": parsed.get("final_result", "")[:200],
        "confidence": confidence,
        "is_valid": parsed.get("self_verification", {}).get("is_valid"),
        "model": tag,
        "elapsed_s": round(elapsed, 1),
    }

def _extract_json(text: str) -> Optional[Dict]:
    """健壮 JSON 提取：直接 parse → ```json 包裹 → 首{末}"""
    # 1. 直接 parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2. ```json 包裹
    import re
    m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if m:
        try: return json.loads(m.group(1))
        except: pass
    # 3. 首{末}
    li, ri = text.find('{'), text.rfind('}')
    if li >= 0 and ri > li:
        try: return json.loads(text[li:ri+1])
        except: pass
    return None

def _hydrate_row(d: Dict) -> Dict:
    """把 DB 里存成 TEXT 的 JSON 字段反序列化成对象.

    容错处理:
    - Markdown ```json 代码块包裹
    - JSON 前后夹杂模型文字 (取第一个 {..} 或 [..])
    - 不是合法 JSON 就保留原字符串
    """
    import json as _j, re as _re

    def _try_load(text):
        if not isinstance(text, str) or not text.strip():
            return text
        s = text.strip()
        # 1) 剥 ```json ... ``` 包裹
        m = _re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s)
        if m:
            s = m.group(1).strip()
        # 2) 直接尝试
        try:
            return _j.loads(s)
        except Exception:
            pass
        # 3) 容错: 提取第一个 {...} 或 [...]
        for opener, closer in [("{", "}"), ("[", "]")]:
            li = s.find(opener)
            ri = s.rfind(closer)
            if li != -1 and ri != -1 and ri > li:
                try:
                    return _j.loads(s[li : ri + 1])
                except Exception:
                    pass
        # 都不行 → 返回原字符串
        return text

    for col in ("derivation_chain", "verification"):
        d[col] = _try_load(d.get(col))
    return d

def list_knowledge(subject: str = None, limit: int = 20) -> List[Dict]:
    ensure_tables()
    with _db() as conn:
        if subject:
            rows = conn.execute(
                "SELECT * FROM mt_derived_knowledge WHERE subject=? ORDER BY created_at DESC LIMIT ?",
                (subject, limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM mt_derived_knowledge ORDER BY created_at DESC LIMIT ?",
                (limit,)).fetchall()
    return [_hydrate_row(dict(r)) for r in rows]

def get_knowledge(kid: int) -> Optional[Dict]:
    ensure_tables()
    with _db() as conn:
        row = conn.execute("SELECT * FROM mt_derived_knowledge WHERE knowledge_id=?", (kid,)).fetchone()
        return _hydrate_row(dict(row)) if row else None

def batch_derive(concepts: List[Dict], user_id: str = "system", model: str = None) -> Dict:
    """批量推导 — 多线程真并行"""
    import threading
    results = {"total": len(concepts), "done": 0, "success": 0, "results": []}
    lock = threading.Lock()

    def _worker(c):
        r = derive(
            concept=c["concept"],
            subject=c.get("subject", "mathematics"),
            user_id=user_id,
            model=model,
        )
        with lock:
            results["done"] += 1
            if r.get("success"): results["success"] += 1
            results["results"].append(r)

    threads = [threading.Thread(target=_worker, args=(c,), daemon=True) for c in concepts]
    for t in threads: t.start()
    for t in threads: t.join(timeout=180)

    return results

if __name__ == "__main__":
    import sys
    ensure_tables()
    if len(sys.argv) < 2:
        print("用法: python3 ramanujan_engine.py derive <concept> [subject]")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "derive":
        concept = sys.argv[2] if len(sys.argv) > 2 else "为什么导数是切线斜率"
        subject = sys.argv[3] if len(sys.argv) > 3 else "mathematics"
        r = derive(concept=concept, subject=subject)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif cmd == "list":
        for r in list_knowledge():
            print(f"#{r['knowledge_id']} [{r['subject']}] {r['concept'][:50]} conf={r['confidence']:.2f} model={r['model_used']}")
