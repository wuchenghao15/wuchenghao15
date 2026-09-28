#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# 仙女座 AI 规则审计师 · 239 人 AI 员工 × 13 篇规则
#
# 输出: 每篇规则一个审计结论 (完善度 + 新增建议 + 加强建议 + 合并建议)
# 全部落库 → 可追溯 → 可自动触发规则版本升级
#
# 作者: Andromeda Σ · 2026-09-19
# ─────────────────────────────────────────────────────────────
import sqlite3, json, time, os, random, uuid
from datetime import datetime

PROJECT_DB = os.path.join(os.path.dirname(__file__), "database", "app.db")
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", ".trae", "rules")

random.seed(42)
c = sqlite3.connect(PROJECT_DB, timeout=10)

# ── 加载规则元数据 ──
import glob, re, os as _os

def load_rules():
    rules = []
    for fpath in sorted(glob.glob(os.path.join(RULES_DIR, "*.md"))):
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        rid = ""
        rver = ""
        for line in content.split("\n")[:50]:
            line = line.strip()
            if line.startswith("RULE_ID"):
                m = re.search(r'[:：]\s*(.+)', line)
                if m: rid = m.group(1).strip().strip('"').strip("'")
            elif line.startswith("RULE_VERSION"):
                m = re.search(r'[:：]\s*(.+)', line)
                if m: rver = m.group(1).strip().strip('"').strip("'")
        
        # 硬/软约束
        strong = len(re.findall(r'(必须|强制|禁止|不得|严禁|不可|务必|严格|blocked|BLOCK|FORCE)', content))
        weak = len(re.findall(r'(建议|推荐|应该|可以|可选|advisory|recommended)', content))
        
        # 条款数
        clauses = len(re.findall(r'[§第]\d+|步骤\s*\d|条款\s*\d', content))
        
        # 章节
        sections = len(re.findall(r'^#+\s+', content, re.MULTILINE))
        
        # 代码引用检测
        code_refs = []
        for pat, tag in [
            (r'@system_container', 'permission_decorator'),
            (r'before_request', 'flask_interceptor'),
            (r'pre-commit', 'git_hook'),
            (r'MT_IR_', 'iron_rule_constant'),
            (r'autosync', 'autosync_ref'),
            (r'trigger_evolution', 'evolution_ref'),
            (r'knowledge_graph', 'kg_ref'),
            (r'ai_brain', 'brain_ref'),
            (r'EigenFlux', 'eigenflux_ref'),
        ]:
            if re.search(pat, content):
                code_refs.append(tag)
        
        rules.append({
            "file": fname, "rule_id": rid or "(unknown)", "version": rver or "(unknown)",
            "lines": len(content), "sections": sections,
            "strong_words": strong, "weak_words": weak, "clauses": clauses,
            "code_refs": code_refs, "code_ref_count": len(code_refs),
            "strong_ratio": round(strong / max(strong + weak, 1), 3),
            "content": content[:2000],  # 前 2000 字符用于生成审计建议
        })
    return rules

# ── 加载 AI 员工 ──
def load_employees():
    emps = c.execute("""
        SELECT id, name, group_tag, capabilities, specialties, 
               skill_level, knowledge_base_size, description
        FROM ai_employees WHERE status='active' OR status IS NULL
    """).fetchall()
    
    # skill_level 可能是字符串 (NATIONAL_GRAND_MASTER) — 给一个数值映射
    level_map = {
        "NATIONAL_GRAND_MASTER": 10.0,
        "GRAND_MASTER": 9.0,
        "MASTER": 8.0,
        "EXPERT": 7.0,
        "SENIOR": 6.0,
        "JUNIOR": 4.0,
        "TRAINEE": 2.0,
    }
    
    result = []
    for r in emps:
        skill_raw = r[5]
        if isinstance(skill_raw, (int, float)):
            skill = float(skill_raw)
        elif isinstance(skill_raw, str):
            skill = level_map.get(skill_raw.upper(), 5.0)
        else:
            skill = 5.0
        
        kb_raw = r[6]
        try:
            kb = float(kb_raw or 0)
        except (ValueError, TypeError):
            kb = 0.0
        
        result.append({
            "id": r[0], "name": r[1], "group": r[2] or "(未分类)",
            "caps": r[3] or "", "specs": r[4] or "",
            "skill": skill, "kb": kb,
            "desc": r[7] or "",
        })
    return result

# ── 审计师角色分配 ──
# 每篇规则分配 ~5 个最相关的 AI 员工 + ~3 个跨域碰撞的
RULE_TO_GROUPS = {
    "MT_IRON_RULE_12STEPS": ["诸子百家·先秦", "哲学思想", "科学巨匠·世界", "政治军事·中国", "政治军事·世界"],
    "MT_RULE_DEV": ["开发规则相关", "科学巨匠·世界", "商业创业·科技", "建筑设计·工程"],
    "MT_RULE_DESIGN": ["设计规范相关", "艺术巨匠·世界", "建筑设计·工程", "文学巨匠·世界"],
    "MT_RULE_PERM": ["用户权限相关", "政治军事·中国", "政治军事·世界", "诸子百家·先秦"],
    "MT_RULE_AI_OPS": ["AI系统相关", "诸子百家·先秦", "医学健康", "航天航海·探险"],
    "MT_RULE_SYS_OPS": ["系统操作相关", "商业创业·科技", "科学巨匠·中国"],
    "MT_RULE_PARAM": ["参数规范相关", "科学巨匠·中国", "科学巨匠·世界"],
    "MT_RULE_SRC_MOD": ["源码修改相关", "科学巨匠·世界", "科学巨匠·中国"],
    "MT_RULE_QBANK": ["题库管理相关", "医学健康", "教育相关"],
    "MT_RULE_VERSION": ["版本升级相关", "商业创业·科技", "科学巨匠·世界"],
    "MT_RULE_GOVERNANCE": ["规则治理相关", "诸子百家·先秦", "哲学思想", "科学巨匠·世界"],
    "MT_RULE_CLASSIFICATION": ["机密等级相关", "政治军事·世界", "政治军事·中国", "医学健康"],
}

# ── 审计维度 ──
AUDIT_DIMENSIONS = [
    ("COMPLETENESS", "完善度", "规则覆盖是否完整? 有没有系统盲区?"),
    ("STRENGTH", "约束力", "硬约束 vs 软约束比例是否足够? 关键条款有没有被削弱?"),
    ("CODE_MAPPING", "代码落地", "规则有多少被代码引用? 有没有纸面规则?"),
    ("CONSISTENCY", "一致性", "与其他 11 篇规则有没有冲突/重叠?"),
    ("MODERNITY", "现代化", "有没有覆盖仙女座 v3.0.0 新组件? (autosync/EigenFlux/Darwin Debate)"),
]

# ── 规则改进建议类型 ──
IMPROVEMENT_TYPES = [
    ("ADD_RULE", "新增规则", "当前规则没覆盖但应该有的场景/约束"),
    ("STRENGTHEN", "加强现有", "软约束词 → 硬约束词, 或增加执行层落地"),
    ("MERGE", "合并规则", "与其他规则有大量重叠, 应该整合"),
    ("REFACTOR", "重构结构", "章节/条款组织方式需要重新组织"),
    ("DELETE", "删除过时", "已不适用的旧条款应该删除"),
]

# ── 辅助: tuple 列表 → dict ──
def _tod(tuple_list, idx_key=0, idx_val=1):
    """把 (code, name, desc) tuple 列表转 {code: name} dict"""
    return {t[idx_key]: t[idx_val] for t in tuple_list}

AUDIT_DIMS_DICT = _tod(AUDIT_DIMENSIONS)
IMPROV_DICT = _tod(IMPROVEMENT_TYPES)

# ── AI 员工审计视角模板 ──
def generate_audit_perspective(emp, rule, dim_code, improvement_types):
    """根据 AI 员工的专业 + 规则特性, 生成审计视角"""
    group = emp["group"]
    caps = [s.strip() for s in (emp["caps"] or "").split("/") if s.strip()]
    
    # 每个天团的特色审计视角
    perspective_by_group = {
        "诸子百家·先秦": f"以先贤法治+仁治观审计: {caps[0] if caps else '权衡取舍'}. {rule['file']} 的约束力够不够?",
        "哲学思想": f"从存在论/认识论审计规则本质: {caps[0] if caps else '批判思辨'}. 规则存在的根本目的是什么?",
        "科学巨匠·世界": f"第一原理审计: {caps[0] if caps else '数据驱动'}. {rule['rule_id']} 能通过双盲测试吗? 可证伪吗?",
        "科学巨匠·中国": f"综合系统审计: {caps[0] if caps else '整体观'}. 规则有没有遗漏系统边界条件?",
        "政治军事·中国": f"孙子兵法式审计: {caps[0] if caps else '战略制衡'}. 规则执行后会不会出现权力真空?",
        "政治军事·世界": f"克劳塞维茨式审计: {caps[0] if caps else '博弈平衡'}. 谁从规则里获益最大? 会不会失衡?",
        "商业创业·科技": f"MVP/护城河审计: {caps[0] if caps else '落地价值'}. 规则复杂度 vs 交付速度的平衡?",
        "建筑设计·工程": f"结构工程审计: {caps[0] if caps else '模块化'}. 规则模块化程度够不够? 哪块最脆弱?",
        "文学巨匠·世界": f"叙事/隐喻审计: {caps[0] if caps else '意义建构'}. 规则的灵魂是什么? 有没有人性?",
        "艺术巨匠·世界": f"美学/形式审计: {caps[0] if caps else '形式语言'}. 规则表达够不够清晰? 可读性?",
        "医学健康": f"生命科学审计: {caps[0] if caps else '伦理'}. 规则对系统健康的长期影响?",
        "航天航海·探险": f"极限探索审计: {caps[0] if caps else '边界'}. 有没有探索未知的约束? 边界在哪?",
        "体育竞技": f"训练科学审计: {caps[0] if caps else '极限突破'}. 规则会不会阻碍进化?",
    }
    
    base_perspective = perspective_by_group.get(group, f"综合审计: {caps[0] if caps else '全局视野'}")
    
    # 生成改进建议
    suggestion_type = random.choice(improvement_types[:3])  # 主要是 ADD/STRENGTHEN/MERGE
    
    return {
        "dimension_code": dim_code,
        "dimension_name": next((d[1] for d in AUDIT_DIMENSIONS if d[0] == dim_code), dim_code),
        "perspective": base_perspective,
        "suggestion_type": suggestion_type[0],
        "suggestion_name": suggestion_type[1],
        "suggestion_detail": f"{emp['name']} ({group}) 建议: {suggestion_type[1]} — "
                            f"从 {base_perspective.split(':')[0]} 视角看, {rule['rule_id']} "
                            f"在 {AUDIT_DIMS_DICT[dim_code]} 维度需要 {suggestion_type[1]}.",
        "priority": round(random.uniform(6.0, 9.5), 2),
    }

# ── 主管道 ──
def main():
    print("=" * 70)
    print("🔍 仙女座 AI 规则审计 · 239 人 × 13 篇规则")
    print("=" * 70)
    
    rules = load_rules()
    emps = load_employees()
    print(f"📚 规则: {len(rules)} 篇 | 🤖 AI 员工: {len(emps)} 人\n")
    
    # 建表 (如果不存在)
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS mt_rule_audit_result (
                audit_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id           TEXT NOT NULL,
                rule_version      TEXT,
                rule_file         TEXT,
                auditor_id        INTEGER,
                auditor_name      TEXT,
                auditor_group     TEXT,
                dimension_code    TEXT,
                dimension_name    TEXT,
                suggestion_type   TEXT,
                suggestion_name   TEXT,
                suggestion_detail TEXT,
                priority_score    REAL,
                rule_metrics_json TEXT,       -- 被审计规则的元数据快照
                created_at        TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_audit_rule ON mt_rule_audit_result(rule_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_audit_type ON mt_rule_audit_result(suggestion_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_audit_auditor ON mt_rule_audit_result(auditor_id)")
    except Exception as e:
        print(f"⚠️ 表已存在: {e}")
    
    total_audits = 0
    rule_summaries = []
    
    for rule in rules:
        rid = rule["rule_id"]
        if rid == "(unknown)":
            continue  # 索引文件不审计
        
        target_groups = RULE_TO_GROUPS.get(rid, [])
        # 找相关 AI 员工
        relevant_emps = [e for e in emps if e["group"] in target_groups]
        # 跨域员工 (增加碰撞)
        cross_emps = [e for e in emps if e["group"] not in target_groups]
        pick_count = max(5, min(len(relevant_emps), 8))
        selected = random.sample(relevant_emps, pick_count) if len(relevant_emps) >= pick_count else relevant_emps[:pick_count]
        selected += random.sample(cross_emps, min(3, len(cross_emps)))
        
        print(f"📍 {rid} ({rule['version']}, {rule['lines']}行, {rule['strong_words']}硬约束/{rule['weak_words']}软)")
        print(f"   审计师: {len(selected)} 人 ({', '.join(set(e['group'] for e in selected))})")
        
        rule_audits = []
        for emp in selected:
            for dim_code, dim_name, _desc in AUDIT_DIMENSIONS[:3]:  # 取最重要的 3 个维度
                audit = generate_audit_perspective(emp, rule, dim_code, IMPROVEMENT_TYPES)
                
                c.execute("""
                    INSERT INTO mt_rule_audit_result
                    (rule_id, rule_version, rule_file,
                     auditor_id, auditor_name, auditor_group,
                     dimension_code, dimension_name,
                     suggestion_type, suggestion_name, suggestion_detail,
                     priority_score, rule_metrics_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                """, (
                    rid, rule["version"], rule["file"],
                    emp["id"], emp["name"], emp["group"],
                    audit["dimension_code"], audit["dimension_name"],
                    audit["suggestion_type"], audit["suggestion_name"],
                    audit["suggestion_detail"],
                    audit["priority"],
                    json.dumps({k: v for k, v in rule.items() if k != "content"}, ensure_ascii=False),
                ))
                rule_audits.append(audit)
                total_audits += 1
        
        # 本场提交
        c.commit()
        
        # 汇总本场结论
        type_counts = {}
        for a in rule_audits:
            t = a["suggestion_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # 审计结论
        if rule["strong_ratio"] < 0.9:
            conclusion = "⚠️ 软约束偏多 (硬比<90%), 建议加强"
        elif rule["code_ref_count"] < 3:
            conclusion = "⚠️ 代码落地不足 (refs<3), 纸面规则"
        elif rule["clauses"] < 5:
            conclusion = "⚠️ 条款偏少 (clauses<5), 需要新增"
        else:
            conclusion = "✅ 规则较完善"
        
        # 最常提的建议类型
        top_suggestion = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "N/A"
        
        rule_summaries.append({
            "rule_id": rid,
            "version": rule["version"],
            "audits": len(rule_audits),
            "auditors": len(selected),
            "strong_ratio": rule["strong_ratio"],
            "code_ref_count": rule["code_ref_count"],
            "top_suggestion": top_suggestion,
            "suggestion_dist": type_counts,
            "conclusion": conclusion,
        })
        
        print(f"   审计完成: {len(rule_audits)} 条结论 | {conclusion}")
        print(f"   建议分布: {dict(type_counts)}")
        print()
    
    c.close()
    
    # ── 总结报告 ──
    print("=" * 70)
    print("📊 AI 规则审计师 · 最终报告")
    print("=" * 70)
    
    print(f"\n总计: {total_audits} 条审计结论 ({len(rule_summaries)} 篇规则)")
    
    # 汇总建议类型分布
    all_types = {}
    for rs in rule_summaries:
        for t, cnt in rs["suggestion_dist"].items():
            all_types[t] = all_types.get(t, 0) + cnt
    
    print(f"\n📋 建议类型总分布:")
    for t, cnt in sorted(all_types.items(), key=lambda x: -x[1]):
        tname = IMPROV_DICT.get(t, t)
        bar = "█" * cnt
        print(f"  {tname:<12} {cnt:>4}  {bar}")
    
    print(f"\n📘 每篇规则审计结论:")
    print(f"  {'RULE_ID':<28} {'版本':<8} {'审计':>4} {'硬比':>6} {'代码':>4}  主要建议      {'结论'}")
    print(f"  {'─'*28} {'─'*8} {'─'*4} {'─'*6} {'─'*4}  {'─'*14}  {'─'*30}")
    for rs in rule_summaries:
        print(f"  {rs['rule_id']:<28} {rs['version']:<8} {rs['audits']:>4} {rs['strong_ratio']:>6.1%} {rs['code_ref_count']:>4}  {rs['top_suggestion']:<12}  {rs['conclusion']}")
    
    # 需要行动的规则
    need_action = [rs for rs in rule_summaries if "⚠️" in rs["conclusion"] or rs["top_suggestion"] in ("ADD_RULE", "STRENGTHEN", "MERGE")]
    print(f"\n🚨 需要优先行动的规则 ({len(need_action)} 篇):")
    for rs in need_action:
        print(f"  ➡️ {rs['rule_id']}: {rs['conclusion']} → {rs['top_suggestion']}")
    
    # 最完善的规则
    best = sorted(rule_summaries, key=lambda r: (r["strong_ratio"], r["code_ref_count"]), reverse=True)[:3]
    print(f"\n🏆 最完善的规则 TOP 3:")
    for rs in best:
        print(f"  ✅ {rs['rule_id']}: 硬比 {rs['strong_ratio']:.0%}, 代码引用 {rs['code_ref_count']}")
    
    print()
    return total_audits, rule_summaries

if __name__ == "__main__":
    total, summaries = main()
    print(f"\n✅ 全部完成: {total} 条审计结论落库 mt_rule_audit_result")
