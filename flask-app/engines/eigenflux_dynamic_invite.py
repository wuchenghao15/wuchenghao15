#!/usr/bin/env python3
"""
仙女座动态专家匹配 — eigenflux_dynamic_invite.py
================================================

核心思想: 每次研发/运维/规则审查活动, 根据内容关键词 + 任务类型, 
自动匹配最对口的 AI 员工 / EigenFlux 专家 入场。

三大数据源:
 ① mt_ai_employees          → 10827 AI 员工 (职能关键词匹配)
 ② mt_eigenflux_registrations → EigenFlux 注册专家 (专长标签)
 ③ 本地 Q5 模型              → 语义级匹配 (关键词不够精确时)

两种匹配模式:
  - 关键词快匹配 (毫秒级, 用正则 + 专长词库)
  - Q5 语义匹配 (10-20s, 活动描述 → 输出匹配的专家名单)

输出:
  {
    "activity_type": "开发提案|规则审查|运维巡检|代码review|架构讨论",
    "matched_employees": [{"name": "...", "role": "...", "match_score": 92, "why": "..."}],
    "matched_experts":   [{"name": "...", "expert_id": "...", "match_score": 88, "why": "..."}],
    "recommended_team":  ["专家A", "员工B", "员工C"],
    "total_matched": 5
  }
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

# ── 路径 ──
BASE = Path(__file__).resolve().parent.parent  # flask-app/
DB   = BASE / "database" / "app.db"

# Ollama
OLLAMA_URL = "http://localhost:11435/api/chat"
MODEL = "qwen2.5:14b-q5"

# ── 专长词库 (关键词 → 专家/角色类型) ──
KEYWORD_EXPERT_MAP = {
    # 安全类
    "security_expert": ["安全", "注入", "XSS", "CSRF", "密码", "加密", "脱敏", "漏洞", "风险", "攻击", "防护"],
    # 架构
    "arch_designer": ["架构", "重构", "模块", "依赖", "解耦", "设计模式", "组件", "service", "controller", "分层"],
    # 性能
    "performance_opt": ["性能", "优化", "缓存", "数据库", "SQL", "查询", "索引", "异步", "队列", "并发", "N+1"],
    # 合规
    "compliance_officer": ["合规", "规则", "治理", "权限", "认证", "授权", "流程", "审计", "铁律", "强制"],
    # 法务
    "legal_consultant": ["法律", "合规", "隐私", "数据保护", "GDPR", "个人信息", "PIPL", "授权", "跨境"],
    # UX
    "ux_designer": ["界面", "UX", "用户", "交互", "前端", "Element", "响应式", "美观", "易用"],
    # 后端
    "backend_engineer": ["路由", "API", "Flask", "SQLite", "ORM", "schema", "表", "迁移", "CRUD", "REST"],
    # 运维
    "ops_engineer": ["daemon", "进程", "监控", "重启", "心跳", "部署", "端口", "负载", "保活", "巡检"],
    # AI/NLP
    "ai_engineer": ["AI", "模型", "LLM", "RAG", "向量", "embedding", "推理", "微调", "token", "Ollama", "EigenFlux"],
    # 规则
    "rule_engineer": ["规则", "rule", "IRON_RULE", "12步骤", "dev_gate", "pre-commit", "hook", "拦截", "强制执行"],
}

ACTIVITY_ROUTING = {
    # 活动类型 → 默认必拉的专家
    "开发提案":  ["compliance_officer", "arch_designer", "legal_consultant"],
    "规则审查":  ["rule_engineer", "compliance_officer", "legal_consultant"],
    "运维巡检":  ["ops_engineer", "performance_opt"],
    "代码review": ["backend_engineer", "security_expert", "rule_engineer"],
    "架构讨论":  ["arch_designer", "performance_opt", "ai_engineer"],
    "安全加固":  ["security_expert", "legal_consultant", "compliance_officer"],
    "数据模型":  ["backend_engineer", "performance_opt", "compliance_officer"],
}


# ═════════════════════════════════════════════════════════════════════════
# 核心匹配
# ═════════════════════════════════════════════════════════════════════════

def match_experts(
    activity_description: str,
    activity_type: str = "开发提案",
    use_llm: bool = True,
    max_experts: int = 6,
    max_employees: int = 4,
) -> dict:
    """
    根据活动描述匹配最对口的专家 + AI 员工。
    
    匹配优先级:
    1. 默认路由的专家 (ACTIVITY_ROUTING[activity_type])
    2. 关键词命中的专家 (KEYWORD_EXPERT_MAP)
    3. 数据库里真实注册的 EigenFlux 专家 (mt_eigenflux_registrations)
    4. 数据库里真实的 AI 员工 (mt_ai_employees)
    5. Q5 语义兜底
    """
    t0 = time.time()
    
    result = {
        "activity_type": activity_type,
        "activity_description": activity_description[:200],
        "matched_experts": [],
        "matched_employees": [],
        "recommended_team": [],
        "match_method": "keyword",
    }
    
    # ── Step 1: 关键词匹配专家类型 ──
    keyword_scores = {}
    for expert_type, keywords in KEYWORD_EXPERT_MAP.items():
        hit = 0
        desc_lower = activity_description.lower()
        for kw in keywords:
            if kw.lower() in desc_lower:
                hit += 1
        if hit > 0:
            keyword_scores[expert_type] = hit
    
    # 加上活动类型默认路由 (权重 +3)
    default_routes = ACTIVITY_ROUTING.get(activity_type, [])
    for r in default_routes:
        keyword_scores[r] = keyword_scores.get(r, 0) + 3
    
    sorted_types = sorted(keyword_scores.items(), key=lambda x: -x[1])
    
    # ── Step 2: 从数据库找真实的 EigenFlux 专家 ──
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    
    # EigenFlux 专家 (最多 12 人)
    eigen_members = []
    try:
        for row in db.execute("SELECT * FROM mt_eigenflux_registrations WHERE is_member=1 LIMIT 12"):
            eigen_members.append(dict(row))
    except Exception as e:
        pass
    
    # AI 员工 (按职能关键词匹配)
    ai_employees = []
    try:
        for row in db.execute(
            "SELECT employee_id, name, role, department, skills, responsibilities FROM mt_ai_employees LIMIT 200"
        ):
            emp = dict(row)
            emp["_match_score"] = 0
            emp["_why"] = []
            
            text = f"{emp.get('role','')} {emp.get('department','')} {emp.get('skills','')} {emp.get('responsibilities','')}"
            for expert_type, score in sorted_types[:5]:
                keywords = KEYWORD_EXPERT_MAP[expert_type]
                for kw in keywords:
                    if kw.lower() in text.lower():
                        emp["_match_score"] += score
                        emp["_why"].append(f"擅长{expert_type.replace('_','/')}")
                        break
            
            if emp["_match_score"] > 0:
                ai_employees.append(emp)
    except Exception as e:
        pass
    
    db.close()
    
    # ── Step 3: 组装结果 ──
    
    # EigenFlux 专家 (用内置的专家池)
    EIGENFLUX_POOL = {
        "security_expert":    {"name": "安全审计专家",   "expert_id": "sec_audit"},
        "arch_designer":      {"name": "架构设计专家",   "expert_id": "arch_design"},
        "performance_opt":    {"name": "性能优化专家",   "expert_id": "perf_opt"},
        "compliance_officer": {"name": "合规审查专家",   "expert_id": "compliance"},
        "legal_consultant":   {"name": "法务王律师",     "expert_id": "legal_wang"},
        "ux_designer":        {"name": "用户体验专家",   "expert_id": "ux"},
        "backend_engineer":   {"name": "后端工程专家",   "expert_id": "backend"},
        "ops_engineer":       {"name": "运维工程专家",   "expert_id": "ops"},
        "ai_engineer":        {"name": "AI算法专家",     "expert_id": "ai_algo"},
        "rule_engineer":      {"name": "规则治理专家",   "expert_id": "rule_governance"},
    }
    
    for expert_type, score in sorted_types[:max_experts]:
        if expert_type in EIGENFLUX_POOL:
            pool_data = EIGENFLUX_POOL[expert_type].copy()
            pool_data["match_score"] = min(score * 15, 100)
            pool_data["why"] = f"命中 {score} 个领域关键词"
            result["matched_experts"].append(pool_data)
    
    # AI 员工 (取前 max_employees)
    ai_employees.sort(key=lambda x: -x.get("_match_score", 0))
    for emp in ai_employees[:max_employees]:
        result["matched_employees"].append({
            "name": emp.get("name", f"员工#{emp.get('employee_id','?')}"),
            "employee_id": emp.get("employee_id"),
            "role": emp.get("role", "AI员工"),
            "department": emp.get("department", ""),
            "match_score": min(emp["_match_score"] * 10, 100),
            "why": "; ".join(emp["_why"][:3]) if emp["_why"] else "通用AI员工",
        })
    
    # ── Step 4: Q5 语义增强 (如果关键词匹配太少) ──
    if use_llm and len(result["matched_experts"]) < 3:
        llm_result = _llm_enhance(activity_description, sorted_types)
        if llm_result:
            for expert in llm_result:
                if expert.get("expert_id") not in [e["expert_id"] for e in result["matched_experts"]]:
                    result["matched_experts"].append(expert)
                    result["match_method"] = "keyword+llm"
    
    # 推荐团队 = 专家 top3 + AI 员工 top2
    result["recommended_team"] = [e["name"] for e in result["matched_experts"][:3]] + \
                                  [e["name"] for e in result["matched_employees"][:2]]
    result["total_matched"] = len(result["matched_experts"]) + len(result["matched_employees"])
    result["elapsed_s"] = round(time.time() - t0, 2)
    
    return result


def _llm_enhance(desc: str, current_types: list) -> Optional[list]:
    """Q5 语义匹配补充专家"""
    sys_prompt = """你是仙女座 AI 的人力资源总监。根据开发活动描述, 选出 3-5 个最应该参与讨论的专家类型。

可选专家类型: security_expert, arch_designer, performance_opt, compliance_officer, legal_consultant, ux_designer, backend_engineer, ops_engineer, ai_engineer, rule_engineer

输出 JSON 数组, 每项 {expert_type, confidence_score(0-100)}"""
    
    try:
        import urllib.request
        payload = json.dumps({"model": MODEL, "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": desc[:500]}
        ], "stream": False}).encode()
        r = urllib.request.urlopen(urllib.request.Request(
            OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"}), timeout=25)
        content = json.loads(r.read())["message"]["content"]
        
        # 解析
        import re as _re
        m = _re.search(r'\[.*?\]', content, _re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            EIGENFLUX_POOL = {
                "security_expert": {"name": "安全审计专家", "expert_id": "sec_audit"},
                "arch_designer": {"name": "架构设计专家", "expert_id": "arch_design"},
                "performance_opt": {"name": "性能优化专家", "expert_id": "perf_opt"},
                "compliance_officer": {"name": "合规审查专家", "expert_id": "compliance"},
                "legal_consultant": {"name": "法务王律师", "expert_id": "legal_wang"},
                "ux_designer": {"name": "用户体验专家", "expert_id": "ux"},
                "backend_engineer": {"name": "后端工程专家", "expert_id": "backend"},
                "ops_engineer": {"name": "运维工程专家", "expert_id": "ops"},
                "ai_engineer": {"name": "AI算法专家", "expert_id": "ai_algo"},
                "rule_engineer": {"name": "规则治理专家", "expert_id": "rule_governance"},
            }
            enhanced = []
            for item in data[:5]:
                etype = item.get("expert_type", "")
                if etype in EIGENFLUX_POOL:
                    info = EIGENFLUX_POOL[etype].copy()
                    info["match_score"] = item.get("confidence_score", 60)
                    info["why"] = f"Q5 语义推荐"
                    enhanced.append(info)
            return enhanced
    except Exception:
        pass
    return None


def build_invitation(result: dict) -> dict:
    """把 match_experts 结果 → 可直接发给专家的邀请消息"""
    invitations = []
    
    team_str = ", ".join(result["recommended_team"])
    desc = result["activity_description"]
    
    for expert in result["matched_experts"]:
        invitations.append({
            "to": expert["name"],
            "expert_id": expert["expert_id"],
            "channel": "EigenFlux",
            "message": (
                f"📢 仙女座邀请你参与【{result['activity_type']}】\n"
                f"📝 议题: {desc[:100]}\n"
                f"👥 团队: {team_str}\n"
                f"🎯 匹配度: {expert['match_score']}% ({expert['why']})\n"
                f"⏰ 方式: Q5 自动拉你进群 / 直接投 EigenFlux 投票"
            ),
            "action": "EIGENFLUX_VOTE",
            "payload": {"activity_type": result["activity_type"], "expert_id": expert["expert_id"]}
        })
    
    for emp in result["matched_employees"]:
        invitations.append({
            "to": emp["name"],
            "employee_id": emp.get("employee_id"),
            "channel": "AI员工心跳",
            "message": (
                f"📢 仙女座给你派单【{result['activity_type']}】\n"
                f"📝 任务: {desc[:100]}\n"
                f"👥 搭档: {team_str}\n"
                f"🎯 匹配度: {emp['match_score']}% ({emp['why']})"
            ),
            "action": "ASSIGN_TASK",
            "payload": {"activity_type": result["activity_type"], "employee_id": emp.get("employee_id")}
        })
    
    result["invitations"] = invitations
    return result


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 eigenflux_dynamic_invite.py match <活动类型> <活动描述>")
        print("  python3 eigenflux_dynamic_invite.py demo")
        print("")
        print("活动类型: 开发提案 | 规则审查 | 运维巡检 | 代码review | 架构讨论 | 安全加固 | 数据模型")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "demo":
        # 3 个典型 demo
        demos = [
            ("开发提案", "新增 SQL 查询缓存, 减少 N+1, 优化数据库性能"),
            ("规则审查", "弱约束词 'may' 'should' 自动强化, 规则一致性校验"),
            ("运维巡检", "daemon 心跳超时自动重启, 端口漂移检测, 进程保活"),
        ]
        for atype, desc in demos:
            print(f"\n{'═'*60}")
            print(f"🎯 [{atype}] {desc}")
            print(f"{'═'*60}")
            result = match_experts(desc, activity_type=atype, use_llm=True)
            team = result["recommended_team"]
            print(f"  👥 推荐团队 ({len(team)}人): {', '.join(team)}")
            print(f"  👁️  EigenFlux 专家 ({len(result['matched_experts'])}人):")
            for e in result["matched_experts"]:
                print(f"     {e['name']:14s} score={e['match_score']:>3}%  {e['why'][:40]}")
            if result["matched_employees"]:
                print(f"  🤖 AI 员工 ({len(result['matched_employees'])}人):")
                for emp in result["matched_employees"]:
                    print(f"     {emp['name']} ({emp['role']}) score={emp['match_score']:>3}%  {emp['why'][:40]}")
            print(f"  ⏱️  匹配耗时: {result['elapsed_s']}s  method={result['match_method']}")
    
    elif cmd == "match":
        atype = sys.argv[2] if len(sys.argv) > 2 else "开发提案"
        desc = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        result = match_experts(desc, activity_type=atype)
        result = build_invitation(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
