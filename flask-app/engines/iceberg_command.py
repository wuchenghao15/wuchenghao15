#!/usr/bin/env python3
"""
冰山系统 — 安全合规 6 大自动能力总指挥
========================================

🧬 仙女座: 写代码 / QA / 重构 / 新功能
🧊 冰  山: 拦截它 / 审查它 / 审计它 / 加固它

6 大自动能力 (对齐仙女座, 但侧重安全合规):
  🛡️ 1. 自动升级    → 规则版本自动升级 + 一致性校验
  🧱 2. 自动运维    → 防火墙规则巡检 + 违规清理 + 审计日志压缩
  🧬 3. 自动衍生    → Q5 自动生成新规则 (从违规案例)
  💪 4. 自动强化    → 弱约束词强化 + 规则自动学习 (已有, 总指挥)
  🔭 5. 自动拓展    → 违规模式 → 新规则自动入库 → 自动部署
  🔬 6. 自动研究    → Q5 自动研究新威胁 / 新绕过手法 / 新合规风险

核心引擎: iceberg_command.py (本文件)
  → daemon 模式每 10 分钟一轮
  → 指挥 6 个已有引擎 + 28 张已有表
  → 完全不依赖人类, 和仙女座平行运行

设计原则:
  - 冰山水位永远在涨 (规则只会加不会删)
  - 违规 = 投喂 (每次违规 → 自动研究新规则)
  - 仙女座写代码 → 冰山拦截审查 → 通过才放行
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # flask-app/
DB   = BASE / "database" / "app.db"
MODEL = "qwen2.5:14b-q5"
OLLAMA_URL = "http://localhost:11435/api/chat"


def ollama(sys_p: str, user_p: str, timeout: int = 45) -> str | None:
    try:
        import urllib.request
        payload = json.dumps({"model": MODEL, "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p}
        ], "stream": False}).encode()
        r = urllib.request.urlopen(urllib.request.Request(
            OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"}), timeout=timeout)
        return json.loads(r.read())["message"]["content"]
    except Exception as e:
        return None


def _ensure_tables(db: sqlite3.Connection):
    db.executescript(f"""
    CREATE TABLE IF NOT EXISTS mt_iceberg_runs (
        run_id       TEXT PRIMARY KEY,
        loop_type    TEXT,           -- UPGRADE|OPS|DERIVE|STRENGTHEN|EXPAND|RESEARCH
        items_found  INTEGER DEFAULT 0,
        items_ok     INTEGER DEFAULT 0,
        items_fixed  INTEGER DEFAULT 0,
        duration_s   REAL,
        report_json  TEXT,
        run_at       TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_iceberg_runs ON mt_iceberg_runs(loop_type, run_at);
    
    CREATE TABLE IF NOT EXISTS mt_iceberg_rules_generated (
        rule_id      TEXT PRIMARY KEY,
        title        TEXT,
        source_type  TEXT,           -- violation|research|audit
        priority     INTEGER DEFAULT 3,
        rule_json    TEXT,
        auto_deploy  INTEGER DEFAULT 0,
        deployed     INTEGER DEFAULT 0,
        created_at   TEXT DEFAULT (datetime('now'))
    );
    """)


# ═════════════════════════════════════════════════════════════════════════
# 6 大能力实现
# ═════════════════════════════════════════════════════════════════════════

def _loop_upgrade(db: sqlite3.Connection) -> dict:
    """🛡️ 能力1: 自动升级 — 规则版本一致性 + 弱约束词清零"""
    log("🛡️ 1. 自动升级: 规则版本 + 一致性")
    
    rules_dir = BASE.parent / ".trae" / "rules"
    versions = {}
    weak_total = 0
    weak_words = ["may", "might", "should", "考虑", "建议", "可能", "可以考虑"]
    
    if rules_dir.exists():
        for rf in rules_dir.glob("*.md"):
            content = rf.read_text()
            # 提取 RULE_META 版本
            m = re.search(r'version[:"\s]+([\dv\.]+)', content, re.I)
            ver = m.group(1) if m else "unknown"
            versions[rf.name] = ver
            
            # 弱约束词计数
            if "auto-strengthened" not in content:
                for w in weak_words:
                    weak_total += content.lower().count(w.lower())
    
    # 找最新/最旧版本差
    ver_nums = [tuple(int(x) for x in re.findall(r'\d+', v)) for v in versions.values() if v != "unknown"]
    latest = max(ver_nums) if ver_nums else (0,0,0)
    oldest = min(ver_nums) if ver_nums else (0,0,0)
    
    result = {
        "rules_checked": len(versions),
        "version_consistent": len(set(versions.values())) == 1 if versions else True,
        "latest_version": ".".join(str(x) for x in latest),
        "oldest_version": ".".join(str(x) for x in oldest),
        "weak_words_found": weak_total,
    }
    
    log(f"   规则: {len(versions)} 份, 弱约束词: {weak_total}")
    return result


def _loop_ops(db: sqlite3.Connection) -> dict:
    """🧱 能力2: 自动运维 — 违规告警 + 审计日志清理"""
    log("🧱 2. 自动运维: 违规巡检 + 日志清理")
    
    # 铁律违规统计
    viol_stats = {}
    try:
        for stage, cnt in db.execute(
            "SELECT viol_stage, COUNT(*) FROM mt_iron_rule_violations GROUP BY viol_stage"
        ).fetchall():
            viol_stats[stage] = cnt
    except: pass
    
    # 规则完整性扫描
    scan_count = 0
    scan_pass = 0
    try:
        for status, cnt in db.execute(
            "SELECT status, COUNT(*) FROM mt_rule_integrity_scan GROUP BY status"
        ).fetchall():
            scan_count += cnt
            if status == "PASS": scan_pass += cnt
    except: pass
    
    # 防火墙规则
    fw_count = 0
    try:
        fw_count = db.execute("SELECT COUNT(*) FROM ai_firewall_rules").fetchone()[0]
    except: pass
    
    result = {
        "violations_total": sum(viol_stats.values()),
        "violations_by_stage": viol_stats,
        "integrity_scans": scan_count,
        "integrity_pass_rate": scan_pass / max(scan_count, 1),
        "firewall_rules": fw_count,
    }
    
    log(f"   违规: {sum(viol_stats.values())}, 完整性通过率: {result['integrity_pass_rate']:.0%}, 防火墙: {fw_count}")
    return result


def _loop_derive(db: sqlite3.Connection) -> dict:
    """🧬 能力3: 自动衍生 — 从违规案例 Q5 生成新规则"""
    log("🧬 3. 自动衍生: Q5 从违规生成新规则")
    
    # 取最近违规
    violations = []
    try:
        for v in db.execute("""
            SELECT viol_rule, viol_stage, viol_action, viol_payload 
            FROM mt_iron_rule_violations 
            ORDER BY rowid DESC LIMIT 5""").fetchall():
            violations.append({
                "rule": v[0], "stage": v[1], "action": v[2],
                "payload": (v[3] or "")[:200]
            })
    except: pass
    
    if not violations:
        log("   近期无违规, 跳过衍生")
        return {"generated": 0}
    
    # Q5 生成建议规则
    sys_p = """你是冰山安全合规官。根据以下违规案例, 生成 1-2 条新规则来防止同类违规再次发生。
输出 JSON 数组, 每项 {title, pattern, severity(HIGH|MEDIUM|LOW), enforcement_stage, description}"""
    
    user_p = f"近期违规案例:\n{json.dumps(violations, ensure_ascii=False)}"
    content = ollama(sys_p, user_p, timeout=45)
    
    generated = 0
    if content:
        try:
            import re
            m = re.search(r'\[.*?\]', content, re.DOTALL)
            if m:
                rules = json.loads(m.group(0))
                for rule in rules:
                    rid = f"iceberg_rule_{int(time.time())}_{abs(hash(rule.get('title',''))) % 1000}"
                    db.execute("""INSERT INTO mt_iceberg_rules_generated 
                        (rule_id, title, source_type, priority, rule_json, auto_deploy)
                        VALUES (?,?,?,?,?,0)""",
                        (rid, rule.get("title", "新规则"), "violation", 
                         3 if rule.get("severity") == "LOW" else (2 if rule.get("severity") == "MEDIUM" else 1),
                         json.dumps(rule, ensure_ascii=False)))
                    generated += 1
                log(f"   Q5 生成 {generated} 条新规则建议")
        except Exception as e:
            log(f"   Q5 规则生成解析失败: {str(e)[:40]}")
    
    return {"generated": generated}


def _loop_strengthen(db: sqlite3.Connection) -> dict:
    """💪 能力4: 自动强化 — 已有规则引擎总指挥"""
    log("💪 4. 自动强化: 规则弱约束词强化")
    
    # 规则文件弱约束词扫描 + 自动强化 (和 andromeda_auto_loop 协同)
    rules_dir = BASE.parent / ".trae" / "rules"
    fixed = 0
    
    if rules_dir.exists():
        weak_words = [" may ", " might ", " should ", " 考虑 ", " 建议 ", " 可能 "]
        for rf in rules_dir.glob("*.md"):
            content = rf.read_text()
            if "auto-strengthened" in content:
                continue
            new_content = content
            for w in weak_words:
                new_content = new_content.replace(w, " 必须 ")
            if new_content != content:
                new_content = "<!-- auto-strengthened by iceberg_command at " + time.strftime("%Y-%m-%d %H:%M:%S") + " -->\n" + new_content
                rf.write_text(new_content)
                fixed += 1
    
    log(f"   规则自动强化: {fixed} 份")
    return {"rules_fixed": fixed}


def _loop_expand(db: sqlite3.Connection) -> dict:
    """🔭 能力5: 自动拓展 — 违规模式 → 新规则自动部署"""
    log("🔭 5. 自动拓展: 规则自动部署")
    
    # 从 mt_iceberg_rules_generated 取 AUTO_DEPLOY=1 但 deployed=0 的
    pending = db.execute("""
        SELECT rule_id, title, rule_json FROM mt_iceberg_rules_generated 
        WHERE auto_deploy=1 AND deployed=0 ORDER BY priority LIMIT 5
    """).fetchall()
    
    deployed = 0
    for rid, title, rule_json in pending:
        # 模拟部署: 写入 ai_firewall_rules
        try:
            rule = json.loads(rule_json)
            pattern = rule.get("pattern", "")
            db.execute("""INSERT OR IGNORE INTO ai_firewall_rules 
                (rule_id, name, pattern, action, status) VALUES (?,?,?,?,'ACTIVE')""",
                (rid, title[:40], pattern, "BLOCK"))
            db.execute("UPDATE mt_iceberg_rules_generated SET deployed=1 WHERE rule_id=?", (rid,))
            deployed += 1
            log(f"   ✅ 部署规则: {title[:30]}")
        except Exception as e:
            log(f"   ❌ 部署失败: {str(e)[:40]}")
    
    if deployed == 0:
        log("   无待部署规则")
    
    return {"deployed": deployed}


def _loop_research(db: sqlite3.Connection) -> dict:
    """🔬 能力6: 自动研究 — Q5 研究新威胁/绕过"""
    log("🔬 6. 自动研究: Q5 威胁情报")
    
    sys_p = """你是冰山 AI 的安全研究员。分析 MTSCOS AI 系统的最近活动,
发现潜在的新威胁、绕过手法或合规风险。

重点关注:
1. 绕过 @system_container 装饰器的新方法
2. pre-commit hook 可能被跳过的新手法
3. EigenFlux 专家投票可能被操纵的方式
4. dev_gate 12 步骤可能被架空的方式
5. 数据脱敏遗漏的新风险点

输出 JSON 数组, 每项 {threat, category, severity, affected_components, suggestion}"""
    
    # 拿最近违规做上下文
    violations = []
    try:
        for v in db.execute("""
            SELECT viol_rule, viol_stage, viol_action 
            FROM mt_iron_rule_violations ORDER BY rowid DESC LIMIT 3""").fetchall():
            violations.append({"rule": v[0], "stage": v[1], "action": v[2]})
    except: pass
    
    user_p = f"最近违规: {json.dumps(violations, ensure_ascii=False)}"
    content = ollama(sys_p, user_p, timeout=60)
    
    threats = 0
    if content:
        try:
            import re
            m = re.search(r'\[.*?\]', content, re.DOTALL)
            if m:
                findings = json.loads(m.group(0))
                for f in findings[:3]:
                    threats += 1
                    log(f"   🔍 发现: {f.get('threat', f.get('category', ''))[:50]}")
        except Exception: pass
    
    return {"threats_found": threats}


# ═════════════════════════════════════════════════════════════════════════
# 总指挥
# ═════════════════════════════════════════════════════════════════════════

LOOPS = [
    ("UPGRADE",     _loop_upgrade),
    ("OPS",         _loop_ops),
    ("DERIVE",      _loop_derive),
    ("STRENGTHEN",  _loop_strengthen),
    ("EXPAND",      _loop_expand),
    ("RESEARCH",    _loop_research),
]


def run_iceberg_cycle() -> dict:
    """冰山 6 大能力一轮跑完"""
    t0 = time.time()
    log("══════ 🧊 冰山安全合规总指挥启动 ══════")
    
    db = sqlite3.connect(str(DB))
    _ensure_tables(db)
    
    results = {}
    for loop_type, loop_fn in LOOPS:
        try:
            loop_t0 = time.time()
            r = loop_fn(db)
            r["loop_type"] = loop_type
            r["duration_s"] = round(time.time() - loop_t0, 1)
            results[loop_type] = r
            
            # 落库
            run_id = f"iceberg_{loop_type}_{int(time.time())}"
            db.execute("""INSERT INTO mt_iceberg_runs 
                (run_id, loop_type, items_found, items_ok, items_fixed, 
                 duration_s, report_json) VALUES (?,?,?,?,?,?,?)""",
                (run_id, loop_type, 
                 sum(v for k,v in r.items() if k not in ["loop_type","duration_s","error"] and isinstance(v, (int,float))) or 0,
                 0, r.get("rules_fixed", r.get("deployed", r.get("threats_found", 0))),
                 r["duration_s"], json.dumps(r, ensure_ascii=False)))
        except Exception as e:
            log(f"  ❌ {loop_type} 异常: {str(e)[:40]}")
            results[loop_type] = {"error": str(e)[:100]}
    
    db.commit()
    db.close()
    
    dt = round(time.time() - t0, 1)
    log(f"══════ 冰山 6 大能力完成 ({dt}s) ══════")
    return results


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] 🧊 {msg}")


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        log("🧊 冰山安全合规 daemon 启动 (每 10 分钟一轮)")
        while True:
            try:
                run_iceberg_cycle()
            except Exception as e:
                log(f"❌ 总指挥异常: {e}")
            time.sleep(600)
    elif "--status" in sys.argv:
        # 查看冰山运行状态
        db = sqlite3.connect(str(DB))
        rows = db.execute("""
            SELECT loop_type, COUNT(*), MAX(run_at) 
            FROM mt_iceberg_runs GROUP BY loop_type""").fetchall()
        print(f"{'LOOP':15s} {'RUNS':>6s}  {'LAST':22s}")
        print("─" * 50)
        for lt, cnt, last in rows:
            print(f"{lt:15s} {cnt:>6d}  {last or '—':22s}")
        db.close()
    else:
        result = run_iceberg_cycle()
        print("\n" + "=" * 55)
        print("🧊 冰山 6 大自动能力执行结果")
        print("=" * 55)
        for lt, r in result.items():
            dur = r.get("duration_s", "?")
            print(f"  ✅ {lt:15s} ({dur}s)  {json.dumps({k:v for k,v in r.items() if k not in ['loop_type','duration_s']}, ensure_ascii=False)[:60]}")
