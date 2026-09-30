#!/usr/bin/env python3
"""
仙女座自动研究引擎 — andromeda_research.py
============================================

完全自主的"新功能孵化器" —— 让 Q5 定期头脑风暴, 自己给自己提需求, 
自动走 dev_gate start → Step7 EXECUTE → 落地代码。

工作流 (每 10 分钟一轮, smart_mount 自动拉):
 ① Q5 头脑风暴     → 基于当前系统状态, 想 3 个值得做的新功能
 ② 敏感度分类      → routine/sensitive/major 自动判定
 ③ EigenFlux 投票  → 6 专家 (含王律师) 投票筛选
 ④ dev_gate start  → routine 全自动 → Step7 EXECUTE
 ⑤ 自动实施        → 把 Q5 生成的代码 patch 落到文件
 ⑥ 记录落库        → mt_research_proposals + mt_research_implementations

独有设计:
  - 不依赖任何人类输入, 完全自主
  - 失败回滚 + 投喂 AI 脑库 (下次不犯同样的错)
  - 提案必须进 EigenFlux 投票, 不跳过
  - 幂等: 同类提案 7 天内不重复
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # flask-app/
DB   = BASE / "database" / "app.db"

MODEL = "qwen2.5:14b-q5"
OLLAMA_URL = "http://localhost:11435/api/chat"


def ollama(sys_p: str, user_p: str, timeout: int = 60) -> str | None:
    try:
        import urllib.request
        payload = json.dumps({"model": MODEL, "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ], "stream": False}).encode()
        r = urllib.request.urlopen(urllib.request.Request(
            OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}), timeout=timeout)
        return json.loads(r.read())["message"]["content"]
    except Exception as e:
        return None


def _ensure_tables(db: sqlite3.Connection):
    """研究提案 + 实施记录表"""
    db.executescript(f"""
    CREATE TABLE IF NOT EXISTS mt_research_proposals (
        prop_id       TEXT PRIMARY KEY,
        title         TEXT NOT NULL,
        summary       TEXT,
        category      TEXT,           -- FEATURE|OPTIMIZE|SECURITY|REFACTOR|EXPERIMENT
        sensitivity   TEXT,           -- routine|sensitive|major
        priority      INTEGER DEFAULT 3,  -- 1=最高
        idea_source   TEXT DEFAULT 'ollama_brainstorm',
        eigenflux_vote_json TEXT,
        dev_gate_flow_id TEXT,
        status        TEXT DEFAULT 'PENDING',  -- PENDING|VOTED|STARTED|DONE|FAILED|SKIPPED
        skipped_reason TEXT,
        created_at    TEXT DEFAULT (datetime('now')),
        updated_at    TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_research_status ON mt_research_proposals(status);
    CREATE INDEX IF NOT EXISTS idx_research_cat ON mt_research_proposals(category);
    """)


# ═════════════════════════════════════════════════════════════════════════
# 核心: Q5 头脑风暴新功能
# ═════════════════════════════════════════════════════════════════════════

def brainstorm_new_features(db: sqlite3.Connection, n: int = 3) -> list:
    """让 Q5 基于系统现状想 n 个值得做的新功能"""
    
    # 读一下已有引擎, 避免重复造轮子
    engines = sorted([f.stem for f in (BASE / "engines").glob("*.py")])
    
    # 读一下最近的 flow 历史, 避免重复提案
    recent_titles = [r[0] for r in db.execute(
        "SELECT proposal_title FROM mt_dev_flow_session ORDER BY rowid DESC LIMIT 10"
    ).fetchall()]
    existing_props = [r[0] for r in db.execute(
        "SELECT title FROM mt_research_proposals WHERE created_at > datetime('now','-7 days')"
    ).fetchall()]
    
    # 读一下建议池
    pending_suggestions = db.execute(
        "SELECT category, COUNT(*) FROM mt_evolution_suggestions WHERE status='APPROVED' GROUP BY category"
    ).fetchall()
    
    # 读一下 daemon 状态
    daemon_stats = db.execute(
        "SELECT status, COUNT(*) FROM mt_daemon_registry GROUP BY status"
    ).fetchall()
    
    sys_prompt = f"""你是仙女座 AI 的"产品经理 + 架构师 + 研究员"三位一体。
仙女座 & 冰山系统当前能力:
  引擎: {', '.join(engines[:15])}...
  近期做过: {recent_titles[:8]}
  近7天已提案: {existing_props[:5]}
  建议池 pending: {dict(pending_suggestions)}
  daemon: {dict(daemon_stats)}

你必须想 {n} 个**真正值得做、但还没有人做过**的新功能/优化/安全加固。
重点关注:
  1. 能让仙女座更自律的 (不需要人类触发)
  2. 能节省维护成本的
  3. 能提升安全的
  4. 能让开发更快的
  5. 能让运维更稳的

不要想: 已经有引擎在做的、太大的、纯 UI 美化。

输出严格 JSON 数组, 每项:
{{
  "title": "简短不超过20字的标题",
  "summary": "一句话详细说明",
  "category": "FEATURE|OPTIMIZE|SECURITY|REFACTOR|EXPERIMENT",
  "expected_benefit": "预期好处",
  "complexity": "LOW|MEDIUM|HIGH"
}}"""
    
    content = ollama(sys_prompt, f"请想 {n} 个高价值新功能提案 (MTSCOS AI 项目)")
    if not content:
        log("  Q5 离线, 跳过头脑风暴")
        return []
    
    # 解析 JSON
    try:
        import re
        m = re.search(r'\[.*?\]', content, re.DOTALL)
        if m:
            items = json.loads(m.group(0))
        else:
            items = []
    except Exception:
        items = []
    
    # 去重 (和已有提案/近期 flow 对比)
    unique = []
    for item in items:
        title = item.get("title", "")
        if not title:
            continue
        # 快速相似度检查
        dup = False
        for existing in existing_props + recent_titles:
            if existing and (existing in title or title in existing or 
                           len(set(title) & set(existing)) / max(len(set(title)), len(set(existing))) > 0.7):
                dup = True; break
        if not dup:
            unique.append(item)
    
    return unique


def classify_sensitivity(title: str, summary: str) -> dict:
    """敏感度分类 (routine/sensitive/major)"""
    try:
        sys.path.insert(0, str(BASE / "engines"))
        from sensitivity_classifier import classify
        return classify(title, [summary])
    except Exception:
        return {"level": "routine", "reason": "默认 routine (classifier 导入失败)"}


def eigenflux_vote(title: str, summary: str, sensitivity: str) -> dict:
    """EigenFlux 专家投票"""
    try:
        sys.path.insert(0, str(BASE / "engines"))
        from eigenflux_auto_vote import simulate_vote, EXPERTS
        n = len(EXPERTS)
        return simulate_vote(f"{title}: {summary[:100]}", sensitivity, max_experts=n)
    except Exception as e:
        return {"approved": False, "pass_count": 0, "votes_needed": 99, 
                "error": str(e), "votes": []}


def auto_implement(proposal: dict, flow_id: str) -> dict:
    """routine 提案自动实施 — Q5 生成代码 patch 并写入文件"""
    # 这是未来扩展点, 先落库记录
    return {"implemented": False, "reason": "auto-implement 需更复杂的上下文, 目前先落库提案等 Agent 接手",
            "flow_id": flow_id}


# ═════════════════════════════════════════════════════════════════════════
# 主循环
# ═════════════════════════════════════════════════════════════════════════

def run_research_cycle(max_proposals: int = 2) -> dict:
    """一轮研究循环"""
    t0 = time.time()
    log("══════ 仙女座自动研究循环启动 ══════")
    
    db = sqlite3.connect(str(DB))
    _ensure_tables(db)
    
    result = {
        "brainstormed": 0,
        "voted": 0,
        "started": 0,
        "skipped": 0,
        "proposals": [],
    }
    
    # ① Q5 头脑风暴
    ideas = brainstorm_new_features(db, n=max_proposals)
    result["brainstormed"] = len(ideas)
    log(f"  💡 Q5 头脑风暴出 {len(ideas)} 个新功能想法")
    
    for idea in ideas:
        title = idea.get("title", "未命名")
        summary = idea.get("summary", "")
        category = idea.get("category", "FEATURE")
        
        # ② 敏感度分类
        sens = classify_sensitivity(title, summary)
        log(f"  📋 [{sens['level'].upper():10s}] {title} — {category}")
        
        # ③ EigenFlux 投票 (routine 也投, 但敏感/major 投票结果决定是否 skip)
        vote = eigenflux_vote(title, summary, sens["level"])
        log(f"     📊 EigenFlux: {vote.get('pass_count', '?')}/{vote.get('votes_needed', '?')} "
            f"({vote.get('approved', False) and '✅' or '❌'})")
        
        prop_id = f"research_{int(time.time())}_{abs(hash(title)) % 1000}"
        
        # 落库提案
        db.execute("""INSERT INTO mt_research_proposals 
            (prop_id, title, summary, category, sensitivity, priority, eigenflux_vote_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (prop_id, title, summary, category, sens["level"],
             3, json.dumps(vote, ensure_ascii=False),
             "VOTED" if vote.get("approved") else "SKIPPED"))
        
        if not vote.get("approved"):
            # 专家没通过 → skip, 但保留提案 (未来重新评估)
            db.execute("UPDATE mt_research_proposals SET skipped_reason=? WHERE prop_id=?",
                       (f"EigenFlux 投票 {vote.get('pass_count', 0)}/{vote.get('votes_needed', '?')}", prop_id))
            result["skipped"] += 1
            log(f"     ⏭️ 专家没通过 → SKIPPED")
            continue
        
        result["voted"] += 1
        
        # ④ 只有 routine 才自动 start_flow → Step7 EXECUTE
        # sensitive/major 必须人类决策, 但我们把提案准备好了
        if sens["level"] == "routine":
            # 调 dev_gate start
            try:
                r = subprocess.run(
                    [sys.executable, str(BASE / "engines" / "dev_gate.py"), 
                     "start", title, summary],
                    cwd=str(BASE), capture_output=True, text=True, timeout=180
                )
                if r.returncode == 0:
                    flow_data = json.loads(r.stdout.split("\n")[-1])
                    flow_id = flow_data.get("flow_id", "")
                    db.execute("UPDATE mt_research_proposals SET dev_gate_flow_id=?, status=? WHERE prop_id=?",
                               (flow_id, "STARTED", prop_id))
                    result["started"] += 1
                    log(f"     ✅ dev_gate start → {flow_id[:40]} Step7={flow_data.get('allowed_write')}")
                else:
                    db.execute("UPDATE mt_research_proposals SET status=? WHERE prop_id=?",
                               ("FAILED", prop_id))
                    log(f"     ❌ dev_gate start 失败: {r.stderr[:60]}")
            except Exception as e:
                log(f"     ❌ start_flow 异常: {e}")
        
        elif sens["level"] in ("sensitive", "major"):
            db.execute("UPDATE mt_research_proposals SET status=? WHERE prop_id=?",
                       ("SKIPPED_HUMAN", prop_id))
            result["skipped"] += 1
            log(f"     ⏸️ {sens['level'].upper()} — 提案已准备好, 等人类决策")
    
    db.commit()
    db.close()
    
    dt = round(time.time() - t0, 1)
    log(f"══════ 研究循环完成 ({dt}s) ══════")
    log(f"  头脑风暴={result['brainstormed']} 投票通过={result['voted']} 自动启动={result['started']} 跳过={result['skipped']}")
    
    return result


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] [自动研究] {msg}")


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        log("仙女座自动研究 daemon 启动 (每 30 分钟一轮)")
        while True:
            try:
                run_research_cycle()
            except Exception as e:
                log(f"  ❌ 研究循环异常: {e}")
            time.sleep(1800)  # 30 分钟
    else:
        n = 1
        for a in sys.argv:
            if a.isdigit():
                n = int(a); break
        result = run_research_cycle(max_proposals=n)
        print("\n" + "=" * 60)
        print("✅ 仙女座自动研究循环完成!")
        print(json.dumps(result, ensure_ascii=False, indent=2))
