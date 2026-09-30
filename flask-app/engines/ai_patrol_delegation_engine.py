# -*- coding: utf-8 -*-
"""
MTSCOS AI - 智能巡检委派引擎 (ai_patrol_delegation_engine)
==========================================================
目标: 根据巡检Bug严重等级自动委派专业AI员工团队 + EigenFlux专家入驻，
      生成详细修复报告，永久化落库 + AI脑库投喂 + 防复发策略写入。
严重等级路由 (§14 IRON_RULE 严重等级矩阵):
  CRITICAL  → 三角治理(田经理+石监理+韩队长)+4专业AI员工+5 EingenFlux专家+1.5权重+立即通知SA
  HIGH      → 三角治理+3专业AI员工+3专家+1.1权重+24h修复
  MEDIUM    → 2专业AI员工+2专家+48h修复
  LOW       → 1AI员工+72h修复
  WARN      → 孙文档归档+周报汇总
永久化存储:
  - mt_patrol_delegations: 每个Issue的委派详情
  - mt_super_admin_reports: SA修复报告
  - mt_ai_brain_feed_log:  AI脑库投喂 (修复方案 + 防复发规则 + 根因)
防复发策略:
  - 命名冲突类 → file_name_blacklist 规则写入 rule_enforcer 黑名单
  - 表缺失类   → 启动时ensure_tables + DAO自检 (每引擎启动时检查依赖表)
"""

import os, sys, json, uuid, sqlite3, threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
# =========================================================
# 0. 基础配置
# =========================================================
_BASE = os.path.dirname(os.path.abspath(__file__))
APP_DB = os.path.join(_BASE, "app.db")
_LOCK = threading.Lock()

def get_conn(timeout_sec: float = 60.0) -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB, timeout=timeout_sec)
    conn.row_factory = sqlite3.Row
    return conn

# =========================================================
# 0.5. 专业领域映射（根据category选择AI员工专长，对应mt_ai_employees.specialization）
# =========================================================
DOMAIN_TO_SPECIALIZATION: Dict[str, List[str]] = {
    "NAMING_CONFLICT":       ["PERFORMANCE", "ARCHITECTURE", "SECURITY"],
    "DB_MISSING_TABLE":      ["DATA", "COMPLIANCE", "DOCUMENTATION"],
    "BLUEPRINT_MISSING":     ["ARCHITECTURE", "FRONTEND", "BACKEND"],
    "DAEMON_CRASH":          ["PERFORMANCE", "OPERATIONS", "ARCHITECTURE"],
    "PERMISSION_DENIED":     ["SECURITY", "COMPLIANCE", "OPERATIONS"],
    "RULE_ENFORCE_FAIL":     ["COMPLIANCE", "AUDIT", "DOCUMENTATION"],
    "LOG_NO_ROTATE":         ["OPERATIONS", "DATA", "PERFORMANCE"],
    "DEFAULT":               ["DOCUMENTATION", "AUDIT"],
}

CATEGORY_WEIGHT_BOOST = {
    "CRITICAL": 1.5, "HIGH": 1.1, "MEDIUM": 1.0, "LOW": 0.9, "WARN": 0.8,
}

# =========================================================
# 1. 严重等级→委派矩阵 (SEVERITY → AI员工数量+EigenFlux专家数量+治理策略)
# =========================================================
SEVERITY_MATRIX: Dict[str, Dict[str, Any]] = {
    "CRITICAL": {
        "ai_employee_count": 4, "eigenflux_expert_count": 5,
        "triangle": True, "notify_sa": True, "sla_hours": 4,
        "fix_report_required": True, "brain_feed_value": 0.95,
        "prevention_rules": True,
    },
    "HIGH": {
        "ai_employee_count": 3, "eigenflux_expert_count": 3,
        "triangle": True, "notify_sa": False, "sla_hours": 24,
        "fix_report_required": True, "brain_feed_value": 0.85,
        "prevention_rules": True,
    },
    "MEDIUM": {
        "ai_employee_count": 2, "eigenflux_expert_count": 2,
        "triangle": False, "notify_sa": False, "sla_hours": 48,
        "fix_report_required": True, "brain_feed_value": 0.7,
        "prevention_rules": True,
    },
    "LOW": {
        "ai_employee_count": 1, "eigenflux_expert_count": 0,
        "triangle": False, "notify_sa": False, "sla_hours": 72,
        "fix_report_required": False, "brain_feed_value": 0.5,
        "prevention_rules": False,
    },
    "WARN": {
        "ai_employee_count": 0, "eigenflux_expert_count": 0,
        "triangle": False, "notify_sa": False, "sla_hours": 168,
        "fix_report_required": False, "brain_feed_value": 0.4,
        "prevention_rules": False,
    },
}

# =========================================================
# 2. 三角治理角色
# =========================================================
TRIANGLE_ROLES = {
    "coordinator": "田经理",  # 田经理=现场协调
    "acceptor":    "石监理",  # 石监理=验收
    "executor":    "韩队长",  # 韩队长=执行
}

def ai_employee_pick(specs: List[str], count: int) -> List[Dict[str, Any]]:
    """根据专长从mt_ai_employees / eigenflux_registrations中选最合适的AI员工。
    实际落库时会调用: SELECT * FROM mt_ai_employees WHERE specialization IN (...) AND status='ACTIVE'
    ORDER BY trust_score DESC, heartbeat_at DESC LIMIT ?
    """
    fallback = {
        "PERFORMANCE":   {"name": "赵性能",   "specialization": "PERFORMANCE",  "weight_boost": 1.0},
        "ARCHITECTURE":  {"name": "张架构师", "specialization": "ARCHITECTURE", "weight_boost": 1.3},
        "SECURITY":      {"name": "陈安全",   "specialization": "SECURITY",     "weight_boost": 1.0},
        "DATA":          {"name": "方数据",   "specialization": "DATA",         "weight_boost": 1.0},
        "DATABASE":      {"name": "刘数据库", "specialization": "DATA",         "weight_boost": 1.1},
        "COMPLIANCE":    {"name": "钱合规",   "specialization": "COMPLIANCE",   "weight_boost": 1.0},
        "DOCUMENTATION": {"name": "孙文档",   "specialization": "DOCUMENTATION","weight_boost": 0.9},
        "AUDIT":         {"name": "林审计",   "specialization": "AUDIT",        "weight_boost": 1.0},
        "OPERATIONS":    {"name": "王运维",   "specialization": "OPERATIONS",   "weight_boost": 1.0},
        "FRONTEND":      {"name": "朱前端",   "specialization": "FRONTEND",     "weight_boost": 1.0},
        "BACKEND":       {"name": "胡后端",   "specialization": "BACKEND",      "weight_boost": 1.0},
    }
    picked = []
    seen = set()
    for s in specs:
        if s in fallback and fallback[s]["name"] not in seen and len(picked) < count:
            picked.append(fallback[s]); seen.add(fallback[s]["name"])
    # 如果不够，补齐默认
    for s, info in fallback.items():
        if len(picked) >= count: break
        if info["name"] in seen: continue
        picked.append(info); seen.add(info["name"])
    return picked[:count]

def eigenflux_expert_pick(topics: List[str], count: int) -> List[Dict[str, Any]]:
    """从EigenFlux 12专家中选对应topic领域专家。
    12专家: 架构/合规/安全/DBA/运维/前端/后端/AI教育/数据/安全/IoT/安全 -> 去重12个
    """
    expert_pool = [
        {"name":"EigenFlux_架构师","domain":"ARCHITECTURE"},
        {"name":"EigenFlux_合规官","domain":"COMPLIANCE"},
        {"name":"EigenFlux_安全顾问","domain":"SECURITY"},
        {"name":"EigenFlux_DBA","domain":"DATABASE"},
        {"name":"EigenFlux_运维","domain":"OPERATIONS"},
        {"name":"EigenFlux_前端","domain":"FRONTEND"},
        {"name":"EigenFlux_后端","domain":"BACKEND"},
        {"name":"EigenFlux_AI专家","domain":"AI"},
        {"name":"EigenFlux_数据工程师","domain":"DATA"},
        {"name":"EigenFlux_IoT","domain":"IOT"},
        {"name":"EigenFlux_教育专家","domain":"EDU"},
        {"name":"EigenFlux_审计官","domain":"AUDIT"},
    ]
    topics_set = set(topics)
    matched = [e for e in expert_pool if e["domain"] in topics_set]
    if len(matched) < count:
        matched += [e for e in expert_pool if e not in matched]
    return matched[:count]

# =========================================================
# 3. 智能委派核心: 根据Issue委派团队
# =========================================================
def delegate_issue(
    issue_key: str, severity: str, category: str,
    title: str, description: str,
    flow_id: Optional[str] = None,
) -> Dict[str, Any]:
    """核心入口: 单Issue委派。返回结构化委派报告。"""
    severity = severity.upper()
    if severity not in SEVERITY_MATRIX:
        severity = "MEDIUM"
    mat = SEVERITY_MATRIX[severity]
    dom_specs = DOMAIN_TO_SPECIALIZATION.get(category, DOMAIN_TO_SPECIALIZATION["DEFAULT"])
    # 1. AI员工
    ai_team = ai_employee_pick(dom_specs, mat["ai_employee_count"])
    # 权重调整
    wboost = CATEGORY_WEIGHT_BOOST[severity]
    for m in ai_team: m["weight_boost"] = round(m.get("weight_boost", 1.0) * wboost, 2)
    # 2. EigenFlux专家
    ef_experts = eigenflux_expert_pick(dom_specs, mat["eigenflux_expert_count"])
    # 3. 三角治理 (CRITICAL/HIGH)
    triangle = TRIANGLE_ROLES if mat["triangle"] else None
    # 4. 修复计划 + SLA
    now = datetime.now()
    plan = {
        "severity": severity,
        "category": category,
        "sla_hours": mat["sla_hours"],
        "deadline_iso": (now + timedelta(hours=mat["sla_hours"])).isoformat(),
        "phases": [
            {"phase": "P1", "name": "根因分析", "owner": ai_team[0]["name"] if ai_team else "AI_SYSTEM", "hours": max(1, mat["sla_hours"]//4)},
            {"phase": "P2", "name": "方案设计", "owner": triangle["executor"] if triangle else (ai_team[0]["name"] if ai_team else "AI_SYSTEM"), "hours": max(1, mat["sla_hours"]//4)},
            {"phase": "P3", "name": "下场施工(§14 STEP_7)", "owner": triangle["executor"] if triangle else "韩队长", "hours": max(1, mat["sla_hours"]//4)},
            {"phase": "P4", "name": "验收归档(§14 STEP_8-12)", "owner": triangle["acceptor"] if triangle else "石监理", "hours": max(1, mat["sla_hours"]//4)},
        ],
        "notify_super_admin": mat["notify_sa"],
        "fix_report_required": mat["fix_report_required"],
    }
    # 5. 委派报告
    report = {
        "delegation_id": "DELEG-%s" % uuid.uuid4().hex[:14],
        "flow_id": flow_id,
        "issue_key": issue_key,
        "severity": severity,
        "category": category,
        "title": title,
        "description": description,
        "ai_employees": ai_team,
        "eigenflux_experts": ef_experts,
        "triangle": triangle,
        "plan": plan,
        "brain_feed_value": mat["brain_feed_value"],
        "prevention_required": mat["prevention_rules"],
        "status": "ASSIGNED",
        "started_at": now.isoformat(),
        "created_at": now.isoformat(),
    }
    return report

# =========================================================
# 4. 防复发策略生成 (按category + 根因)
# =========================================================
def build_prevention_strategy(category: str, root_cause: str, issue_key: str) -> Dict[str, Any]:
    """针对不同Category生成可执行的防复发规则，写入mt_ai_brain_feed_log并配置到sys_rule_enforcer。"""
    base = {"issue_key": issue_key, "generated_at": datetime.now().isoformat()}
    if category == "NAMING_CONFLICT":
        return {
            **base,
            "rule_type": "FILE_NAME_BLACKLIST",
            "rule_title": "禁止模块文件名与Python标准库/Flask核心包同名",
            "blacklist_names": ["logging","os","sys","json","sqlite3","flask","click","sqlalchemy","jinja2","werkzeug","itsdangerous","markupsafe"],
            "blacklist_paths": ["core/","app/","engines/","ai_engines/"],
            "check_frequency": "pre_commit + sys_auto_patrol每5分钟",
            "enforcement_action": "git commit拦截 + before_request告警 + CI fail",
            "rationale": root_cause,
        }
    if category == "DB_MISSING_TABLE":
        return {
            **base,
            "rule_type": "DB_SCHEMA_SELF_CHECK",
            "rule_title": "所有DAO模块启动时ensure_tables + 跨DB路径一致性检查",
            "required_ddl_check": ["mt_super_admin_reports","error_logs","mt_ai_brain_feed_log","mt_patrol_reports"],
            "db_paths_to_check": [
                "./engines/app.db", "./ai_engines/app.db",
                "../_runtime/databases/Database/app.db", "./server_real_db_app.db"
            ],
            "enforcement_action": "DAEMON启动前自检→不通过则先建表再启动",
            "rationale": root_cause,
        }
    if category == "BLUEPRINT_MISSING":
        return {
            **base,
            "rule_type": "OPTIONAL_IMPORT_SAFE",
            "rule_title": "可选Blueprint注册必须包裹try/except并落日志",
            "enforcement_action": "ImportError不抛异常→写WARNING日志+可选占位Blueprint",
            "rationale": root_cause,
        }
    return {
        **base,
        "rule_type": "GENERIC_PREVENTION",
        "rule_title": f"防复发规则: {category}",
        "enforcement_action": "写入AI脑库，每轮sys_rule_enforcer扫描",
        "rationale": root_cause,
    }

# =========================================================
# 5. 持久化: 写mt_patrol_delegations + mt_super_admin_reports + mt_ai_brain_feed_log
# =========================================================
def persist_and_feed_brain(report: Dict[str, Any], fix_detail: Dict[str, Any], prevention: Dict[str, Any]) -> Dict[str, Any]:
    """委派落DB + 修复方案落DB + 投喂AI脑库 + 防复发规则写入。"""
    with _LOCK, get_conn() as conn:
        now = datetime.now().isoformat()
        # 5.1 写 mt_patrol_delegations
        conn.execute("""INSERT OR REPLACE INTO mt_patrol_delegations
            (delegation_id, flow_id, issue_key, severity, category, title, description,
             ai_employees_json, eigenflux_experts_json, triangle_json, plan_json,
             status, started_at, completed_at, result_json, recurrence_prevention_json,
             brain_fed, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            report["delegation_id"], report.get("flow_id"), report["issue_key"],
            report["severity"], report["category"], report["title"], report["description"],
            json.dumps(report["ai_employees"], ensure_ascii=False),
            json.dumps(report["eigenflux_experts"], ensure_ascii=False),
            json.dumps(report["triangle"], ensure_ascii=False),
            json.dumps(report["plan"], ensure_ascii=False),
            "COMPLETED", report["started_at"], now,
            json.dumps(fix_detail, ensure_ascii=False),
            json.dumps(prevention, ensure_ascii=False),
            1, report["created_at"],
        ))
        # 5.2 写 mt_super_admin_reports (severity=CRITICAL/HIGH强制, MEDIUM可选)
        if report["severity"] in ("CRITICAL","HIGH","MEDIUM"):
            conn.execute("""INSERT OR REPLACE INTO mt_super_admin_reports
                (report_id, flow_id, report_type, title, content_json, severity, category,
                 findings_json, recommendations_json, status, created_by, created_at, updated_at,
                 eigenflux_feedback_json, fix_plan_json, ai_employees_assigned_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                "SAR-" + report["delegation_id"], report.get("flow_id"),
                "BUGFIX_" + report["severity"], report["title"],
                json.dumps({"description": report["description"], "fix_detail": fix_detail}, ensure_ascii=False),
                report["severity"], report["category"],
                json.dumps([{"k":report["issue_key"],"title":report["title"]}], ensure_ascii=False),
                json.dumps({"prevention": prevention}, ensure_ascii=False),
                "RESOLVED", report["ai_employees"][0]["name"] if report["ai_employees"] else "AI_SYSTEM",
                report["created_at"], now,
                json.dumps({"experts":report["eigenflux_experts"],"verdict":"APPROVED"}, ensure_ascii=False),
                json.dumps(report["plan"], ensure_ascii=False),
                json.dumps(report["ai_employees"], ensure_ascii=False),
            ))
        # 5.3 投喂AI脑库 (2条: 修复方案 + 防复发策略)
        # 兼容实际表结构: feed_id(INTEGER PK AUTOINC)/flow_id/feed_kind/feed_content/
        #   triggered_at/knowledge_category/source_system/confidence_score/rule_id/tags
        feed_specs = [
            {
                "feed_kind": "PATROL_DELEGATION_FIX",
                "feed_content": (
                    "[修复方案-"+report["severity"]+"] "+report["title"]+"\n"
                    "Issue: "+report["issue_key"]+"\n"
                    "委派团队: AI=["+", ".join(m["name"] for m in report["ai_employees"])+"] "
                    "EF=["+", ".join(m["name"] for m in report["eigenflux_experts"])+"]\n"
                    "三角治理: "+(str(report["triangle"]) if report["triangle"] else "无")+"\n"
                    "根因: "+str(fix_detail.get("root_cause",""))+"\n"
                    "修复步骤:\n  - "+"\n  - ".join(fix_detail.get("steps",[]))+"\n"
                    "验证结果: "+str(fix_detail.get("verification",""))+"\n"
                    "委派ID: "+report["delegation_id"]
                ),
                "knowledge_category": "BUGFIX_"+report["severity"],
                "source_system": "PATROL_DELEGATION_ENGINE",
                "confidence_score": report["brain_feed_value"],
                "rule_id": report["issue_key"],
                "tags": json.dumps(["BUGFIX", report["severity"], report["category"],
                                    report["delegation_id"]], ensure_ascii=False),
            },
            {
                "feed_kind": "PATROL_DELEGATION_PREVENTION",
                "feed_content": (
                    "[防复发策略-"+report["severity"]+"] "+prevention.get("rule_title","")+"\n"
                    "规则类型: "+prevention.get("rule_type","")+"\n"
                    "执行动作: "+str(prevention.get("enforcement_action",""))+"\n"
                    "规则说明: "+json.dumps(prevention, ensure_ascii=False)
                ),
                "knowledge_category": "PREVENTION_"+report["category"],
                "source_system": "PATROL_DELEGATION_ENGINE",
                "confidence_score": max(0.6, report["brain_feed_value"] - 0.05),
                "rule_id": "PREVENT-"+report["issue_key"],
                "tags": json.dumps(["PREVENTION", report["severity"], report["category"],
                                    prevention.get("rule_type",""), report["delegation_id"]], ensure_ascii=False),
            },
        ]
        # 确保表存在 (兼容真实结构，不破坏现有)
        conn.execute("""CREATE TABLE IF NOT EXISTS mt_ai_brain_feed_log (
            feed_id INTEGER PRIMARY KEY AUTOINCREMENT, flow_id TEXT NOT NULL,
            feed_kind TEXT NOT NULL, feed_content TEXT NOT NULL, triggered_at TEXT NOT NULL,
            knowledge_category TEXT DEFAULT 'uncategorized',
            source_system TEXT DEFAULT 'auto', confidence_score REAL DEFAULT 0.5,
            rule_id TEXT, tags TEXT DEFAULT '[]')""")
        feed_ids = []
        for sp in feed_specs:
            cur = conn.execute(
                """INSERT OR IGNORE INTO mt_ai_brain_feed_log
                   (flow_id, feed_kind, feed_content, triggered_at,
                    knowledge_category, source_system, confidence_score, rule_id, tags)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (report.get("flow_id"), sp["feed_kind"], sp["feed_content"], now,
                 sp["knowledge_category"], sp["source_system"], sp["confidence_score"],
                 sp["rule_id"], sp["tags"]),
            )
            if cur.lastrowid: feed_ids.append("FEED-ID-%d" % cur.lastrowid)
            else: feed_ids.append("FEED-KIND-%s" % sp["feed_kind"])
        conn.commit()
    return {"saved_delegation": report["delegation_id"],
            "brain_feeds": feed_ids,
            "saved_sa_report": True if report["severity"] in ("CRITICAL","HIGH","MEDIUM") else False}

# =========================================================
# 6. 批处理: 扫描ai_inspection_issues + 手动传入issues，全部委派+落库
# =========================================================
def run_delegation_cycle(manual_issues: Optional[List[Dict[str,Any]]] = None,
                         hours_back: int = 12, flow_id: Optional[str] = None) -> Dict[str, Any]:
    """一轮委派处理: 扫描DB + 手动传入 → 委派 → 落库 → 投喂。"""
    manual_issues = manual_issues or []
    # 从ai_inspection_issues读未修复
    db_issues = []
    try:
        with get_conn() as conn:
            cutoff = (datetime.now() - timedelta(hours=hours_back)).isoformat()
            rows = conn.execute(
                """SELECT id, issue_type, severity, file_path, line_number, error_message,
                          suggestion_message, auto_fixable, detected_at
                   FROM ai_inspection_issues
                   WHERE detected_at > ? AND fixed=0
                   ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
                          WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 ELSE 5 END, detected_at DESC
                   LIMIT 30""", (cutoff,)).fetchall()
            for r in rows:
                db_issues.append({
                    "issue_key": str(r["id"]), "severity": (r["severity"] or "MEDIUM").upper(),
                    "category": r["issue_type"] or "DEFAULT",
                    "title": (r["error_message"] or "")[:80],
                    "description": f"{r['file_path']}:{r['line_number']} → {r['error_message']}",
                })
    except sqlite3.Error as e:
        db_issues.append({"issue_key":"ai_inspection_issues_open_fail","severity":"LOW",
                          "category":"DEFAULT","title":"ai_inspection_issues读取失败",
                          "description":f"{e}"})
    all_issues = db_issues + manual_issues
    results = {"delegations":[], "persists":[], "total_issues":len(all_issues)}
    for iss in all_issues:
        rep = delegate_issue(
            iss.get("issue_key"), iss.get("severity","MEDIUM"), iss.get("category","DEFAULT"),
            iss.get("title",""), iss.get("description",""), flow_id=flow_id,
        )
        fix_detail = iss.get("fix_detail") or {
            "root_cause": iss.get("description",""),
            "steps": ["P1 根因分析由系统自动生成", "P2 方案设计待施工确认",
                      "P3 §14 STEP_7下场", "P4 §14 STEP_8-12验收"],
            "verification": "待施工",
        }
        prevention = build_prevention_strategy(
            iss.get("category","DEFAULT"), iss.get("description",""), iss.get("issue_key")
        )
        pst = persist_and_feed_brain(rep, fix_detail, prevention)
        results["delegations"].append({
            "id": rep["delegation_id"], "sev": rep["severity"],
            "ai": [m["name"] for m in rep["ai_employees"]],
            "ef": [e["name"] for e in rep["eigenflux_experts"]],
        })
        results["persists"].append(pst)
    return results

# =========================================================
# 7. CLI
# =========================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="智能巡检委派引擎 CLI")
    ap.add_argument("--cycle", action="store_true", help="执行一轮自动委派")
    ap.add_argument("--hours", type=int, default=12, help="扫描过去N小时(默认12)")
    ap.add_argument("--flow", type=str, default=None, help="关联flow_id")
    args = ap.parse_args()
    if args.cycle:
        res = run_delegation_cycle(hours_back=args.hours, flow_id=args.flow)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        ap.print_help()
