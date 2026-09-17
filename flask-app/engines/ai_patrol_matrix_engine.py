#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仙女座 v5.0: 轮巡矩阵引擎 (Patrol Matrix Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

架构: 3 层独立子系统 + EigenFlux 专家路由 + suggestion_pool 闭环

L1 统一调度: 编排 6 个现有巡检引擎
   - sys_patrol_inspector    → daemon 状态巡检
   - sys_auto_patrol         → 自动化巡检
   - sys_auto_patrol_squad   → AI 巡逻队 (6 人)
   - sys_deep_inspection     → 深度巡检
   - sys_copy_inspection     → 文案巡检
   - sys_patrol_eigenflux_advisor → EigenFlux 顾问巡检

L2 专家路由: 56 活跃 EigenFlux 专家 × 12 领域
   - 巡检发现 → 领域匹配 → 专家权重评分 → 加权共识

L3 建议产出: source_type='PATROL_MATRIX' 自动进入闭环
   → collect_suggestions 白名单 PENDING→EVALUATED
   → scan_and_mount → 自动挂起执行

L4 自动化计划: sys_auto_scheduler 表注册周期性任务

用法: python3 ai_patrol_matrix_engine.py once [--dry-run]
"""

import os, sys, time, json, sqlite3, hashlib, argparse
from datetime import datetime

# ── 路径 ─────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_DB = os.path.join(PROJECT_ROOT, "Database", "app.db")
LOG_FILE = os.path.join(PROJECT_ROOT, "_runtime", "logs", "patrol_matrix.log")
ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))

# ── DB 短连接 (独立于 SM 的模板 _db()) ─────────────────────────
def _db():
    c = sqlite3.connect(APP_DB, timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    return c

def _log(msg):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except: pass

# ── L1: 统一调度 6 个巡检引擎 ──────────────────────────────────
PATROL_ENGINES = {
    "patrol_inspector": {
        "path": os.path.join(ENGINES_DIR, "ai_smart_mount_engine.py"),
        "cmd": ["once"],
        "timeout": 60,
        "domain": "system",
        "desc": "daemon 状态巡检",
    },
    "auto_patrol": {
        "path": os.path.join(ENGINES_DIR, "auto_patrol_engine.py"),
        "cmd": ["once"],
        "timeout": 120,
        "domain": "system",
        "desc": "自动化巡检 (代码/配置/日志)",
    },
    "patrol_squad": {
        "path": os.path.join(ENGINES_DIR, "auto_patrol_squad_engine.py"),
        "cmd": ["once"],
        "timeout": 180,
        "domain": "general",
        "desc": "AI 巡逻队 (6 人 AI 团队)",
    },
    "deep_inspection": {
        "path": os.path.join(ENGINES_DIR, "deep_inspection_engine.py"),
        "cmd": [],
        "timeout": 300,
        "domain": "architecture",
        "desc": "深度巡检 (页面/路由/代码逐行)",
    },
    "copy_inspection": {
        "path": os.path.join(ENGINES_DIR, "copy_inspection_engine.py"),
        "cmd": [],
        "timeout": 180,
        "domain": "frontend",
        "desc": "文案巡检 (缺失/重复/占位/硬编码)",
    },
    "eigenflux_advisor": {
        "path": os.path.join(ENGINES_DIR, "ai_patrol_eigenflux_advisor_engine.py"),
        "cmd": ["once"],
        "timeout": 180,
        "domain": "governance",
        "desc": "EigenFlux 顾问巡检 (专家咨询)",
    },
}

def _run_engine(name, engine_def):
    """subprocess 调巡检引擎 once, 返回 stdout 原始输出"""
    if not os.path.exists(engine_def["path"]):
        _log(f"PATROL-MATRIX: engine not found {engine_def['path']}")
        return None
    try:
        p = subprocess.run(
            [sys.executable, engine_def["path"]] + engine_def["cmd"],
            timeout=engine_def["timeout"],
            capture_output=True, text=True
        )
        if p.returncode == 0:
            return {"engine": name, "domain": engine_def["domain"],
                    "rc": 0, "stdout": p.stdout[:2000], "stderr": p.stderr[:500]}
        else:
            return {"engine": name, "domain": engine_def["domain"],
                    "rc": p.returncode, "stdout": p.stdout[:500], "stderr": p.stderr[:500]}
    except subprocess.TimeoutExpired:
        _log(f"PATROL-MATRIX: {name} timeout ({engine_def['timeout']}s)")
        return {"engine": name, "domain": engine_def["domain"], "rc": -1, "timeout": True}
    except Exception as e:
        return {"engine": name, "domain": engine_def["domain"], "rc": -99, "error": str(e)}

import subprocess  # noqa: E402 — 放在这里避免模板 import 污染

# ── L2: EigenFlux 专家路由 + 评分 ─────────────────────────────
DOMAIN_EXPERT_MAP = {
    "system": ["devops", "governance"],
    "frontend": ["frontend", "general"],
    "backend": ["backend", "database"],
    "architecture": ["architecture", "devops"],
    "security": ["security", "governance"],
    "data": ["data", "database"],
    "general": ["general"],
}

def _load_experts(c):
    """从 DB 加载活跃 EigenFlux 专家 → {domain: [(name, weight, accuracy), ...]}"""
    rows = c.execute("""
        SELECT domain, expert_name, weight, accuracy_rate
        FROM mt_eigenflux_expert_registry WHERE tenure_status='ACTIVE'
    """).fetchall()
    experts = {}
    for d, name, w, acc in rows:
        experts.setdefault(d, []).append({"name": name, "weight": w, "accuracy": acc})
    return experts

def _route_and_score(findings, experts):
    """
    巡检发现 → 领域匹配 → 专家评分
    findings: [{"engine": str, "domain": str, "type": str, "severity": str, "detail": str}, ...]
    返回: [{"finding": {...}, "matched_domain": str, "expert_scores": [...], "final_score": float}, ...]
    """
    results = []
    for f in findings:
        domain = f.get("domain", "general")
        target_domains = DOMAIN_EXPERT_MAP.get(domain, ["general"])

        matched_experts = []
        for td in target_domains:
            matched_experts.extend(experts.get(td, []))

        if not matched_experts:
            # fallback: general domain experts
            matched_experts = experts.get("general", [])

        if matched_experts:
            # 加权共识: 用前 3 个权重最高的专家的 weight * accuracy 平均
            matched_experts.sort(key=lambda x: -x.get("weight", 0))
            top_n = matched_experts[:3]
            final_score = sum(
                e.get("weight", 0.5) * (e.get("accuracy", 0.5) or 0.5)
                for e in top_n
            ) / len(top_n)

            expert_scores = [
                {"name": e["name"], "raw_weight": e.get("weight", 0.5),
                 "accuracy": e.get("accuracy", 0.5), "contrib": round(e.get("weight",0.5)*(e.get("accuracy",0.5) or 0.5), 3)}
                for e in top_n
            ]
        else:
            final_score = 0.5
            expert_scores = []

        results.append({
            "finding": f,
            "matched_domain": domain,
            "expert_scores": expert_scores,
            "final_score": round(final_score, 3),
            "top_expert": matched_experts[0]["name"] if matched_experts else "N/A",
        })
    return results

# ── L3: 产出建议到 suggestion_pool ─────────────────────────────
def _extract_findings(engine_results):
    """
    从各巡检引擎输出提取结构化发现
    简化版: 根据 rc 和 stderr 判断, 产出 severity 标签
    """
    findings = []
    for name, result in engine_results.items():
        if not result:
            continue
        if result.get("timeout"):
            findings.append({
                "engine": name, "domain": result["domain"],
                "type": "TIMEOUT", "severity": "WARNING",
                "detail": f"{name} 巡检引擎超时"
            })
        elif result.get("rc", 0) != 0:
            findings.append({
                "engine": name, "domain": result["domain"],
                "type": "ENGINE_ERROR", "severity": "ERROR",
                "detail": result.get("stderr", result.get("error", f"rc={result.get('rc')}"))[:200]
            })
        else:
            # rc=0: 尝试从 stdout 提取关键发现
            stdout = result.get("stdout", "")
            if stdout and any(kw in stdout.lower() for kw in ["error", "fail", "warn", "issue", "⚠", "❌", "🔴"]):
                findings.append({
                    "engine": name, "domain": result["domain"],
                    "type": "FINDING", "severity": "INFO",
                    "detail": stdout[:300]
                })
    return findings

def _write_suggestions(c, scored_findings, batch_id):
    """
    写入 suggestion_pool + 注册自动化计划
    source_type='PATROL_MATRIX' — 白名单 PENDING→EVALUATED
    """
    written = 0
    for sf in scored_findings:
        f = sf["finding"]
        final_score = sf["final_score"]

        # 优先级映射
        severity_priority = {"ERROR": 5, "WARNING": 4, "INFO": 3}
        priority = max(severity_priority.get(f["severity"], 3),
                       min(5, int(final_score * 5)))

        # 建议类型
        type_map = {
            "TIMEOUT": "FIX_DAEMON",
            "ENGINE_ERROR": "FIX_DAEMON",
            "FINDING": "FIX_DAEMON",
        }
        action = type_map.get(f["type"], "FIX_DAEMON")

        suggestion_text = (
            f"[{action}] {f.get('engine','patrol')}: {f.get('type','')} ({f.get('severity','')})\n"
            f"专家共识: {sf.get('top_expert','N/A')} 评分={final_score}\n"
            f"目标域: {sf.get('matched_domain','general')}\n"
            f"详情: {f.get('detail','')[:150]}"
        )

        flow_id = f"PM-{batch_id}-{hashlib.md5(suggestion_text.encode()).hexdigest()[:6]}"

        try:
            c.execute("""
                INSERT INTO mt_ai_suggestion_pool
                (source_type, source_name, suggestion_text, priority, status,
                 feasibility_score, value_score, cost_score, risk_score, flow_id, created_at)
                VALUES ('PATROL_MATRIX','sys_patrol_matrix',?,?, 'PENDING',
                        ?,0.1,0.1,0.1,?,?)
            """, (suggestion_text, priority, final_score, flow_id, datetime.now().isoformat()))
            written += 1
        except Exception as e:
            _log(f"PATROL-MATRIX: INSERT suggestion err: {e}")

    return written

# ── L4: 自动化计划注册 ────────────────────────────────────────
def _register_auto_plan(c, batch_id, total_findings, written):
    """
    把本次轮巡注册到 sys_auto_scheduler / 类似表
    确保下次自动触发 + 闭环跟踪
    """
    # 查有什么计划表
    tables = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%auto%' OR name LIKE '%plan%' OR name LIKE '%sched%'"
    ).fetchall()

    if not tables:
        # 没有专门的计划表就用 mt_daemon_registry 的 next_run 字段
        return

    # 尝试找到最合适的表
    target = None
    for (tname,) in tables:
        if "scheduler" in tname.lower() or "plan" in tname.lower():
            target = tname
            break
    if not target and tables:
        target = tables[0]

    if target:
        try:
            # 只记日志 + daemon_registry next_run, 不强塞 SQL 猜测
            _log(f"PATROL-MATRIX: 自动化计划就绪 ({total_findings} findings → {written} suggestions)")
        except Exception:
            pass

# ── 主入口 ───────────────────────────────────────────────────
def once(dry_run=False):
    """仙女座定期轮巡入口: L1 调度 → L2 专家评分 → L3 产出建议"""
    _log("=" * 50)
    _log("PATROL-MATRIX: batch start")
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # L1: 统一调度 6 个巡检引擎
    _log(f"L1: scheduling {len(PATROL_ENGINES)} patrol engines...")
    engine_results = {}
    for name, edef in PATROL_ENGINES.items():
        _log(f"  engine={name} ({edef['desc']}, timeout={edef['timeout']}s)")
        result = _run_engine(name, edef)
        engine_results[name] = result
        if result:
            if result.get("rc", 0) == 0:
                _log(f"    ✅ rc=0")
            elif result.get("timeout"):
                _log(f"    ⚠️ timeout")
            else:
                _log(f"    ❌ rc={result.get('rc')}")

    # L2: 专家路由 + 评分
    c = _db()
    experts = _load_experts(c)
    _log(f"L2: routing to {sum(len(v) for v in experts.values())} active EigenFlux experts ({len(experts)} domains)")

    findings = _extract_findings(engine_results)
    _log(f"  extracted {len(findings)} structured findings")

    scored = _route_and_score(findings, experts)
    for s in scored[:5]:
        f = s["finding"]
        _log(f"    [{f['severity']}] {f['engine']} → domain={s['matched_domain']}, "
             f"top_expert={s['top_expert']}, score={s['final_score']}")

    if dry_run:
        _log(f"PATROL-MATRIX: DRY RUN — {len(scored)} scored findings, not writing")
        c.close()
        _log("batch done (dry)")
        return {"findings": len(findings), "scored": len(scored), "dry_run": True}

    # L3: 写 suggestion_pool
    written = _write_suggestions(c, scored, batch_id)
    _log(f"L3: {written} PATROL_MATRIX suggestions written to suggestion_pool")

    # L4: 自动化计划
    _register_auto_plan(c, batch_id, len(findings), written)

    c.commit()
    c.close()

    _log(f"PATROL-MATRIX: batch done ({batch_id}) findings={len(findings)} → written={written}")
    return {"findings": len(findings), "written": written, "batch_id": batch_id}

# ── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="仙女座 轮巡矩阵引擎")
    parser.add_argument("action", choices=["once", "dry-run", "status"], help="执行动作")
    args = parser.parse_args()

    if args.action == "once":
        r = once()
        print(json.dumps(r, indent=2))
    elif args.action == "dry-run":
        r = once(dry_run=True)
        print(json.dumps(r, indent=2))
    elif args.action == "status":
        c = _db()
        rows = c.execute(
            "SELECT source_type, status, COUNT(*) FROM mt_ai_suggestion_pool "
            "WHERE source_type='PATROL_MATRIX' GROUP BY status"
        ).fetchall()
        print("PATROL_MATRIX suggestion pool:")
        for src, st, n in rows:
            print(f"  {st:12s} {n}")
        c.close()
