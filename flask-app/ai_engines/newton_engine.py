#!/usr/bin/env python3
"""
§二 牛顿归纳推理引擎 (Newtonian Induction Engine)
=================================================

核心理念: 从大量观察数据归纳出自然律
—— 给定一组观测事实 → 找出规律 → 提出假说 → 验证 → 存入 mt_derived_knowledge (source='newton')

与拉马努金发散引擎的区别:
  拉马努金 = 从少量前提 (公理/定义) → 发散推导结论 (演绎)
  牛顿     = 从大量观察数据 → 归纳出普遍规律 (归纳)

历史原型:
  牛顿看到苹果落地 + 月球绕地 + 潮汐 → 归纳出万有引力定律
  第谷行星观测 20 年 → 开普勒三定律 → 牛顿力学

Prompt 设计要点:
  1. 强制"从数据中归纳", 禁止直接用已知定律
  2. 要求列出所有观察事实, 然后找出其中的数学关系
  3. 要求提出可检验的预测 (如果定律成立, 那么 X 应该也成立)
  4. 要求反例扫描 (这个规律在哪种情况下会失效?)

质量门控:
  confidence >= 0.7 AND prediction_consistency >= 0.6 → 写入 mt_edu_creative_tricks

Author: Trae-Agent (flow_ramanujan_newton)
Date: 2026-09-18
Flow: flow_ramanujan_newton_1789704880
"""
import sqlite3, os, json, time, urllib.request, urllib.error
from datetime import datetime
from typing import Optional, Dict, List

# ==== 路径 (与 ramanujan_engine 统一) ====
_HERE = os.path.dirname(os.path.abspath(__file__))
_FLASK_APP = os.path.dirname(_HERE)
_APP_DB = os.path.join(_FLASK_APP, "database", "app.db")
# ⚠️ 不读 OLLAMA_HOST env — 避免被错误的 11434 覆盖
_OLLAMA = "http://localhost:11435"
_MODEL = os.environ.get("NEWTON_MODEL", "qwen2.5:14b")

# ==== 质量门控 ====
_CONFIDENCE_THRESHOLD = 0.7
_PREDICTION_CONSISTENCY_THRESHOLD = 0.6


def _db():
    conn = sqlite3.connect(_APP_DB, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables():
    """确保 mt_derived_knowledge 存在 + newton 列 + 索引"""
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
        # 牛顿专有扩展表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mt_inductive_laws (
                law_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                law_name        TEXT NOT NULL,
                subject         TEXT,
                observed_data   TEXT,         -- 观测事实 JSON
                inductive_steps TEXT,         -- 归纳步骤 JSON
                hypothesis      TEXT,         -- 假说/定律陈述
                testable_predictions TEXT,    -- 可检验预测 JSON
                counter_examples TEXT,        -- 反例 JSON
                confidence      REAL DEFAULT 0.0,
                prediction_consistency REAL DEFAULT 0.0,
                law_status      TEXT DEFAULT 'proposal',  -- proposal/tested/verified/falsified
                model_used      TEXT,
                user_id         TEXT DEFAULT 'system',
                source          TEXT DEFAULT 'newton',
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                updated_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_law_name ON mt_inductive_laws(law_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_il_subject ON mt_inductive_laws(subject)")
        conn.commit()


# ==== 核心 Prompt ====
NEWTON_SYSTEM = """你是牛顿式的归纳推理引擎。核心规则:
1. 不允许直接引用已知物理/数学定律
2. 必须从给定的观测数据/事实中独立归纳出规律
3. 每一步标注: [观察] / [假设] / [归纳] / [定律]
4. 必须提出至少 3 条可检验预测 (如果定律成立, 那么 X 应该成立)
5. 必须扫描反例边界 (这个规律在哪种条件下会失效?)
6. 置信度评估: 数据量、一致性、预测可检验性

输出必须是严格 JSON:
{
  "law_name": "定律/规律名称",
  "observations": [{"obs_id": 1, "fact": "观察事实", "source": "数据来源"}],
  "inductive_steps": [{"step": 1, "type": "观察/假设/归纳/抽象", "content": "...", "reasoning": "..."}],
  "hypothesis": "归纳出的定律/规律陈述",
  "mathematical_formulation": "数学表达式 (如适用)",
  "predictions": [{"prediction": "可检验预测", "test_method": "如何检验", "expected_result": "..."}],
  "counter_examples": [{"condition": "失效条件", "reason": "为什么不适用"}],
  "confidence": 0.0-1.0,
  "prediction_consistency": 0.0-1.0
}"""


def induce(observations: str, subject: str = "physics", law_name_hint: str = "",
           user_id: str = "system", model: str = None, timeout: int = 180) -> Dict:
    """
    对一组观测数据执行牛顿式归纳推理
    
    observations: 一段观测事实/数据描述 (可以是自然语言或结构化文本)
    subject: 学科领域
    law_name_hint: 可选, 对规律名称的提示
    """
    ensure_tables()
    tag = model or _MODEL
    
    hint = f"提示定律名称: {law_name_hint}\n" if law_name_hint else ""
    prompt = f"""从以下观测数据/事实中归纳出普遍规律。

{hint}
观测数据:
{observations}

学科: {subject}

像牛顿一样思考 —— 从第谷 20 年行星观测数据中归纳开普勒三定律，
从苹果落地+月球+潮汐中归纳万有引力定律。"""

    payload = {
        "model": tag,
        "messages": [
            {"role": "system", "content": NEWTON_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 1600}  # 稍高温让归纳有创造性
    }

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

    parsed = _extract_json(raw)
    if not parsed:
        return {"success": False, "error": "JSON 解析失败", "raw": raw[:400]}

    confidence = float(parsed.get("confidence", 0.5))
    pred_consistency = float(parsed.get("prediction_consistency", 0.5))
    law_name = parsed.get("law_name", law_name_hint or "未命名归纳规律")
    
    # ═══ 质量门控 ═══
    quality_pass = (confidence >= _CONFIDENCE_THRESHOLD and 
                    pred_consistency >= _PREDICTION_CONSISTENCY_THRESHOLD)
    law_status = "tested" if quality_pass else "proposal"

    obs_json = json.dumps(parsed.get("observations", []), ensure_ascii=False)
    steps_json = json.dumps(parsed.get("inductive_steps", []), ensure_ascii=False)
    preds_json = json.dumps(parsed.get("predictions", []), ensure_ascii=False)
    counter_json = json.dumps(parsed.get("counter_examples", []), ensure_ascii=False)
    hypothesis = parsed.get("hypothesis", "")

    with _db() as conn:
        cur = conn.execute("""
            INSERT INTO mt_inductive_laws 
                (law_name, subject, observed_data, inductive_steps, hypothesis,
                 testable_predictions, counter_examples, confidence, prediction_consistency,
                 law_status, model_used, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (law_name, subject, obs_json, steps_json, hypothesis,
              preds_json, counter_json, confidence, pred_consistency,
              law_status, tag, user_id))
        law_id = cur.lastrowid

        # 同步写入 mt_derived_knowledge (source='newton')
        combined = f"定律: {law_name}\n{hypothesis}\n\n归纳步骤:\n{steps_json}"
        conn.execute("""
            INSERT INTO mt_derived_knowledge 
                (concept, subject, derivation_chain, verification, confidence, 
                 model_used, user_id, verification_status, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'newton')
        """, (law_name, subject, combined, 
              json.dumps({"predictions": preds_json, "counter": counter_json}, ensure_ascii=False),
              confidence, tag, user_id, "verified" if quality_pass else "quality_gate_fail"))

        # 质量门控通过 → 同步到 mt_edu_creative_tricks
        if quality_pass:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                subject_cn = {"physics": "物理", "chemistry": "化学", "mathematics": "数学",
                              "biology": "生物", "engineering": "工科", "economics": "经济学"}.get(subject, subject)
            except: subject_cn = subject
            tricks_title = f"[牛顿] {law_name[:50]}"
            dedup = conn.execute("SELECT trick_code FROM mt_edu_creative_tricks WHERE title=?", (tricks_title,)).fetchone()
            if not dedup:
                formulation = parsed.get("mathematical_formulation", "")
                desc = f"{hypothesis[:150]}\n数学表达: {formulation[:100]}" if formulation else hypothesis[:200]
                conn.execute("""INSERT INTO mt_edu_creative_tricks 
                    (trick_code, subject, grade, title, category, difficulty, effectiveness_score, ai_quality_pass, description, author_type, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (f"RN_NEW_{law_id:04d}", subject_cn, "通用", tricks_title, "newton",
                     min(5, max(1, int(round(confidence * 5)))),
                     round(confidence * 100, 1), 1, desc, "newton_engine", now))
        conn.commit()

    return {
        "success": True,
        "law_id": law_id,
        "law_name": law_name,
        "hypothesis": hypothesis[:300],
        "observations_count": len(parsed.get("observations", [])),
        "inductive_steps_count": len(parsed.get("inductive_steps", [])),
        "predictions_count": len(parsed.get("predictions", [])),
        "counter_examples_count": len(parsed.get("counter_examples", [])),
        "confidence": confidence,
        "prediction_consistency": pred_consistency,
        "quality_pass": quality_pass,
        "law_status": law_status,
        "model": tag,
        "elapsed_s": round(elapsed, 1),
        "tricks_synced": quality_pass,
    }


def _extract_json(text: str) -> Optional[Dict]:
    """健壮 JSON 提取 (复用 ramanujan_engine 逻辑)"""
    import re
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if m:
        try: return json.loads(m.group(1))
        except: pass
    li, ri = text.find('{'), text.rfind('}')
    if li >= 0 and ri > li:
        try: return json.loads(text[li:ri+1])
        except: pass
    return None


def list_laws(subject: str = None, limit: int = 20, law_status: str = None) -> List[Dict]:
    ensure_tables()
    with _db() as conn:
        sql = "SELECT * FROM mt_inductive_laws WHERE 1=1"
        params = []
        if subject: sql += " AND subject=?"; params.append(subject)
        if law_status: sql += " AND law_status=?"; params.append(law_status)
        sql += " ORDER BY confidence DESC LIMIT ?"; params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def batch_induce(observation_sets: List[Dict], user_id: str = "system", model: str = None) -> Dict:
    """批量归纳"""
    import threading
    results = {"total": len(observation_sets), "done": 0, "success": 0, "results": []}
    lock = threading.Lock()

    def _worker(c):
        r = induce(
            observations=c["observations"],
            subject=c.get("subject", "physics"),
            law_name_hint=c.get("law_name_hint", ""),
            user_id=user_id, model=model,
        )
        with lock:
            results["done"] += 1
            if r.get("success"): results["success"] += 1
            results["results"].append(r)

    threads = [threading.Thread(target=_worker, args=(c,), daemon=True) for c in observation_sets]
    for t in threads: t.start()
    for t in threads: t.join(timeout=240)
    return results


# ==== 预置归纳场景 (零 token 启动) ====
PRESET_SCENARIOS = [
    {
        "law_name_hint": "速度-时间-距离关系",
        "subject": "physics",
        "observations": """
观察 1: 汽车从静止出发, 1 秒后速度 10 m/s, 2 秒后 20 m/s, 3 秒后 30 m/s
观察 2: 苹果从树上落下, 第 1 秒落下 5 m, 第 2 秒 15 m, 第 3 秒 25 m
观察 3: 子弹发射后速度从 400 m/s 降到 380 m/s, 再到 360 m/s
观察 4: 卫星绕地运行, 周期 T 与轨道半径 r 的 3/2 次方成正比 (从开普勒第三定律已知, 但假装不知道)
"""
    },
    {
        "law_name_hint": "理想气体状态方程",
        "subject": "physics",
        "observations": """
观察 1: 温度不变时, 气体体积减半 → 压力加倍 (pV = 常数)
观察 2: 压力不变时, 温度升高 1°C → 体积膨胀 1/273
观察 3: 体积不变时, 压力与温度成正比
观察 4: 相同条件下, 不同气体 1 mol 体积相同 (阿伏伽德罗常数)
"""
    },
    {
        "law_name_hint": "生物演化自然选择",
        "subject": "biology",
        "observations": """
观察 1: 工业革命前英国桦尺蠖浅色多, 革命后黑色多
观察 2: 加拉帕戈斯群岛 14 种雀鸟来自同一祖先, 喙形因食物不同而异
观察 3: 抗生素使用越多, 耐药菌株出现越快
观察 4: 人类镰刀型细胞杂合子抗疟疾, 但纯合子患镰刀型贫血
"""
    },
]


if __name__ == "__main__":
    import sys
    ensure_tables()
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 newton_engine.py induce <observations_file> [subject]")
        print("  python3 newton_engine.py preset [index]  # 0/1/2 或 all")
        print("  python3 newton_engine.py list [subject]")
        sys.exit(0)
    
    cmd = sys.argv[1]
    if cmd == "induce":
        obs_file = sys.argv[2]
        subject = sys.argv[3] if len(sys.argv) > 3 else "physics"
        with open(obs_file) as f: obs = f.read()
        r = induce(observations=obs, subject=subject)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    
    elif cmd == "preset":
        idx = sys.argv[2] if len(sys.argv) > 2 else "0"
        if idx == "all":
            results = batch_induce([{"observations": s["observations"], "subject": s["subject"], "law_name_hint": s["law_name_hint"]} for s in PRESET_SCENARIOS])
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            s = PRESET_SCENARIOS[int(idx)]
            r = induce(**s)
            print(json.dumps(r, ensure_ascii=False, indent=2))
    
    elif cmd == "list":
        subj = sys.argv[2] if len(sys.argv) > 2 else None
        for r in list_laws(subject=subj):
            print(f"#{r['law_id']} [{r['subject']}] {r['law_name'][:50]} conf={r['confidence']:.2f} status={r['law_status']}")
